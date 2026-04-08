"""
simulated_annealing.py
Simulated Annealing Metaheuristic for CVRP
IIT VRP Course Project

Algorithm Steps:
  1. Build initial solution via Clarke-Wright
  2. Set T = T0 (initial temperature)
  3. Repeat for max_iter iterations:
       a. Generate neighbor via 2-opt or Or-opt
       b. delta = new_cost - current_cost
       c. If delta < 0: accept (improvement)
          Else: accept with prob exp(-delta / T)
       d. Cool: T = alpha * T
  4. Return best solution found

Acceptance criterion (Metropolis):
  P(accept) = exp(-delta / T)
  - At high T: almost any move accepted  (exploration)
  - At low  T: only improvements accepted (exploitation)
"""

import math
import random
import time
import copy
import sys

from vrp_parser import parse_vrp, solution_cost, route_cost, route_demand, validate_solution
from clarke_wright import clarke_wright


# ─── Neighborhood Operators ──────────────────────────────────────────────────

def two_opt(route):
    """Reverse a random sub-segment within a single route."""
    if len(route) < 4:
        return route[:]
    i = random.randint(1, len(route) - 2)
    j = random.randint(i + 1, len(route) - 1)
    return route[:i] + route[i:j+1][::-1] + route[j+1:]


def or_opt_relocate(routes, nodes, capacity):
    """Move one customer from one route to the best position in another route."""
    if len(routes) < 2:
        return None
    r1_idx = random.randrange(len(routes))
    if not routes[r1_idx]:
        return None
    pos = random.randrange(len(routes[r1_idx]))
    cust = routes[r1_idx][pos]

    # Pick a different route
    candidates = [i for i in range(len(routes)) if i != r1_idx]
    r2_idx = random.choice(candidates)

    new_demand = route_demand(routes[r2_idx], nodes) + nodes[cust]["demand"]
    if new_demand > capacity:
        return None

    new_routes = [r[:] for r in routes]
    new_routes[r1_idx].pop(pos)
    ins = random.randint(0, len(new_routes[r2_idx]))
    new_routes[r2_idx].insert(ins, cust)
    new_routes = [r for r in new_routes if r]
    return new_routes


def two_opt_star(routes, nodes, capacity):
    """
    2-opt* : exchange tails between two routes.
    Route A: a1 ... ai | ai+1 ... end
    Route B: b1 ... bj | bj+1 ... end
    New routes: A[:i+1] + B[j+1:], B[:j+1] + A[i+1:]
    """
    if len(routes) < 2:
        return None
    r1 = random.randrange(len(routes))
    r2 = random.randrange(len(routes))
    if r1 == r2 or not routes[r1] or not routes[r2]:
        return None
    i = random.randint(0, len(routes[r1]) - 1)
    j = random.randint(0, len(routes[r2]) - 1)
    new_r1 = routes[r1][:i+1] + routes[r2][j+1:]
    new_r2 = routes[r2][:j+1] + routes[r1][i+1:]
    if route_demand(new_r1, nodes) > capacity or route_demand(new_r2, nodes) > capacity:
        return None
    new_routes = [r[:] for r in routes]
    new_routes[r1] = new_r1
    new_routes[r2] = new_r2
    return [r for r in new_routes if r]


# ─── SA Core ─────────────────────────────────────────────────────────────────

def simulated_annealing(inst, T0=1000.0, alpha=0.995, max_iter=5000, seed=42):
    random.seed(seed)
    nodes    = inst["nodes"]
    dist     = inst["dist"]
    capacity = inst["capacity"]

    # Initial solution
    current_routes = clarke_wright(inst)
    current_cost   = solution_cost(current_routes, dist)
    best_routes    = copy.deepcopy(current_routes)
    best_cost      = current_cost

    T = T0
    history = []          # (iter, best_cost) for convergence plot
    accepted = rejected = 0

    t_start = time.time()

    for it in range(max_iter):
        # Choose operator randomly
        op = random.random()
        if op < 0.40:
            # Intra-route 2-opt
            ri = random.randrange(len(current_routes))
            new_routes = [r[:] for r in current_routes]
            new_routes[ri] = two_opt(current_routes[ri])
        elif op < 0.70:
            # Inter-route Or-opt (relocate)
            candidate = or_opt_relocate(current_routes, nodes, capacity)
            if candidate is None:
                T *= alpha
                continue
            new_routes = candidate
        else:
            # 2-opt*
            candidate = two_opt_star(current_routes, nodes, capacity)
            if candidate is None:
                T *= alpha
                continue
            new_routes = candidate

        new_cost = solution_cost(new_routes, dist)
        delta    = new_cost - current_cost

        # Metropolis acceptance
        if delta < 0 or (T > 1e-9 and random.random() < math.exp(-delta / T)):
            current_routes = new_routes
            current_cost   = new_cost
            accepted += 1
            if current_cost < best_cost:
                best_routes = copy.deepcopy(current_routes)
                best_cost   = current_cost
        else:
            rejected += 1

        T *= alpha
        if it % 50 == 0:
            history.append((it, best_cost))

    elapsed = time.time() - t_start
    history.append((max_iter, best_cost))

    return {
        "routes":   best_routes,
        "cost":     best_cost,
        "history":  history,
        "elapsed":  elapsed,
        "accepted": accepted,
        "rejected": rejected,
        "T_final":  T,
    }


def run(filepath, T0=1000.0, alpha=0.995, max_iter=5000):
    inst   = parse_vrp(filepath)
    result = simulated_annealing(inst, T0=T0, alpha=alpha, max_iter=max_iter)

    ok, msg = validate_solution(result["routes"], inst)
    rate = result["accepted"] / (result["accepted"] + result["rejected"]) * 100

    print(f"\n{'='*55}")
    print(f"Simulated Annealing  |  {inst['name']}")
    print(f"  T0={T0}, alpha={alpha}, iters={max_iter}")
    print(f"{'='*55}")
    print(f"Best cost    : {result['cost']:.4f}")
    print(f"Routes used  : {len(result['routes'])}")
    print(f"Feasible     : {ok}  ({msg})")
    print(f"Acceptance % : {rate:.1f}%")
    print(f"T_final      : {result['T_final']:.6f}")
    print(f"Runtime      : {result['elapsed']:.3f}s")
    print(f"\nRoute detail:")
    for k, r in enumerate(result["routes"]):
        d = route_demand(r, inst["nodes"])
        c = route_cost(r, inst["dist"])
        print(f"  Vehicle {k+1:2d}: {[0]+r+[0]}  demand={d}/{inst['capacity']}  cost={c:.2f}")
    print(f"{'='*55}\n")
    return result, inst


if __name__ == "__main__":
    fp = sys.argv[1] if len(sys.argv) > 1 else "input_data/instance_small.vrp"
    run(fp)
