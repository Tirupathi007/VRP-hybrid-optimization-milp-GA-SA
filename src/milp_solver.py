"""
milp_solver.py
Exact MILP Solver for CVRP using Gurobi
IIT VRP Course Project

Formulation: Arc-based model with MTZ subtour elimination
Decision variables:
  x[i,j,k] in {0,1}  -- 1 if vehicle k traverses arc (i,j)
  u[i,k]   >= 0      -- cumulative load on vehicle k after node i (MTZ)

Objective:
  min  SUM_{k,i,j}  c_ij * x[i,j,k]

Constraints:
  (C1) Coverage       : each customer visited exactly once
  (C2) Flow balance   : vehicle enters iff it exits every node
  (C3) Depot depart   : each vehicle leaves depot at most once
  (C4) MTZ capacity   : u[i,k] - u[j,k] + Q*x[i,j,k] <= Q - d_j
  (C5) Load bounds    : d_i <= u[i,k] <= Q
  (C6) Fleet size     : total vehicles used <= K

Note: MILP is exact for n <= ~20 within reasonable time.
      For n > 20, use time_limit parameter to get best bound.
"""

import os
import sys
import time
import math

sys.path.insert(0, os.path.dirname(__file__))
from vrp_parser import parse_vrp, route_demand, route_cost, validate_solution

try:
    import gurobipy as gp
    from gurobipy import GRB
    GUROBI_AVAILABLE = True
except ImportError:
    GUROBI_AVAILABLE = False


def solve_milp(inst, num_vehicles=None, time_limit=120, verbose=True):
    """
    Solve CVRP exactly using Gurobi MILP.

    Parameters
    ----------
    inst         : parsed instance dict from vrp_parser
    num_vehicles : max vehicles K (default = ceil(total_demand / Q))
    time_limit   : Gurobi time limit in seconds (default 120s)
    verbose      : print Gurobi log if True

    Returns
    -------
    dict with keys:
      routes       : list of routes (list of customer id lists)
      cost         : optimal/best cost found
      lower_bound  : LP relaxation lower bound (Z_LP*)
      gap          : optimality gap % (0 if proven optimal)
      status       : 'Optimal', 'TimeLimit', 'Infeasible'
      elapsed      : wall-clock time
      obj_bound    : Gurobi objective bound
    """
    if not GUROBI_AVAILABLE:
        raise RuntimeError("gurobipy not installed. Run: pip install gurobipy")

    nodes    = inst["nodes"]
    dist     = inst["dist"]
    capacity = inst["capacity"]
    n        = inst["n"]          # number of customers

    # Auto-estimate fleet size
    if num_vehicles is None:
        total_demand = sum(nodes[i]["demand"] for i in range(1, n + 1))
        num_vehicles = math.ceil(total_demand / capacity)
        num_vehicles = max(num_vehicles, 2)

    K = num_vehicles
    V = list(range(n + 1))         # all nodes including depot (0)
    C = list(range(1, n + 1))      # customers only
    Kv = list(range(K))            # vehicle indices

    t_start = time.time()

    # ── Build Gurobi model ────────────────────────────────────────────────────
    env = gp.Env(empty=True)
    env.setParam("OutputFlag", 1 if verbose else 0)
    env.setParam("LogToConsole", 1 if verbose else 0)
    env.start()

    m = gp.Model("CVRP", env=env)
    m.setParam("TimeLimit", time_limit)
    m.setParam("MIPGap", 1e-4)       # 0.01% gap tolerance
    m.setParam("Threads", 4)
    m.setParam("MIPFocus", 1)        # focus on finding good feasible solutions

    # ── Decision variables ────────────────────────────────────────────────────
    # x[i,j,k] = 1 if vehicle k goes from i to j
    x = {}
    for k in Kv:
        for i in V:
            for j in V:
                if i != j:
                    x[i, j, k] = m.addVar(
                        vtype=GRB.BINARY,
                        name=f"x_{i}_{j}_{k}",
                        obj=dist[i][j]          # cost coefficient in objective
                    )

    # u[i,k] = cumulative load after visiting i with vehicle k (MTZ variable)
    u = {}
    for k in Kv:
        for i in C:
            u[i, k] = m.addVar(
                lb=nodes[i]["demand"],
                ub=capacity,
                vtype=GRB.CONTINUOUS,
                name=f"u_{i}_{k}"
            )

    m.ModelSense = GRB.MINIMIZE
    m.update()

    # ── Constraints ───────────────────────────────────────────────────────────

    # C1: each customer visited exactly once across all vehicles
    for i in C:
        m.addConstr(
            gp.quicksum(x[i, j, k] for k in Kv for j in V if j != i) == 1,
            name=f"visit_{i}"
        )

    # C2: flow conservation at every node for every vehicle
    for k in Kv:
        for i in V:
            m.addConstr(
                gp.quicksum(x[i, j, k] for j in V if j != i) ==
                gp.quicksum(x[j, i, k] for j in V if j != i),
                name=f"flow_{i}_{k}"
            )

    # C3: each vehicle leaves depot at most once
    for k in Kv:
        m.addConstr(
            gp.quicksum(x[0, j, k] for j in C) <= 1,
            name=f"depot_depart_{k}"
        )

    # C4 + C5: MTZ subtour elimination + capacity
    for k in Kv:
        for i in C:
            for j in C:
                if i != j:
                    m.addConstr(
                        u[i, k] - u[j, k] + capacity * x[i, j, k]
                        <= capacity - nodes[j]["demand"],
                        name=f"mtz_{i}_{j}_{k}"
                    )

    # C6: no self-loops (already excluded by i != j in variable creation)
    # Tighten: depot cannot be mid-route destination with immediate re-departure
    for k in Kv:
        m.addConstr(
            gp.quicksum(x[i, 0, k] for i in C) <= 1,
            name=f"depot_return_{k}"
        )

    # ── Solve ─────────────────────────────────────────────────────────────────
    m.optimize()
    elapsed = time.time() - t_start

    # ── Extract solution ──────────────────────────────────────────────────────
    status_map = {
        GRB.OPTIMAL:    "Optimal",
        GRB.TIME_LIMIT: "TimeLimit",
        GRB.INFEASIBLE: "Infeasible",
        GRB.SUBOPTIMAL: "Suboptimal",
    }
    status = status_map.get(m.Status, f"Code_{m.Status}")

    if m.Status in (GRB.OPTIMAL, GRB.TIME_LIMIT, GRB.SUBOPTIMAL):
        if m.SolCount == 0:
            return {
                "routes": [], "cost": float("inf"),
                "lower_bound": m.ObjBound, "gap": 100.0,
                "status": status, "elapsed": elapsed,
                "obj_bound": m.ObjBound,
            }

        # Reconstruct routes from x variables
        routes = []
        for k in Kv:
            # Find arc sequence starting from depot
            arc_map = {}
            for i in V:
                for j in V:
                    if i != j and (i, j, k) in x:
                        if x[i, j, k].X > 0.5:
                            arc_map[i] = j

            if 0 not in arc_map:
                continue

            route = []
            cur = arc_map[0]
            while cur != 0:
                route.append(cur)
                cur = arc_map.get(cur, 0)
            if route:
                routes.append(route)

        cost       = m.ObjVal
        obj_bound  = m.ObjBound
        gap_pct    = abs(cost - obj_bound) / (abs(cost) + 1e-9) * 100

        return {
            "routes":      routes,
            "cost":        cost,
            "lower_bound": obj_bound,
            "gap":         gap_pct,
            "status":      status,
            "elapsed":     elapsed,
            "obj_bound":   obj_bound,
            "num_vehicles": K,
        }

    return {
        "routes": [], "cost": float("inf"),
        "lower_bound": 0, "gap": 100.0,
        "status": status, "elapsed": elapsed,
        "obj_bound": 0,
    }


