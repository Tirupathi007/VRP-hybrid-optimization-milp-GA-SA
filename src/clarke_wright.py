"""
clarke_wright.py
Clarke-Wright Savings Algorithm for CVRP
IIT VRP Course Project

Algorithm Steps:
  1. Start: each customer on its own route (depot -> i -> depot)
  2. Compute savings s_ij = c(0,i) + c(0,j) - c(i,j)  for all i != j
  3. Sort savings descending
  4. Greedily merge routes if:
       - i is the LAST node of its route
       - j is the FIRST node of another route
       - merged demand <= Q
  5. Stop when no profitable merge remains

Complexity: O(n^2 log n) for sorting savings
"""

from vrp_parser import parse_vrp, solution_cost, route_demand, validate_solution


def clarke_wright(inst, num_vehicles=None):
    nodes = inst["nodes"]
    dist  = inst["dist"]
    q     = inst["capacity"]
    n     = inst["n"]

    # Step 1: initialise one route per customer
    routes = [[i] for i in range(1, n + 1)]

    # Step 2: compute all savings
    savings = []
    for i in range(1, n + 1):
        for j in range(1, n + 1):
            if i == j:
                continue
            s = dist[0][i] + dist[0][j] - dist[i][j]
            savings.append((s, i, j))

    # Step 3: sort descending
    savings.sort(reverse=True)

    # Helper: find which route contains a node, and its position
    def find_route(node):
        for idx, r in enumerate(routes):
            if node in r:
                pos = r.index(node)
                return idx, pos
        return None, None

    # Step 4: greedy merging
    for s, i, j in savings:
        if s <= 0:
            break
        ri, pi = find_route(i)
        rj, pj = find_route(j)
        if ri is None or rj is None or ri == rj:
            continue
        # i must be LAST in its route, j must be FIRST in its route
        if pi != len(routes[ri]) - 1:
            continue
        if pj != 0:
            continue
        merged = routes[ri] + routes[rj]
        if route_demand(merged, nodes) > q:
            continue
        if num_vehicles and len(routes) - 1 < num_vehicles:
            pass  # already within limit
        routes[ri] = merged
        routes.pop(rj)

    routes = [r for r in routes if r]
    return routes


def run(filepath, num_vehicles=None):
    inst = parse_vrp(filepath)
    routes = clarke_wright(inst, num_vehicles)
    cost   = solution_cost(routes, inst["dist"])
    ok, msg = validate_solution(routes, inst)

    print(f"\n{'='*55}")
    print(f"Clarke-Wright Savings  |  {inst['name']}")
    print(f"{'='*55}")
    print(f"Routes used : {len(routes)}")
    print(f"Total cost  : {cost:.4f}")
    print(f"Feasible    : {ok}  ({msg})")
    print(f"\nRoute detail:")
    for k, r in enumerate(routes):
        d = route_demand(r, inst["nodes"])
        c = __import__('vrp_parser').route_cost(r, inst["dist"])
        util = d / inst["capacity"] * 100
        print(f"  Vehicle {k+1:2d}: {[0]+r+[0]}  demand={d}/{inst['capacity']} ({util:.0f}%)  cost={c:.2f}")
    print(f"{'='*55}\n")
    return routes, cost, inst


if __name__ == "__main__":
    import sys
    fp = sys.argv[1] if len(sys.argv) > 1 else "input_data/instance_small.vrp"
    run(fp)
