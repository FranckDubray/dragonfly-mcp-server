"""
Date tool: common date/time operations (weekday, differences, now/today, add, format, parse, week number)
"""
from __future__ import annotations
from typing import Any, Dict, Optional
import datetime as dt
import re
import json
import os
import logging

logger = logging.getLogger(__name__)

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore

WEEKDAY_NAMES_EN = [
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
]
WEEKDAY_NAMES_FR = [
    "lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"
]


def _get_tz(tz: Optional[str]) -> Optional[Any]:
    if not tz:
        return None
    if ZoneInfo is None:
        logger.warning("ZoneInfo not available (Python <3.11), timezone ignored")
        return None
    try:
        return ZoneInfo(tz)
    except Exception as e:
        logger.warning(f"Invalid timezone '{tz}': {e}, using UTC")
        return dt.timezone.utc


def _now(tz: Optional[str]) -> dt.datetime:
    tzinfo = _get_tz(tz)
    if tzinfo is None:
        return dt.datetime.now(dt.timezone.utc).astimezone()
    return dt.datetime.now(tzinfo)


_COMMON_FORMATS = [
    "%Y-%m-%d",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d %H:%M:%S",
    "%Y/%m/%d",
    "%d/%m/%Y",
    "%d/%m/%Y %H:%M",
    "%d/%m/%Y %H:%M:%S",
    "%m/%d/%Y",
    "%m/%d/%Y %H:%M",
    "%m/%d/%Y %H:%M:%S",
]


def _parse_datetime(s: str, input_format: Optional[str] = None, tz: Optional[str] = None) -> dt.datetime:
    s = (s or "").strip()
    if not s:
        raise ValueError("Empty date string")

    # Try Python 3.11+ fromisoformat for full datetime
    try:
        dtv = dt.datetime.fromisoformat(s)
        if dtv.tzinfo is None and tz:
            dtv = dtv.replace(tzinfo=_get_tz(tz) or dt.timezone.utc)
        return dtv
    except Exception:
        pass

    # If only date part
    try:
        dv = dt.date.fromisoformat(s)
        return dt.datetime.combine(dv, dt.time(0, 0, 0), _get_tz(tz) or dt.timezone.utc)
    except Exception:
        pass

    # Use provided format
    if input_format:
        try:
            dtv = dt.datetime.strptime(s, input_format)
            if tz:
                dtv = dtv.replace(tzinfo=_get_tz(tz) or dt.timezone.utc)
            return dtv
        except Exception as e:
            raise ValueError(f"Failed to parse with input_format: {e}")

    # Try common formats
    for fmt in _COMMON_FORMATS:
        try:
            dtv = dt.datetime.strptime(s, fmt)
            if tz:
                dtv = dtv.replace(tzinfo=_get_tz(tz) or dt.timezone.utc)
            return dtv
        except Exception:
            continue

    raise ValueError("Unrecognized date/time format. Provide input_format or use ISO like 'YYYY-MM-DD' or 'YYYY-MM-DDTHH:MM:SS'.")


