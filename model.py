"""Production LP and basis calculations, independent of the web interface.

Live solutions use SciPy/HiGHS. No Gurobi installation or licence is required.
"""
from dataclasses import dataclass
import numpy as np
from scipy.optimize import linprog

PRODUCTS = ("A", "B", "C")
RESOURCES = ("Machines", "Staff", "Material")
USAGE = np.array([[4., 3., 5.], [2., 4., 3.], [3., 2., 4.]])
BASE_CAPACITIES = (240., 180., 200.)
BASE_PROFITS = (48., 40., 55.)
BASE_PLAN = np.array([33.2, 22.4, 8.])
BASE_PROFIT = 2929.6
G = np.vstack([USAGE, [0., 0., -1.], [-2., 1., 0.]])
BASIS_INVERSE = np.array([
    [.4, -.3, 0., -1.1, 0.],
    [-.2, .4, 0., -.2, 0.],
    [0., 0., 0., 1., 0.],
    [-.8, .1, 1., -.3, 0.],
    [1., -1., 0., -2., 1.],
])
BASIC_NAMES = ("A", "B", "C", "Unused material", "2A minus B")
TOL = 1e-7


@dataclass
class Solution:
    status: str
    capacities: tuple
    profits: tuple
    minimum_c: float
    plan: np.ndarray | None = None
    profit: float | None = None
    margins: np.ndarray | None = None
    shadow_prices: np.ndarray | None = None
    message: str = ""


def solve(capacities=BASE_CAPACITIES, profit_a=48., minimum_c=8.):
    """Solve the original continuous model with selected inputs changed."""
    caps = np.asarray(capacities, dtype=float)
    if caps.shape != (3,) or not np.all(np.isfinite(caps)) or np.any(caps < 0):
        raise ValueError("Provide three finite, non-negative resource capacities.")
    if not np.isfinite(profit_a) or not np.isfinite(minimum_c) or minimum_c < 0:
        raise ValueError("Unit profit must be finite and minimum C non-negative.")
    profits = np.array([profit_a, 40., 55.], dtype=float)
    rhs = np.r_[caps, -minimum_c, 0.]
    result = linprog(-profits, A_ub=G, b_ub=rhs,
                     bounds=[(0., None)] * 3, method="highs")
    status = {0: "Optimal", 1: "Limit reached", 2: "Infeasible",
              3: "Unbounded", 4: "Solver error"}.get(result.status, "Solver error")
    common = dict(status=status, capacities=tuple(caps), profits=tuple(profits),
                  minimum_c=float(minimum_c), message=result.message)
    if not result.success:
        return Solution(**common)
    plan = result.x.copy()
    margins = rhs - G @ plan
    margins[np.abs(margins) < 1e-9] = 0.
    # HiGHS minimises -profit. Convert back to maximisation duals.
    dual = -np.asarray(result.ineqlin.marginals)
    # The fourth stored row is -C <= -q; show the price for C >= q.
    dual[3] *= -1
    dual[np.abs(dual) < 1e-9] = 0.
    return Solution(**common, plan=plan, profit=float(-result.fun),
                    margins=margins, shadow_prices=dual)


def constraint_rows(solution):
    if solution.plan is None:
        return []
    q = solution.plan
    actual = [*list(USAGE @ q), q[2], q[1]]
    limits = [*solution.capacities, solution.minimum_c, 2 * q[0]]
    names = ["Machine hours", "Staff hours", "Material", "Minimum C", "B ≤ 2A"]
    senses = ["≤", "≤", "≤", "≥", "≤"]
    return [{"Constraint": n, "Used or produced": float(a), "Sense": sense,
             "Limit": float(b), "Margin": float(m),
             "Binding": "Yes" if abs(m) <= TOL else "No",
             "Shadow price (£ per RHS unit)": float(price)}
            for n, a, sense, b, m, price in
            zip(names, actual, senses, limits, solution.margins, solution.shadow_prices)]


def baseline_basis_values(capacities=BASE_CAPACITIES, minimum_c=8.):
    """Candidate values for the original basis; do not treat them as a new solve."""
    return BASIS_INVERSE @ np.r_[np.asarray(capacities, float), minimum_c, 0.]


def baseline_basis_is_feasible(capacities=BASE_CAPACITIES, minimum_c=8.):
    return bool(np.all(baseline_basis_values(capacities, minimum_c) >= -TOL))


def baseline_prediction(capacities=BASE_CAPACITIES, minimum_c=8.):
    caps = np.asarray(capacities)
    return float(BASE_PROFIT + np.dot([11.2, 1.6, 0.], caps - BASE_CAPACITIES)
                 - 5.8 * (minimum_c - 8.))


def solution_record(solution):
    row = {"Status": solution.status, "Machine hours": solution.capacities[0],
           "Staff hours": solution.capacities[1], "Material units": solution.capacities[2],
           "Unit profit A": solution.profits[0], "Minimum C": solution.minimum_c,
           "Profit": solution.profit}
    row.update({p: (float(solution.plan[i]) if solution.plan is not None else None)
                for i, p in enumerate(PRODUCTS)})
    return row


def coefficient_plans():
    return [
        {"Unit profit A": "p < 30", "Plan (A, B, C)": "(0, 0, 48)", "Profit": "2640"},
        {"Unit profit A": "30 < p < 470/11", "Plan (A, B, C)": "(9, 18, 30)", "Profit": "9p + 2370"},
        {"Unit profit A": "470/11 < p < 160/3", "Plan (A, B, C)": "(33.2, 22.4, 8)", "Profit": "33.2p + 1336"},
        {"Unit profit A": "p > 160/3", "Plan (A, B, C)": "(50, 0, 8)", "Profit": "50p + 440"},
    ]


def alternative_plans(p):
    boundaries = [(30., [0, 0, 48], [9, 18, 30]),
                  (470/11, [9, 18, 30], BASE_PLAN),
                  (160/3, BASE_PLAN, [50, 0, 8])]
    for boundary, first, second in boundaries:
        if abs(p - boundary) < TOL:
            return [w * np.array(first) + (1-w) * np.array(second)
                    for w in (0., .5, 1.)]
    return []
