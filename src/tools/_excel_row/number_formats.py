from __future__ import annotations

# Map presets to Excel number format codes. Some presets accept params.

def currency_format(symbol: str = "€", locale: str | None = None, decimals: int | None = 2) -> str:
    d = 2 if decimals is None else max(0, min(6, int(decimals)))
    decs = "" if d == 0 else "." + ("0" * d)
    loc = f"-{locale}" if locale else ""
    # Example: #,##0.00 [$€-fr-FR]
    return f"#,##0{decs} [$${symbol}{loc}]".replace("$$", "")


def accounting_eur_fr(decimals: int | None = 2) -> str:
    d = 2 if decimals is None else max(0, min(6, int(decimals)))
    decs = "" if d == 0 else "." + ("0" * d)
    # Classic accounting pattern with € and fr-FR
    return (
        f"_-* [$€-fr-FR] #,##0{decs}_-;"
        f"[Red]-* [$€-fr-FR] #,##0{decs}_-;"
        f"_-* [$€-fr-FR] \"-\"??_-;_-@_-"
    )


PRESETS: dict[str, str | callable] = {
    "general": "General",
    "text": "@",
    "integer": "0",
    "decimal_2": "0.00",
    "decimal_3": "0.000",
    "percent_0": "0%",
    "percent_2": "0.00%",
    "date_iso": "yyyy-mm-dd",
    "date_short_fr": "dd/mm/yyyy",
    "currency_eur_fr": lambda params: currency_format("€", "fr-FR", params.get("decimals")),
    "currency_usd_en": lambda params: currency_format("$", "en-US", params.get("decimals")),
    "accounting_eur_fr": lambda params: accounting_eur_fr(params.get("decimals")),
}


def resolve_number_format(preset: str | None, custom: str | None, params: dict | None) -> str | None:
    if custom:
        return custom
    if not preset:
        return None
    fmt = PRESETS.get(preset)
    if fmt is None:
        return None
    if callable(fmt):
        return fmt(params or {})
    return fmt
