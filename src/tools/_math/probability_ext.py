"""Extra probability distributions without SciPy"""
from __future__ import annotations
import math
from statistics import NormalDist
from typing import Dict, Any


def normal_cdf(x: float, mu: float = 0.0, sigma: float = 1.0) -> Dict[str, Any]:
    if sigma <= 0:
        return {"error": "sigma must be positive"}
    dist = NormalDist(mu, sigma)
    return {"result": dist.cdf(x)}


def normal_ppf(p: float, mu: float = 0.0, sigma: float = 1.0) -> Dict[str, Any]:
    if sigma <= 0:
        return {"error": "sigma must be positive"}
    if not (0 < p < 1):
        return {"error": "p must be in (0,1)"}
    dist = NormalDist(mu, sigma)
    return {"result": dist.inv_cdf(p)}


def poisson_pmf(k: int, lam: float) -> Dict[str, Any]:
    if lam <= 0:
        return {"error": "lambda must be positive"}
    if k < 0:
        return {"error": "k must be >= 0"}
    return {"result": math.exp(-lam) * lam**k / math.factorial(k)}


def poisson_cdf(k: int, lam: float) -> Dict[str, Any]:
    if lam <= 0:
        return {"error": "lambda must be positive"}
    if k < 0:
        return {"error": "k must be >= 0"}
    s = 0.0
    for i in range(0, k+1):
        s += math.exp(-lam) * lam**i / math.factorial(i)
    return {"result": s}


def binomial_cdf(k: int, n: int, p: float) -> Dict[str, Any]:
    if not (0 <= p <= 1):
        return {"error": "p must be in [0,1]"}
    if not (0 <= k <= n):
        return {"error": "k must be in [0,n]"}
    from math import comb
    s = 0.0
    for i in range(0, k+1):
        s += comb(n, i) * (p**i) * ((1-p)**(n-i))
    return {"result": s}


def uniform_pdf(x: float, a: float, b: float) -> Dict[str, Any]:
    if b <= a:
        return {"error": "Require b > a for uniform"}
    if x < a or x > b:
        return {"result": 0.0}
    return {"result": 1.0 / (b - a)}


def uniform_cdf(x: float, a: float, b: float) -> Dict[str, Any]:
    if b <= a:
        return {"error": "Require b > a for uniform"}
    if x <= a:
        return {"result": 0.0}
    if x >= b:
        return {"result": 1.0}
    return {"result": (x - a) / (b - a)}


def exponential_pdf(x: float, lam: float) -> Dict[str, Any]:
    if lam <= 0:
        return {"error": "lambda must be positive"}
    if x < 0:
        return {"result": 0.0}
    return {"result": lam * math.exp(-lam * x)}


def exponential_cdf(x: float, lam: float) -> Dict[str, Any]:
    if lam <= 0:
        return {"error": "lambda must be positive"}
    if x < 0:
        return {"result": 0.0}
    return {"result": 1 - math.exp(-lam * x)}