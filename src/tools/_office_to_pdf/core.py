
"""
Core logic for office_to_pdf operations.
"""
from typing import Dict, Any
from .validators import validate_convert_params, validate_get_info_params
from .utils import get_unique_output_path, get_file_info
from .analyzers import analyze_office_file


def handle_convert(**params) -> Dict[str, Any]:
    """Handle convert operation.
    
    Args:
        **params: Convert parameters
            - input_path (str): Path to input Office file (required)
            - output_path (str): Path to output PDF file (optional)
            - overwrite (bool): Overwrite existing file (default: False)
            - engine (str): 'auto' | 'docx2pdf' | 'libreoffice' (optional)
    
    Returns:
        Conversion results
    """
    try:
        # Validate parameters
        validated = validate_convert_params(params)

        # Import service lazily to avoid import-time failure when docx2pdf/Office not installed
        from .services.office_converter import convert_to_pdf  # noqa: WPS433 (local import by design)
        
        # Get unique output path (add suffix if file exists and not overwrite)
        output_path = get_unique_output_path(
            validated["output_path"],
            validated["overwrite"]
        )
        
        # Convert using native Office apps or headless fallback, depending on engine
        result = convert_to_pdf(
            validated["input_path"],
            output_path,
            engine=validated.get("engine", "auto"),
        )
        
        # Harmonize response shape with README
        return {
            "success": True,
            **result,
            "message": result.get("message", "Conversion successful"),
        }
        
    except ValueError as e:
        return {"error": f"Validation error: {str(e)}"}
    except RuntimeError as e:
        # Propagate clear engine/service errors as-is
        return {"error": str(e)}
    except Exception as e:
        # Minimal error, no verbose metadata
        return {"error": f"Unexpected error: {str(e)}"}


def handle_get_info(**params) -> Dict[str, Any]:
    """Handle get_info operation.
    
    Args:
        **params: Get info parameters
            - input_path (str): Path to input Office file (required)
    
    Returns:
        File metadata
    """
    try:
        # Validate parameters
        validated = validate_get_info_params(params)
        
        # Get file info
        info = get_file_info(validated["input_path"])
        # Optional richer analysis: pages and large images
        extra = analyze_office_file(validated["input_path"])
        
        return {
            "success": True,
            **info,
            **extra,
        }
        
    except ValueError as e:
        return {"error": f"Validation error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

 