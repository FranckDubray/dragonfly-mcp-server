import os
from typing import Any, Dict
from .validators import validate_params, ValidationError
from .core import start_create, extend_video, get_status, wait_for_completion, download
from .utils import auto_start_video


def run(**params) -> Dict[str, Any]:
    try:
        validate_params(params)
        op = params["operation"]
        if op == "create":
            result = start_create(params)
            if params.get("wait"):
                # Poll until completion or timeout
                wait_res = wait_for_completion({
                    "operation_name": result["operation_name"],
                    "timeout_seconds": params.get("timeout_seconds", 600),
                    "max_attempts": params.get("max_attempts", 60)
                })
                result.update({"wait_result": wait_res})
                if wait_res.get("done") and params.get("auto_download"):
                    dl = download({
                        "operation_name": result["operation_name"],
                        "filename": params.get("filename"),
                        "overwrite": params.get("overwrite", False)
                    })
                    result.update({"auto_download": dl})
            return result
        elif op == "extend":
            return extend_video(params)
        elif op == "get_status":
            return get_status(params)
        elif op == "download":
            return download(params)
        elif op == "auto_start":
            return auto_start_video(params["path"])
        else:
            return {"error": "operation non supportée"}
    except ValidationError as e:
        return {"error": str(e)}
    except Exception as e:
        # Avoid leaking secrets
        msg = str(e)
        key = os.getenv('GOOGLE_API_KEY')
        if key and key in msg:
            msg = msg.replace(key, '***')
        return {"error": f"veo_video failure: {type(e).__name__}: {msg[:200]}"}
