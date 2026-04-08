"""
vrp_parser.py
Parses .vrp files in TSPLIB format (EUC_2D CVRP instances)
IIT VRP Course Project
"""

import math
import os


def parse_vrp(filepath):
    """
    Parse a .vrp file and return an instance dict with:
      nodes       : list of dicts {id, x, y, demand}
      n           : number of customers (excluding depot)
      capacity    : vehicle capacity Q
      name        : instance name
      dist_matrix : n+1 x n+1 Euclidean distance matrix
    """
    data = {}
    nodes = []
    demands = {}
    section = None

    with open(filepath) as f:
        for raw in f:
            line = raw.strip()
            if not line or line == "EOF":
                continue

            # Section headers
            if line == "NODE_COORD_SECTION":
                section = "coord"
                continue
            if line == "DEMAND_SECTION":
                section = "demand"
                continue
            if line == "DEPOT_SECTION":
                section = "depot"
                continue

            # Key-value metadata
            if ":" in line and section is None:
                key, _, val = line.partition(":")
                data[key.strip()] = val.strip()
                continue

            # Parse coords
            if section == "coord":
                parts = line.split()
                nodes.append({"id": int(parts[0]), "x": float(parts[1]), "y": float(parts[2])})

            # Parse demands
            elif section == "demand":
                parts = line.split()
                demands[int(parts[0])] = int(parts[1])

    # Attach demands
    for node in nodes:
        node["demand"] = demands.get(node["id"], 0)

    n = len(nodes) - 1  # exclude depot
    capacity = int(data.get("CAPACITY", 100))
    name = data.get("NAME", os.path.basename(filepath))

    # Build Euclidean distance matrix
    size = len(nodes)
    dist = [[0.0] * size for _ in range(size)]
    for i in range(size):
        for j in range(size):
            if i != j:
                dx = nodes[i]["x"] - nodes[j]["x"]
                dy = nodes[i]["y"] - nodes[j]["y"]
                dist[i][j] = math.sqrt(dx * dx + dy * dy)

    return {
        "name": name,
        "nodes": nodes,
        "n": n,
        "capacity": capacity,
        "dist": dist,
    }


def route_cost(route, dist):
    """Total travel cost of a route (depot -> customers -> depot)."""
    if not route:
        return 0.0
    cost = dist[0][route[0]]
    for i in range(len(route) - 1):
        cost += dist[route[i]][route[i + 1]]
    cost += dist[route[-1]][0]
    return cost


def solution_cost(routes, dist):
    return sum(route_cost(r, dist) for r in routes)


def route_demand(route, nodes):
    return sum(nodes[i]["demand"] for i in route)


def validate_solution(routes, inst):
    """Check feasibility: all customers visited once, capacity respected."""
    nodes = inst["nodes"]
    q = inst["capacity"]
    n = inst["n"]
    visited = []
    for r in routes:
        d = route_demand(r, nodes)
        if d > q:
            return False, f"Capacity violated: {d} > {q}"
        visited.extend(r)
    expected = set(range(1, n + 1))
    got = set(visited)
    if got != expected:
        missing = expected - got
        extra = got - expected
        return False, f"Missing: {missing}, Extra: {extra}"
    return True, "OK"


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "input_data/instance_small.vrp"
    inst = parse_vrp(path)
    print(f"Instance : {inst['name']}")
    print(f"Customers: {inst['n']}")
    print(f"Capacity : {inst['capacity']}")
    print(f"Nodes    :")
    for node in inst["nodes"]:
        print(f"  {node['id']:2d}  x={node['x']:5.1f}  y={node['y']:5.1f}  d={node['demand']}")
