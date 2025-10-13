"""
Validators for device_location tool parameters.
"""
from typing import Literal

ALLOWED_OPERATIONS = {"get_location"}
ALLOWED_PROVIDERS = {"ipapi", "ip-api"}


def validate_operation(operation: str) -> str:
    if operation not in ALLOWED_OPERATIONS:
        raise ValueError(f"Invalid operation: {operation}. Allowed: {sorted(ALLOWED_OPERATIONS)}")
    return operation


def validate_provider(provider: str | None) -> Literal["ipapi", "ip-api"]:
    if provider is None:
        return "ipapi"
    if provider not in ALLOWED_PROVIDERS:
        raise ValueError(f"Invalid provider: {provider}. Allowed: {sorted(ALLOWED_PROVIDERS)}")
    return provider  # type: ignore[return-value]
