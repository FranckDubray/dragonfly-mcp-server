"""Core logic for office_to_pdf operations."""

from typing import Dict, Any
from .validators import validate_convert_params, validate_get_info_params
from .utils import get_unique_output_path, get_file_info
from .services.office_converter import convert_to_pdf


def handle_convert(**params) -> Dict[str, Any]:
    """Handle convert operation.
    
    Args:
        **params: Convert parameters
            - input_path (str): Path to input Office file (required)
            - output_path (str): Path to output PDF file (optional)
            - overwrite (bool): Overwrite existing file (default: False)
    
    Returns:
        Conversion results
    """
    try:
        # Validate parameters
        validated = validate_convert_params(params)
        
        # Get unique output path (add suffix if file exists and not overwrite)
        output_path = get_unique_output_path(
            validated["output_path"],
            validated["overwrite"]
        )
        
        # Convert using native Office apps
        result = convert_to_pdf(validated["input_path"], output_path)
        
        return result
        
    except ValueError as e:
        return {"error": f"Validation error: {str(e)}"}
    except Exception as e:
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
        
        return {
            "success": True,
            **info
        }
        
    except ValueError as e:
        return {"error": f"Validation error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}
