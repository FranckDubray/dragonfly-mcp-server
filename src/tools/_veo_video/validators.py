from typing import Dict, Any

ALLOWED_MODELS = {"veo-3.1-generate-preview", "veo-3.1-fast-generate-preview"}
ALLOWED_ASPECT = {"16:9", "9:16"}
ALLOWED_RES = {"720p", "1080p"}
ALLOWED_SECONDS = {4, 6, 8}
ALLOWED_PERSON_GEN = {"allow_all", "allow_adult", "dont_allow"}

class ValidationError(ValueError):
    pass

def ensure(cond: bool, msg: str):
    if not cond:
        raise ValidationError(msg)


def validate_params(params: Dict[str, Any]) -> None:
    op = params.get("operation")
    ensure(op in {"create", "get_status", "download", "extend", "auto_start"}, "operation invalide")

    model = params.get("model", "veo-3.1-generate-preview")
    ensure(model in ALLOWED_MODELS, "model invalide")

    # Shared option checks
    if "aspect_ratio" in params:
        ensure(params["aspect_ratio"] in ALLOWED_ASPECT, "aspect_ratio invalide")
    if "resolution" in params:
        ensure(params["resolution"] in ALLOWED_RES, "resolution invalide")
    if "seconds" in params:
        ensure(params["seconds"] in ALLOWED_SECONDS, "seconds invalide (4,6,8)")
    if "person_generation" in params and params["person_generation"] is not None:
        ensure(params["person_generation"] in ALLOWED_PERSON_GEN, "person_generation invalide")

    if op == "create":
        prompt = params.get("prompt")
        ensure(isinstance(prompt, str) and prompt.strip(), "prompt requis pour create")
        image_path = params.get("image_path")
        last_frame_path = params.get("last_frame_path")
        ref_paths = params.get("reference_image_paths")
        seconds = params.get("seconds", 8)
        aspect = params.get("aspect_ratio", "16:9")
        res = params.get("resolution", "720p")

        # 1080p requires 8s
        if res == "1080p":
            ensure(seconds == 8, "1080p exige seconds=8")
        # reference_images constraints
        if ref_paths:
            ensure(1 <= len(ref_paths) <= 3, "reference_image_paths: 1 à 3 images")
            ensure(seconds == 8, "reference_image_paths exige seconds=8")
            ensure(aspect == "16:9", "reference_image_paths exige aspect_ratio=16:9")
        # interpolation constraints
        if last_frame_path:
            ensure(image_path is not None, "last_frame_path exige aussi image_path (première image)")
            ensure(seconds == 8, "Interpolation exige seconds=8")

    elif op == "extend":
        video_path = params.get("video_path")
        ensure(isinstance(video_path, str) and video_path.strip(), "video_path requis pour extend")
        # Extension resolution is 720p only per docs
        res = params.get("resolution", "720p")
        ensure(res == "720p", "extend: resolution doit être 720p")

    elif op == "get_status":
        ensure(isinstance(params.get("operation_name"), str) and params["operation_name"].strip(), "operation_name requis pour get_status")

    elif op == "download":
        ensure(isinstance(params.get("operation_name"), str) and params["operation_name"].strip(), "operation_name requis pour download")

    elif op == "auto_start":
        ensure(isinstance(params.get("path"), str) and params["path"].strip(), "path requis pour auto_start")
