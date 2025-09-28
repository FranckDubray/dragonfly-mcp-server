"""Statistics extensions: regression, correlation, covariance, zscore, moving average"""
from __future__ import annotations
from typing import Dict, Any, List, Tuple
import math


def linear_regression(x: List[float], y: List[float]) -> Dict[str, Any]:
    if not x or not y or len(x) != len(y):
        return {"error": "x and y must be same-length non-empty lists"}
    n = len(x)
    sx = sum(x)
    sy = sum(y)
    sxx = sum(xi*xi for xi in x)
    sxy = sum(xi*yi for xi, yi in zip(x, y))
    denom = n * sxx - sx * sx
    if denom == 0:
        return {"error": "Cannot compute regression (singular)"}
    slope = (n * sxy - sx * sy) / denom
    intercept = (sy - slope * sx) / n
    # R^2
    y_mean = sy / n
    ss_tot = sum((yi - y_mean)**2 for yi in y)
    ss_res = sum((yi - (slope*xi + intercept))**2 for xi, yi in zip(x, y))
    r2 = 1 - ss_res / ss_tot if ss_tot != 0 else 1.0
    return {"result": {"slope": slope, "intercept": intercept, "r2": r2}}


def correlation(x: List[float], y: List[float]) -> Dict[str, Any]:
    if not x or not y or len(x) != len(y):
        return {"error": "x and y must be same-length non-empty lists"}
    n = len(x)
    mx = sum(x) / n
    my = sum(y) / n
    num = sum((xi - mx)*(yi - my) for xi, yi in zip(x, y))
    dx = math.sqrt(sum((xi - mx)**2 for xi in x))
    dy = math.sqrt(sum((yi - my)**2 for yi in y))
    if dx == 0 or dy == 0:
        return {"error": "Zero variance in x or y"}
    return {"result": num / (dx * dy)}


def covariance(x: List[float], y: List[float], sample: bool = True) -> Dict[str, Any]:
    if not x or not y or len(x) != len(y):
        return {"error": "x and y must be same-length non-empty lists"}
    n = len(x)
    if n < 2:
        return {"error": "At least two points required"}
    mx = sum(x) / n
    my = sum(y) / n
    cov = sum((xi - mx)*(yi - my) for xi, yi in zip(x, y)) / (n - 1 if sample else n)
    return {"result": cov}


def zscore(data: List[float]) -> Dict[str, Any]:
    if not data or len(data) < 2:
        return {"error": "At least two data points required"}
    n = len(data)
    m = sum(data) / n
    s = math.sqrt(sum((xi - m)**2 for xi in data) / (n - 1))
    if s == 0:
        return {"error": "Zero standard deviation"}
    return {"result": [(xi - m)/s for xi in data]}


def moving_average(data: List[float], window: int) -> Dict[str, Any]:
    if not data or window <= 0 or window > len(data):
        return {"error": "Invalid window or empty data"}
    out = []
    s = sum(data[:window])
    out.append(s / window)
    for i in range(window, len(data)):
        s += data[i] - data[i - 1 - (window - 1)]
        out.append(s / window)
    return {"result": out}