def run(filepath, num_vehicles=None, time_limit=120, verbose=True):
    inst   = parse_vrp(filepath)
    print(f"\n{'='*60}")
    print(f"MILP Solver (Gurobi)  |  {inst['name']}")
    print(f"  n={inst['n']}, Q={inst['capacity']}, K={num_vehicles or 'auto'}, TL={time_limit}s")
    print(f"{'='*60}")

    result = solve_milp(inst, num_vehicles=num_vehicles,
                        time_limit=time_limit, verbose=verbose)

    ok, msg = validate_solution(result["routes"], inst) if result["routes"] else (False, "No solution")

    print(f"\nStatus      : {result['status']}")
    print(f"Optimal cost: {result['cost']:.4f}")
    print(f"Lower bound : {result['lower_bound']:.4f}")
    print(f"MIP gap     : {result['gap']:.4f}%")
    print(f"Feasible    : {ok}  ({msg})")
    print(f"Runtime     : {result['elapsed']:.3f}s")
    print(f"\nRoute detail:")
    for k, r in enumerate(result["routes"]):
        d = route_demand(r, inst["nodes"])
        c = route_cost(r, inst["dist"])
        print(f"  Vehicle {k+1:2d}: {[0]+r+[0]}  demand={d}/{inst['capacity']}  cost={c:.2f}")
    print(f"{'='*60}\n")
    return result, inst


if __name__ == "__main__":
    fp = sys.argv[1] if len(sys.argv) > 1 else "input_data/instance_small.vrp"
    tl = int(sys.argv[2]) if len(sys.argv) > 2 else 120
    run(fp, time_limit=tl)
