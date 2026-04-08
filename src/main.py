"""
main.py
Master runner for VRP Metaheuristics Project
IIT Course Project

Usage:
  python main.py                          # runs all instances
  python main.py instance_small.vrp      # runs one instance
"""

import sys
import os
import csv
import json
import time

sys.path.insert(0, os.path.dirname(__file__))

from vrp_parser       import parse_vrp, solution_cost, route_demand, validate_solution
from clarke_wright    import clarke_wright
from simulated_annealing import simulated_annealing
from genetic_algorithm   import genetic_algorithm

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def run_instance(filepath):
    inst = parse_vrp(filepath)
    name = inst["name"]
    print(f"\n{'#'*60}")
    print(f"  Instance: {name}  |  n={inst['n']}  |  Q={inst['capacity']}")
    print(f"{'#'*60}")

    results = {}

    # 1. Clarke-Wright
    t0 = time.perf_counter()
    cw_routes = clarke_wright(inst)
    cw_time   = time.perf_counter() - t0
    cw_cost   = solution_cost(cw_routes, inst["dist"])
    cw_ok, _  = validate_solution(cw_routes, inst)
    results["CW"] = {"cost": cw_cost, "routes": len(cw_routes),
                     "time": cw_time, "feasible": cw_ok, "history": []}
    print(f"  CW   cost={cw_cost:.2f}  routes={len(cw_routes)}  t={cw_time:.3f}s")

    # 2. Simulated Annealing
    sa = simulated_annealing(inst, T0=1000, alpha=0.995, max_iter=5000)
    sa_ok, _ = validate_solution(sa["routes"], inst)
    results["SA"] = {"cost": sa["cost"], "routes": len(sa["routes"]),
                     "time": sa["elapsed"], "feasible": sa_ok,
                     "history": sa["history"]}
    print(f"  SA   cost={sa['cost']:.2f}  routes={len(sa['routes'])}  t={sa['elapsed']:.3f}s")

    # 3. Genetic Algorithm
    ga = genetic_algorithm(inst, pop_size=40, generations=200)
    ga_ok, _ = validate_solution(ga["routes"], inst)
    results["GA"] = {"cost": ga["cost"], "routes": len(ga["routes"]),
                     "time": ga["elapsed"], "feasible": ga_ok,
                     "history": ga["history"]}
    print(f"  GA   cost={ga['cost']:.2f}  routes={len(ga['routes'])}  t={ga['elapsed']:.3f}s")

    # Optimality gaps vs CW bound
    for alg in ["SA", "GA"]:
        gap = (results[alg]["cost"] - cw_cost) / cw_cost * 100
        results[alg]["gap_vs_cw"] = gap
        sign = "+" if gap > 0 else ""
        print(f"  Gap {alg} vs CW: {sign}{gap:.2f}%")

    results["CW"]["gap_vs_cw"] = 0.0

    # Save route details
    best_alg  = min(["CW","SA","GA"], key=lambda a: results[a]["cost"])
    best_data = {"CW": cw_routes, "SA": sa["routes"], "GA": ga["routes"]}

    save_routes(name, best_data, inst, results)
    return inst, results


def save_routes(name, route_data, inst, summary):
    """Write per-instance output files."""
    safe = name.replace(" ", "_")

    # CSV: summary
    csv_path = os.path.join(OUTPUT_DIR, f"{safe}_summary.csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Algorithm", "Cost", "Routes", "Time_s", "Gap_vs_CW_%", "Feasible"])
        for alg in ["CW", "SA", "GA"]:
            r = summary[alg]
            w.writerow([alg, f"{r['cost']:.4f}", r["routes"],
                        f"{r['time']:.4f}", f"{r.get('gap_vs_cw',0):.2f}", r["feasible"]])
    print(f"  >> Summary CSV saved: {csv_path}")

    # JSON: route details
    json_path = os.path.join(OUTPUT_DIR, f"{safe}_routes.json")
    out = {}
    for alg, routes in route_data.items():
        out[alg] = []
        for k, r in enumerate(routes):
            out[alg].append({
                "vehicle": k + 1,
                "route": [0] + r + [0],
                "demand": route_demand(r, inst["nodes"]),
                "capacity": inst["capacity"],
                "cost": round(__import__('vrp_parser').route_cost(r, inst["dist"]), 4),
            })
    with open(json_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"  >> Route JSON saved : {json_path}")

    # Convergence CSV for SA/GA
    for alg, hist_key in [("SA", "SA"), ("GA", "GA")]:
        hist = summary[alg].get("history", [])
        if hist:
            conv_path = os.path.join(OUTPUT_DIR, f"{safe}_{alg}_convergence.csv")
            with open(conv_path, "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["Iteration", "Best_Cost"])
                for it, cost in hist:
                    w.writerow([it, f"{cost:.4f}"])
            print(f"  >> Convergence CSV  : {conv_path}")


def run_all():
    input_dir = os.path.join(os.path.dirname(__file__), "..", "input_data")
    files = sorted(f for f in os.listdir(input_dir) if f.endswith(".vrp"))
    if not files:
        print("No .vrp files found in input_data/")
        return

    all_results = {}
    for fname in files:
        fp = os.path.join(input_dir, fname)
        inst, results = run_instance(fp)
        all_results[inst["name"]] = {
            "n": inst["n"], "Q": inst["capacity"], **{
                alg: {"cost": round(results[alg]["cost"], 4),
                      "routes": results[alg]["routes"],
                      "gap": round(results[alg].get("gap_vs_cw", 0), 3)}
                for alg in ["CW", "SA", "GA"]
            }
        }

    # Master comparison CSV
    master_path = os.path.join(OUTPUT_DIR, "master_comparison.csv")
    with open(master_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Instance","n","Q",
                    "CW_Cost","SA_Cost","GA_Cost",
                    "SA_Gap_%","GA_Gap_%",
                    "CW_Routes","SA_Routes","GA_Routes"])
        for iname, d in all_results.items():
            w.writerow([iname, d["n"], d["Q"],
                        d["CW"]["cost"], d["SA"]["cost"], d["GA"]["cost"],
                        d["SA"]["gap"],  d["GA"]["gap"],
                        d["CW"]["routes"],d["SA"]["routes"],d["GA"]["routes"]])
    print(f"\n>> Master comparison: {master_path}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_instance(sys.argv[1])
    else:
        run_all()
