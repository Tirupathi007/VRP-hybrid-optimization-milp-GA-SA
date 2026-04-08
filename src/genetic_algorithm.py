"""
genetic_algorithm.py
Genetic Algorithm for CVRP using Permutation Chromosome + OX Crossover
IIT VRP Course Project

Chromosome representation:
  A permutation of customer IDs [1..n], decoded left-to-right:
  Start a new route whenever adding the next customer would exceed Q.

  Example: [3, 7, 2, 5, 1, 4, 6]  Q=50
    Route 1: [3,7,2] until demand > Q → new route
    Route 2: [5,1]   → new route
    Route 3: [4,6]
    Depot (0) is implicit at start/end of every route.

Algorithm:
  1. Initialise population (CW solution + random shuffles)
  2. Evaluate fitness = total_cost + penalty * max(0, routes - K)
  3. Tournament selection
  4. Order Crossover (OX)
  5. Swap mutation
  6. Elitism: carry best chromosome unchanged
  7. Repeat for G generations
"""

import random
import time
import copy
import sys

from vrp_parser import parse_vrp, solution_cost, route_cost, route_demand, validate_solution
from clarke_wright import clarke_wright


# ─── Chromosome encoding / decoding ─────────────────────────────────────────

def encode(routes):
    """Flatten route list to permutation."""
    return [cust for route in routes for cust in route]


def decode(chrom, nodes, capacity):
    """Split permutation into routes by capacity constraint."""
    routes = []
    current = []
    load = 0
    for cust in chrom:
        d = nodes[cust]["demand"]
        if load + d > capacity and current:
            routes.append(current)
            current = []
            load = 0
        current.append(cust)
        load += d
    if current:
        routes.append(current)
    return routes


def fitness(chrom, nodes, dist, capacity, max_vehicles, penalty=1e5):
    routes = decode(chrom, nodes, capacity)
    cost   = solution_cost(routes, dist)
    viol   = max(0, len(routes) - max_vehicles)
    return cost + penalty * viol


# ─── Genetic Operators ───────────────────────────────────────────────────────

def ox_crossover(p1, p2):
    """
    Order Crossover (OX):
    1. Choose random segment from p1
    2. Fill rest from p2 in order, skipping duplicates
    """
    n = len(p1)
    a, b = sorted(random.sample(range(n), 2))
    child = [-1] * n
    child[a:b+1] = p1[a:b+1]
    filled = set(child[a:b+1])
    ci = (b + 1) % n
    for pi in range(n):
        gene = p2[(b + 1 + pi) % n]
        if gene not in filled:
            child[ci] = gene
            filled.add(gene)
            ci = (ci + 1) % n
    return child


def swap_mutation(chrom, rate):
    """Randomly swap two genes with probability = rate."""
    c = chrom[:]
    if random.random() < rate:
        i, j = random.sample(range(len(c)), 2)
        c[i], c[j] = c[j], c[i]
    return c


def inversion_mutation(chrom, rate):
    """Invert a random sub-segment."""
    c = chrom[:]
    if random.random() < rate:
        i, j = sorted(random.sample(range(len(c)), 2))
        c[i:j+1] = c[i:j+1][::-1]
    return c


def tournament_select(pop, scores, k=3):
    """Return the best among k random candidates."""
    competitors = random.sample(list(zip(pop, scores)), k)
    return min(competitors, key=lambda x: x[1])[0]


# ─── GA Core ─────────────────────────────────────────────────────────────────

def genetic_algorithm(inst, pop_size=40, generations=200,
                       cx_rate=0.80, mut_rate=0.15,
                       max_vehicles=None, seed=42):
    random.seed(seed)
    nodes    = inst["nodes"]
    dist     = inst["dist"]
    capacity = inst["capacity"]
    n        = inst["n"]
    if max_vehicles is None:
        max_vehicles = n  # no hard limit

    fit = lambda chrom: fitness(chrom, nodes, dist, capacity, max_vehicles)

    # Step 1: Initialise population
    cw_routes = clarke_wright(inst)
    base      = encode(cw_routes)
    population = [base]
    while len(population) < pop_size:
        shuffled = base[:]
        random.shuffle(shuffled)
        population.append(shuffled)

    best_chrom  = min(population, key=fit)
    best_score  = fit(best_chrom)
    history     = []
    t_start     = time.time()

    for gen in range(generations):
        scores   = [fit(c) for c in population]
        best_idx = scores.index(min(scores))
        if scores[best_idx] < best_score:
            best_score = scores[best_idx]
            best_chrom = population[best_idx][:]

        new_pop = [population[best_idx][:]]  # elitism

        while len(new_pop) < pop_size:
            p1 = tournament_select(population, scores)
            p2 = tournament_select(population, scores)
            # Crossover
            child = ox_crossover(p1, p2) if random.random() < cx_rate else p1[:]
            # Mutation (alternating operators)
            if random.random() < 0.5:
                child = swap_mutation(child, mut_rate)
            else:
                child = inversion_mutation(child, mut_rate)
            new_pop.append(child)

        population = new_pop
        if gen % 5 == 0:
            history.append((gen, best_score))

    elapsed = time.time() - t_start
    history.append((generations, best_score))

    best_routes = decode(best_chrom, nodes, capacity)
    return {
        "routes":  best_routes,
        "cost":    solution_cost(best_routes, dist),
        "history": history,
        "elapsed": elapsed,
    }


def run(filepath, pop_size=40, generations=200, cx_rate=0.80, mut_rate=0.15):
    inst   = parse_vrp(filepath)
    result = genetic_algorithm(inst, pop_size=pop_size,
                                generations=generations,
                                cx_rate=cx_rate, mut_rate=mut_rate)
    ok, msg = validate_solution(result["routes"], inst)

    print(f"\n{'='*55}")
    print(f"Genetic Algorithm  |  {inst['name']}")
    print(f"  pop={pop_size}, gens={generations}, cx={cx_rate}, mut={mut_rate}")
    print(f"{'='*55}")
    print(f"Best cost   : {result['cost']:.4f}")
    print(f"Routes used : {len(result['routes'])}")
    print(f"Feasible    : {ok}  ({msg})")
    print(f"Runtime     : {result['elapsed']:.3f}s")
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
