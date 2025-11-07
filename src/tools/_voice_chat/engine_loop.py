

from __future__ import annotations
from typing import Dict, Any, List, Optional
import time, queue
import numpy as np

from .vad_tts import pre_emphasis, rms, TTSManager
from .engine_utils import compute_snr_db, voiced_flag, strong_peak, handle_end_of_utterance
from .logs import dbg
from .engine_config import get_barge_config, get_tts_max_chars, get_snr_min_db, get_relief_config, get_min_abs_mult
from .vad_webrtc import get_webrtc_vad
from .engine_transient import Debouncer


def run_loop(
    *,
    q: "queue.Queue[np.ndarray]",
    messages: List[Dict[str, str]],
    tts: TTSManager,
    sample_rate: int,
    min_seconds: float,
    vad_threshold: float,
    vad_silence_ms: int,
    model: Optional[str],
    temperature: float,
    max_tokens: int,
    whisper_model: Optional[str],
    idle_timeout_s: int,
    tool_names: Optional[List[str]] = None,
    system_prompt: Optional[str] = None,
) -> Dict[str, Any]:
    barge_grace_ms, barge_arm_blocks, barge_snr_extra, barge_min_abs_mult = get_barge_config()
    tts_max_chars = get_tts_max_chars()
    SNR_MIN_DB = get_snr_min_db()

    relief_interval_s, relief_factor, relief_to_base = get_relief_config()
    min_abs_mult = get_min_abs_mult()

    webrtc = get_webrtc_vad(aggressiveness=2)
    if webrtc:
        dbg("voice_chat_vad_backend", name="webrtcvad", aggressiveness=2)
    else:
        dbg("voice_chat_vad_backend", name="rms_snr")

    # VAD calibration
    noise_rms = 0.0
    noise_frames = 0
    start_threshold = float(vad_threshold)
    stop_threshold = start_threshold * 0.8

    needed = 14
    safety_deadline = time.time() + 6.0
    while noise_frames < needed:
        try:
            blk = q.get(timeout=1.0)
        except queue.Empty:
            if time.time() > safety_deadline:
                break
            continue
        if tts.speaking_elapsed_ms() > 0:
            # Skip calibration samples while TTS is speaking to avoid polluting noise baseline
            if time.time() > safety_deadline:
                continue
            else:
                continue
        blk_pe = pre_emphasis(blk)
        noise_rms += rms(blk_pe)
        noise_frames += 1
    if noise_frames > 0:
        noise_rms /= noise_frames
        base = noise_rms * 3.0
        start_threshold = max(start_threshold, base)
        stop_threshold = start_threshold * 0.8
    dbg("voice_chat_vad_calibrated", noise_rms=round(noise_rms, 6), start_threshold=round(start_threshold, 6), stop_threshold=round(stop_threshold, 6))

    # Loop state
    recording = False
    utter_frames: List[np.ndarray] = []
    started_at: Optional[float] = None
    silence_ms = 0.0
    last_voiced_block_idx = -1

    # Accumulate the voice-mode dialog (list of {user, assistant})
    vocal_dialog: List[Dict[str, str]] = []

    deb = Debouncer(window_blocks=5, min_onset_blocks=3)
    barge_deb = Debouncer(window_blocks=max(7, barge_arm_blocks), min_onset_blocks=max(7, barge_arm_blocks))

    last_relief_ts = time.time()
    calibration_base = max(start_threshold, noise_rms * 3.0)

    # Idle timer counts activity; must not trigger while TTS is speaking
    last_activity_ts = time.time()
    speaking_prev = False

    def ping_activity(phase: str) -> None:
        nonlocal last_activity_ts
        last_activity_ts = time.time()
        dbg("voice_chat_activity", phase=phase)

    while True:
        # Track TTS state and update last activity continuously during speech
        speaking_ms_now = tts.speaking_elapsed_ms()
        speaking_now = speaking_ms_now > 0
        if speaking_now and not speaking_prev:
            last_activity_ts = time.time()  # TTS started
        elif (not speaking_now) and speaking_prev:
            last_activity_ts = time.time()  # TTS ended
        if speaking_now:
            # Consider ongoing TTS as activity to prevent idle timeout mid-speech
            last_activity_ts = time.time()
        speaking_prev = speaking_now

        # Idle timeout (never fire while speaking)
        if (not speaking_now) and (time.time() - last_activity_ts) >= float(idle_timeout_s):
            dbg("voice_chat_idle_timeout", seconds=idle_timeout_s)
            return {
                "success": True,
                "ended": True,
                "reason": "idle_timeout",
                "message": f"Fin du mode vocal (inactivité {idle_timeout_s}s). Reprenez en conversation texte.",
                "idle_timeout": idle_timeout_s,
                "turns": len(vocal_dialog),
                "returned_turns": len(vocal_dialog),
                "vocal_dialog": vocal_dialog,
                "llm_note": "Mode vocal terminé. Reprends en conversation texte.",
            }

        try:
            block = q.get(timeout=1.0)
        except queue.Empty:
            now = time.time()
            if not recording and (now - last_relief_ts) >= float(relief_interval_s):
                target = float(vad_threshold)
                if relief_to_base:
                    target = min(target, calibration_base)
                new_thr = max(target, start_threshold * float(relief_factor))
                if new_thr < start_threshold:
                    start_threshold = new_thr
                    stop_threshold = start_threshold * 0.8
                    dbg("voice_chat_vad_relief", start_threshold=round(start_threshold, 6), stop_threshold=round(stop_threshold, 6))
                last_relief_ts = now
            continue

        blk_pe = pre_emphasis(block)
        level = rms(blk_pe)
        snr_db = compute_snr_db(level, noise_rms)
        thr = start_threshold if not recording else stop_threshold
        min_abs = noise_rms * float(min_abs_mult)
        min_abs_barge = noise_rms * barge_min_abs_mult

        # While TTS is speaking
        if speaking_now:
            within_grace = speaking_ms_now < float(barge_grace_ms)
            if within_grace:
                deb.reset(); barge_deb.reset()
                continue
            # After grace: allow barge-in only on sustained speech, with WebRTC VAD positive if available
            if webrtc is not None:
                vad_speech = webrtc.is_speech(blk, sample_rate)
                barge_raw = vad_speech and voiced_flag(level, snr_db, thr, SNR_MIN_DB, min_abs_barge)
            else:
                barge_raw = voiced_flag(level, snr_db, thr, SNR_MIN_DB, min_abs_barge)
            barge_sustained = barge_deb.update(barge_raw)
            if barge_sustained:
                try:
                    tts.interrupt()
                    dbg("voice_chat_tts_barge_in", elapsed_ms=round(speaking_ms_now, 1), grace_ms=barge_grace_ms,
                        sustained=True, snr_db=round(snr_db,2), level=round(level,6))
                except Exception:
                    try:
                        tts.stop()
                    except Exception:
                        pass
                recording = True
                utter_frames = [block]
                started_at = time.time()
                silence_ms = 0.0
                last_voiced_block_idx = 0
                last_activity_ts = time.time()  # user activity (barge)
                deb.reset(); barge_deb.reset()
                dbg("voice_chat_recording_start", level=round(level, 6), snr_db=round(snr_db, 2),
                    start_threshold=round(start_threshold, 6), stop_threshold=round(stop_threshold, 6))
                continue
            else:
                continue

        # Not speaking: speech decision (hybrid): WebRTC VAD (if present) + RMS/SNR, then debounce
        if webrtc is not None:
            vad_speech = webrtc.is_speech(blk, sample_rate)
            raw_voiced = vad_speech or voiced_flag(level, snr_db, thr, SNR_MIN_DB, min_abs)
        else:
            raw_voiced = voiced_flag(level, snr_db, thr, SNR_MIN_DB, min_abs)

        voiced_now = deb.update(raw_voiced)
        block_ms = (len(block) / float(sample_rate)) * 1000.0

        if not recording:
            if voiced_now:
                recording = True
                utter_frames = [block]
                started_at = time.time()
                silence_ms = 0.0
                last_voiced_block_idx = 0
                last_activity_ts = time.time()  # user voice activity
                dbg("voice_chat_recording_start", level=round(level, 6), snr_db=round(snr_db, 2), start_threshold=round(start_threshold, 6), stop_threshold=round(stop_threshold, 6))
        else:
            utter_frames.append(block)
            if voiced_now:
                silence_ms = 0.0
                last_voiced_block_idx = len(utter_frames) - 1
                last_activity_ts = time.time()  # ongoing user voice
            else:
                silence_ms += block_ms

            dur = (time.time() - (started_at or time.time())) if started_at else 0.0
            MIN_VOICED_MS = 300.0
            if silence_ms >= float(vad_silence_ms) and dur >= float(min_seconds or 0.5) and (last_voiced_block_idx >= 0):
                last_activity_ts = time.time()
                result = handle_end_of_utterance(
                    utter_frames,
                    last_voiced_block_idx,
                    sample_rate=sample_rate,
                    min_seconds=min_seconds,
                    whisper_model=whisper_model,
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    tts=tts,
                    tts_max_chars=tts_max_chars,
                    ping_activity=ping_activity,
                    tool_names=tool_names,
                    system_prompt=system_prompt,
                )

                recording = False
                utter_frames = []
                started_at = None
                silence_ms = 0.0
                deb.reset(); barge_deb.reset()

                # Immediate end if stop_tag or any ended flag
                if result.get("ended"):
                    return {
                        "success": True,
                        "ended": True,
                        "reason": result.get("reason", "stop_tag"),
                        "turns": len(vocal_dialog),
                        "returned_turns": len(vocal_dialog),
                        "vocal_dialog": vocal_dialog,
                        "llm_note": "Mode vocal terminé. Reprends en conversation texte.",
                    }

                if result.get("success"):
                    # Append this vocal turn (user + assistant)
                    u = (result.get("transcript") or "").strip()
                    a = (result.get("assistant_text") or "").strip()
                    if u or a:
                        vocal_dialog.append({"user": u, "assistant": a})
                else:
                    continue

    # unreachable