def _parse_dateonly(s: str, input_format: Optional[str] = None) -> dt.date:
    s = (s or "").strip()
    if not s:
        raise ValueError("Empty date string")
    try:
        return dt.date.fromisoformat(s)
    except Exception:
        pass
    if input_format:
        try:
            return dt.datetime.strptime(s, input_format).date()
        except Exception as e:
            raise ValueError(f"Failed to parse with input_format: {e}")
    for fmt in ("%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return dt.datetime.strptime(s, fmt).date()
        except Exception:
            continue
    raise ValueError("Unrecognized date format. Provide input_format or use 'YYYY-MM-DD'.")


def run(operation: str, **params) -> Dict[str, Any]:
    try:
        if not operation:
            return {"error": "Missing required parameter 'operation'"}
        op = operation.strip()

        if op == "now":
            tz = params.get("tz")
            now = _now(tz)
            return {"result": now.isoformat()}

        if op == "today":
            tz = params.get("tz")
            today = _now(tz).date()
            return {"result": today.isoformat()}

        if op == "day_of_week":
            # Accept 'date' or 'datetime'
            s = params.get("date") or params.get("datetime")
            if not s:
                return {"error": "Parameter 'date' (or 'datetime') required"}
            input_format = params.get("input_format")
            # Use date-only parsing for accuracy
            d = _parse_dateonly(s, input_format)
            # weekday(): Monday=0..Sunday=6, ISO weekday 1..7
            w = d.weekday()
            iso = d.isoweekday()
            locale = (params.get("locale") or "en").lower()
            name = WEEKDAY_NAMES_FR[w] if locale.startswith("fr") else WEEKDAY_NAMES_EN[w]
            return {"result": {"weekday": w, "weekday_iso": iso, "weekday_name": name}}

        if op in ("diff", "diff_days"):
            # Compute difference between two dates/datetimes
            s1 = params.get("start") or params.get("date1") or params.get("from")
            s2 = params.get("end") or params.get("date2") or params.get("to")
            if not s1 or not s2:
                return {"error": "Parameters 'start' (or 'date1') and 'end' (or 'date2') are required"}
            unit = (params.get("unit") or ("days" if op == "diff_days" else "days")).lower()
            input_format = params.get("input_format")
            tz = params.get("tz")
            # Parse as datetime to include time if present
            dt1 = _parse_datetime(s1, input_format, tz)
            dt2 = _parse_datetime(s2, input_format, tz)
            delta = dt2 - dt1
            if unit == "days":
                value = delta.total_seconds() / 86400.0
            elif unit == "hours":
                value = delta.total_seconds() / 3600.0
            elif unit == "minutes":
                value = delta.total_seconds() / 60.0
            elif unit == "seconds":
                value = delta.total_seconds()
            else:
                return {"error": "Invalid unit. Use one of: days, hours, minutes, seconds"}
            return {"result": value}

        if op == "add":
            s = params.get("date") or params.get("datetime")
            if not s:
                return {"error": "Parameter 'date' (or 'datetime') required"}
            input_format = params.get("input_format")
            tz = params.get("tz")
            dtv = _parse_datetime(s, input_format, tz)
            # Build timedelta with validation
            weeks = int(params.get("weeks") or 0)
            days = int(params.get("days") or 0)
            hours = int(params.get("hours") or 0)
            minutes = int(params.get("minutes") or 0)
            seconds = int(params.get("seconds") or 0)
            
            # Validation: prevent absurd values
            if abs(weeks) > 520 or abs(days) > 3650 or abs(hours) > 87600 or abs(minutes) > 525600 or abs(seconds) > 31536000:
                logger.warning(f"add: large delta values detected (weeks={weeks}, days={days}, hours={hours}, minutes={minutes}, seconds={seconds})")
            
            delta = dt.timedelta(weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds)
            out = dtv + delta
            return {"result": out.isoformat()}

        if op == "format":
            s = params.get("date") or params.get("datetime")
            if not s:
                return {"error": "Parameter 'date' (or 'datetime') required"}
            input_format = params.get("input_format")
            tz = params.get("tz")
            fmt = params.get("format") or "%Y-%m-%d %H:%M:%S%z"
            
            # Validation: prevent complex format strings
            if len(fmt) > 100:
                return {"error": "Format string too long (max 100 chars)"}
            
            dtv = _parse_datetime(s, input_format, tz)
            return {"result": dtv.strftime(fmt)}

        if op == "parse":
            s = params.get("date") or params.get("datetime")
            if not s:
                return {"error": "Parameter 'date' (or 'datetime') required"}
            input_format = params.get("input_format")
            tz = params.get("tz")
            dtv = _parse_datetime(s, input_format, tz)
            return {"result": {"iso": dtv.isoformat(), "timestamp": int(dtv.timestamp())}}

        if op == "week_number":
            s = params.get("date") or params.get("datetime")
            if not s:
                return {"error": "Parameter 'date' (or 'datetime') required"}
            input_format = params.get("input_format")
            tz = params.get("tz")
            dtv = _parse_datetime(s, input_format, tz)
            iso_year, iso_week, iso_weekday = dtv.isocalendar()
            return {"result": {"iso_year": iso_year, "iso_week": iso_week, "iso_weekday": iso_weekday}}

        return {"error": f"Unknown operation: '{operation}'. Available: now, today, day_of_week, diff, diff_days, add, format, parse, week_number"}

    except Exception as e:
        logger.error(f"date tool error (operation={operation}): {e}")
        return {"error": str(e)}


def spec() -> Dict[str, Any]:
    """Load canonical JSON spec"""
    here = os.path.dirname(__file__)
    spec_path = os.path.abspath(os.path.join(here, '..', 'tool_specs', 'date.json'))
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)
