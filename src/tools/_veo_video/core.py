from typing import Any, Dict
from .services import GoogleGenAIClient
from .utils import safe_join


def start_create(params: Dict[str, Any]) -> Dict[str, Any]:
    client = GoogleGenAIClient()
    image_path = params.get("image_path")
    last_frame_path = params.get("last_frame_path")
    ref_paths = params.get("reference_image_paths") or []

    res = client.start_generate(
        model=params.get("model", "veo-3.1-generate-preview"),
        prompt=params["prompt"],
        negative_prompt=params.get("negative_prompt"),
        image_path=(safe_join(image_path) if image_path else None),
        last_frame_path=(safe_join(last_frame_path) if last_frame_path else None),
        reference_image_paths=[safe_join(p) for p in ref_paths] if ref_paths else None,
        aspect_ratio=params.get("aspect_ratio"),
        resolution=params.get("resolution"),
        duration_seconds=params.get("seconds"),
        person_generation=params.get("person_generation"),
        seed=params.get("seed"),
        number_of_videos=1,
    )
    return {"operation_name": res.get("operation_name", ""), "model": params.get("model", "veo-3.1-generate-preview")}


def extend_video(params: Dict[str, Any]) -> Dict[str, Any]:
    client = GoogleGenAIClient()
    video_abs = safe_join(params["video_path"]) if params.get("video_path") else None
    res = client.extend_video(
        model=params.get("model", "veo-3.1-generate-preview"),
        video_path=video_abs,  # type: ignore[arg-type]
        prompt=params.get("prompt"),
        resolution=params.get("resolution", "720p"),
    )
    return {"operation_name": res.get("operation_name", ""), "model": params.get("model", "veo-3.1-generate-preview")}


def get_status(params: Dict[str, Any]) -> Dict[str, Any]:
    client = GoogleGenAIClient()
    op = client.get_operation(params["operation_name"])
    done = bool(getattr(op, 'done', False))
    out: Dict[str, Any] = {"done": done}
    if done:
        out["ready"] = True
    state = getattr(op, 'metadata', None)
    if state is not None:
        hint = getattr(state, 'state', None) or getattr(state, 'progress', None)
        if hint:
            out["progress_hint"] = str(hint)
    return out


def wait_for_completion(params: Dict[str, Any]) -> Dict[str, Any]:
    import time
    client = GoogleGenAIClient()
    timeout = params.get("timeout_seconds", 600)
    max_attempts = max(1, int(params.get("max_attempts", 60)))
    poll_every = max(1.0, min(60.0, float(timeout) / float(max_attempts)))

    start = time.time()
    while True:
        op = client.get_operation(params["operation_name"])
        if getattr(op, 'done', False):
            break
        if time.time() - start > timeout:
            return {"done": False, "timeout": True}
        time.sleep(poll_every)
    return {"done": True}


def download(params: Dict[str, Any]) -> Dict[str, Any]:
    client = GoogleGenAIClient()
    filename = params.get("filename") or "veo_video.mp4"
    rel = f"docs/video/{filename if filename.lower().endswith('.mp4') else filename + '.mp4'}"
    out = client.download_operation_result(params["operation_name"], dest_path=rel, overwrite=bool(params.get("overwrite", False)))
    return out
