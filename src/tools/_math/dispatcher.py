"""
High-level dispatcher for 'math' tool.
Routes to specialized modules and basic ops. Always returns explicit error dicts.
"""
from __future__ import annotations
from typing import Any, Dict

from .dispatch_core import err
from .dispatch_basic import (
    do_add, do_subtract, do_multiply, do_divide, do_power, do_mod,
    do_sqrt, do_trig, do_ln_log, do_exp, do_complex, do_conjugate,
    do_magnitude, do_phase,
)

# Advanced modules map (imported lazily inside functions to keep imports light)

def handle(operation: str, **params) -> Dict[str, Any]:
    op = (operation or "").strip()
    op_l = op.lower()
    if not op_l:
        return err("Operation is required", op)

    # Basic arithmetic / transcendental / complex
    if op_l in ("add", "sum"):
        return do_add(params, op)
    if op_l in ("subtract", "sub"):
        return do_subtract(params, op)
    if op_l in ("multiply", "mul", "product"):
        return do_multiply(params, op)
    if op_l in ("divide", "div"):
        return do_divide(params, op)
    if op_l in ("power", "pow"):
        return do_power(params, op)
    if op_l in ("mod", "modulo"):
        return do_mod(params, op)
    if op_l == "sqrt":
        return do_sqrt(params, op)
    if op_l in ("sin", "cos", "tan"):
        return do_trig(params, op_l)
    if op_l in ("ln", "log"):
        return do_ln_log(params, op_l)
    if op_l == "exp":
        return do_exp(params, op)
    if op_l in ("complex", "to_complex"):
        return do_complex(params, op)
    if op_l == "conjugate":
        return do_conjugate(params, op)
    if op_l in ("abs", "magnitude", "modulus"):
        return do_magnitude(params, op)
    if op_l == "phase":
        return do_phase(params, op)

    # Advanced symbolic / calculus / LA / probas / solvers / number theory / sums
    try:
        # Import inside to avoid mandatory deps on load
        from .symbolic import SymbolicOps
        from .calculus import limit as calc_limit, series as calc_series, gradient as calc_gradient, jacobian as calc_jacobian, hessian as calc_hessian
        from .linear_algebra import LinearAlgebraOps
        from .linear_algebra_ext import pinv as la_pinv, cond as la_cond, trace as la_trace, nullspace as la_nullspace, lu as la_lu, qr as la_qr
        from .probability import ProbabilityOps
        from .probability_ext import (
            normal_cdf, normal_ppf, poisson_pmf, poisson_cdf, binomial_cdf,
            uniform_pdf, uniform_cdf, exponential_pdf, exponential_cdf,
        )
        from .stats_ext import linear_regression, correlation, covariance, zscore, moving_average
        from .polynomial import poly_roots, poly_factor, poly_expand
        from .solvers import solve_eq, solve_system, nsolve_expr, root_find, optimize_1d
        from .expression_parser import ExpressionParser
        from .number_theory import NumberTheoryOps
        from .summation import sum_finite, product_finite, sum_infinite
        from .high_precision import HighPrecisionOps
        from .advanced import AdvancedOps
    except Exception as e:
        return err(f"Module import error: {e}", op)

    # Expression evaluation
    if op_l in ("eval", "evaluate"):
        try:
            parser = ExpressionParser()
            return parser.evaluate(
                params.get("expr") or params.get("expression"),
                params.get("variables") or params.get("vars"),
                params.get("precision"),
            )
        except Exception as e:
            return err(f"Expression evaluation error: {e}", op)

    # Symbolic
    if op_l in {"derivative", "integral", "simplify", "expand", "factor"}:
        try:
            return SymbolicOps().handle(op_l, **params)
        except Exception as e:
            return err(f"Symbolic operation failed: {e}", op)

    # Calculus
    if op_l == "limit":
        return calc_limit(
            expression=params.get("expression") or params.get("expr"),
            variable=params.get("variable") or params.get("var") or "x",
            point=params.get("point"),
            direction=params.get("direction", "+"),
        )
    if op_l == "series":
        return calc_series(
            expression=params.get("expression") or params.get("expr"),
            variable=params.get("variable") or params.get("var") or "x",
            point=params.get("point", 0),
            order=int(params.get("order", 6)),
        )
    if op_l == "gradient":
        return calc_gradient(
            expression=params.get("expression") or params.get("expr"),
            variables=params.get("variables") or params.get("vars") or [],
        )
    if op_l == "jacobian":
        return calc_jacobian(
            expressions=params.get("expressions") or params.get("exprs") or [],
            variables=params.get("variables") or params.get("vars") or [],
        )
    if op_l == "hessian":
        return calc_hessian(
            expression=params.get("expression") or params.get("expr"),
            variables=params.get("variables") or params.get("vars") or [],
        )

    # Linear algebra (base)
    LA_OPS = {
        "mat_add", "mat_mul", "mat_det", "mat_inv", "mat_transpose", "mat_rank",
        "mat_solve", "eig", "vec_add", "dot", "cross", "norm",
    }
    if op_l in LA_OPS:
        return LinearAlgebraOps().handle(op_l, **params)

    # Linear algebra (extensions)
    if op_l in {"pinv", "cond", "trace", "nullspace", "lu", "qr"}:
        try:
            if op_l == "pinv":
                return la_pinv(params.get("A") or params.get("matrix"))
            if op_l == "cond":
                return la_cond(params.get("A") or params.get("matrix"), params.get("p", 2))
            if op_l == "trace":
                return la_trace(params.get("A") or params.get("matrix"))
            if op_l == "nullspace":
                return la_nullspace(params.get("A") or params.get("matrix"))
            if op_l == "lu":
                return la_lu(params.get("A") or params.get("matrix"))
            if op_l == "qr":
                return la_qr(params.get("A") or params.get("matrix"))
        except Exception as e:
            return err(f"Linear algebra ext error: {e}", op)

    # Probability (basic)
    if op_l in {"mean", "median", "mode", "stdev", "variance", "combination", "permutation", "normal_pdf", "binomial"}:
        # ProbabilityOps handles its own inputs
        try:
            if "values" in params and "data" not in params:
                params = dict(params)
                params["data"] = params["values"]
            return ProbabilityOps().handle(op_l, **params)
        except Exception as e:
            return err(f"Probability error: {e}", op)

    # Distributions ext
    if op_l in {"normal_cdf", "normal_ppf", "poisson_pmf", "poisson_cdf", "binomial_cdf", "uniform_pdf", "uniform_cdf", "exponential_pdf", "exponential_cdf"}:
        try:
            if op_l == "normal_cdf":
                return normal_cdf(float(params.get("x")), float(params.get("mu", 0)), float(params.get("sigma", 1)))
            if op_l == "normal_ppf":
                return normal_ppf(float(params.get("p")), float(params.get("mu", 0)), float(params.get("sigma", 1)))
            if op_l == "poisson_pmf":
                return poisson_pmf(int(params.get("k")), float(params.get("lam") or params.get("lambda")))
            if op_l == "poisson_cdf":
                return poisson_cdf(int(params.get("k")), float(params.get("lam") or params.get("lambda")))
            if op_l == "binomial_cdf":
                return binomial_cdf(int(params.get("k")), int(params.get("n")), float(params.get("p")))
            if op_l == "uniform_pdf":
                return uniform_pdf(float(params.get("x")), float(params.get("a")), float(params.get("b")))
            if op_l == "uniform_cdf":
                return uniform_cdf(float(params.get("x")), float(params.get("a")), float(params.get("b")))
            if op_l == "exponential_pdf":
                return exponential_pdf(float(params.get("x")), float(params.get("lam") or params.get("lambda")))
            if op_l == "exponential_cdf":
                return exponential_cdf(float(params.get("x")), float(params.get("lam") or params.get("lambda")))
        except Exception as e:
            return err(f"Distribution error: {e}", op)

    # Stats extensions
    if op_l == "linear_regression":
        return linear_regression(params.get("x") or params.get("x_data"), params.get("y") or params.get("y_data"))
    if op_l == "correlation":
        return correlation(params.get("x") or params.get("x_data"), params.get("y") or params.get("y_data"))
    if op_l == "covariance":
        return covariance(params.get("x") or params.get("x_data"), params.get("y") or params.get("y_data"), bool(params.get("sample", True)))
    if op_l == "zscore":
        return zscore(params.get("data") or params.get("values"))
    if op_l == "moving_average":
        return moving_average(params.get("data") or params.get("values"), int(params.get("window", 1)))

    # Polynomial
    if op_l == "poly_roots":
        return poly_roots(params.get("coeffs"))
    if op_l == "poly_factor":
        return poly_factor(params.get("expression") or params.get("expr"))
    if op_l == "poly_expand":
        return poly_expand(params.get("expression") or params.get("expr"))

    # Solvers
    if op_l == "solve_eq":
        return solve_eq(params.get("equation"), params.get("variable") or params.get("var"))
    if op_l == "solve_system":
        return solve_system(params.get("equations") or [], params.get("variables") or params.get("vars") or [])
    if op_l == "nsolve":
        return nsolve_expr(params.get("expression") or params.get("expr"), params.get("variable") or params.get("var"), params.get("guess"))
    if op_l == "root_find":
        return root_find(params.get("expression") or params.get("expr"), params.get("variable") or params.get("var"), params.get("x0"), float(params.get("tol", 1e-7)), int(params.get("max_iter", 50)))
    if op_l == "optimize_1d":
        return optimize_1d(
            params.get("expression") or params.get("expr"),
            params.get("variable") or params.get("var"),
            float(params.get("a")), float(params.get("b")),
            params.get("goal", "min"),
            float(params.get("tol", 1e-6)), int(params.get("max_iter", 100))
        )

    # Number theory
    if op_l in {"nth_prime", "prime_approx", "is_prime", "next_prime", "prev_prime", "prime_factors", "factorize", "euler_phi", "primes_range"}:
        return NumberTheoryOps().handle(op_l, **params)

    # Summations / products
    if op_l == "sum_finite":
        return sum_finite(params.get("expression") or params.get("expr"), params.get("index", "i"), params.get("start"), params.get("end"))
    if op_l == "product_finite":
        return product_finite(params.get("expression") or params.get("expr"), params.get("index", "i"), params.get("start"), params.get("end"))
    if op_l == "sum_infinite":
        return sum_infinite(params.get("expression") or params.get("expr"), params.get("index", "i"), params.get("start"))

    # High precision
    if op_l == "eval_precise":
        return HighPrecisionOps().handle(op_l, **params)

    return err(f"Unknown operation: {operation}", op)
