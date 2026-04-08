"""
compare_all.py
Full Comparison: MILP (Gurobi) vs SA vs GA vs CW
IIT VRP Course Project

Gurobi restricted license: ~2000 variable limit
  n=10, K=3 -> ~330 vars  -> MILP exact optimal  ✓
  n=15, K=3 -> ~765 vars  -> MILP exact optimal  ✓
  n=25+     -> >2000 vars -> skipped, heuristics only
"""

import os, sys, csv, time, math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

from vrp_parser          import parse_vrp, solution_cost, route_demand, route_cost
from clarke_wright       import clarke_wright
from simulated_annealing import simulated_annealing
from genetic_algorithm   import genetic_algorithm
from milp_solver         import solve_milp

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

COLORS    = {"MILP":"#E24B4A","SA":"#BA7517","GA":"#1D9E75","CW":"#378ADD"}
NODE_COLS = ["#378ADD","#1D9E75","#D85A30","#D4537E","#7F77DD",
             "#BA7517","#639922","#E24B4A","#0F6E56","#993C1D"]
MILP_MAX_N = 15


def opt_gap(h_cost, z_star):
    if math.isinf(z_star) or z_star <= 0:
        return float("nan")
    return (h_cost - z_star) / z_star * 100.0


def draw_routes(ax, routes, inst, title):
    nodes = inst["nodes"]; depot = nodes[0]
    for k, route in enumerate(routes):
        col  = NODE_COLS[k % len(NODE_COLS)]
        path = [depot] + [nodes[i] for i in route] + [depot]
        ax.plot([n["x"] for n in path], [n["y"] for n in path],
                color=col, lw=1.6, alpha=0.75)
        for nd in [nodes[i] for i in route]:
            ax.scatter(nd["x"], nd["y"], s=50, color=col,
                       edgecolors="white", lw=0.6, zorder=4)
            ax.annotate(str(nd["id"]), (nd["x"], nd["y"]), fontsize=6.5,
                        ha="center", va="bottom",
                        xytext=(0,4), textcoords="offset points", color="#444")
    ax.scatter(depot["x"], depot["y"], s=160, color="#E24B4A",
               marker="*", zorder=5, edgecolors="#A32D2D", lw=1)
    ax.set_title(title, fontsize=8.5, pad=5)
    ax.set_aspect("equal", adjustable="datalim")
    ax.grid(True, lw=0.3, alpha=0.4); ax.set_xticks([]); ax.set_yticks([])


def run_comparison(milp_time_limit=120):
    input_dir = os.path.join(os.path.dirname(__file__), "..", "input_data")
    all_files = sorted(f for f in os.listdir(input_dir) if f.endswith(".vrp"))
    priority  = ["instance_milp15.vrp","instance_small.vrp",
                 "instance_medium.vrp","instance_large.vrp"]
    files = [f for f in priority if f in all_files] + \
            [f for f in all_files if f not in priority]

    all_rows = []
    summary  = []

    for fname in files:
        inst = parse_vrp(os.path.join(input_dir, fname))
        name = inst["name"]; safe = name.replace(" ", "_")
        print(f"\n{'#'*65}")
        print(f"  {name}  (n={inst['n']}, Q={inst['capacity']})")
        print(f"{'#'*65}")

        # Clarke-Wright
        t0 = time.perf_counter()
        cw_routes = clarke_wright(inst)
        cw_time   = time.perf_counter() - t0
        cw_cost   = solution_cost(cw_routes, inst["dist"])
        print(f"  CW    cost={cw_cost:.2f}  t={cw_time:.4f}s")

        # Simulated Annealing
        sa = simulated_annealing(inst, T0=1000, alpha=0.995, max_iter=5000, seed=42)
        print(f"  SA    cost={sa['cost']:.2f}  t={sa['elapsed']:.3f}s")

        # Genetic Algorithm
        ga = genetic_algorithm(inst, pop_size=50, generations=300, seed=42)
        print(f"  GA    cost={ga['cost']:.2f}  t={ga['elapsed']:.3f}s")

        # MILP
        if inst["n"] <= MILP_MAX_N:
            print(f"  MILP  solving (TL={milp_time_limit}s)...")
            milp = solve_milp(inst, time_limit=milp_time_limit, verbose=False)
            print(f"  MILP  cost={milp['cost']:.2f}  status={milp['status']}"
                  f"  MIPgap={milp['gap']:.4f}%  t={milp['elapsed']:.1f}s")
        else:
            print(f"  MILP  SKIPPED — n={inst['n']} > license limit ({MILP_MAX_N})")
            milp = {"routes":[], "cost":float("inf"), "gap":float("nan"),
                    "status":"LicenseLimit", "elapsed":0}

        z_ref      = milp["cost"] if not math.isinf(milp["cost"]) \
                     else min(cw_cost, sa["cost"], ga["cost"])
        ref_label  = "MILP Z*" if not math.isinf(milp["cost"]) else "best heuristic"
        cw_gap = opt_gap(cw_cost,    z_ref)
        sa_gap = opt_gap(sa["cost"], z_ref)
        ga_gap = opt_gap(ga["cost"], z_ref)
        print(f"  Gaps vs {ref_label} ({z_ref:.2f}):  CW={cw_gap:+.2f}%  SA={sa_gap:+.2f}%  GA={ga_gap:+.2f}%")

        all_rows.append({
            "instance":       name,
            "n":              inst["n"],
            "Q":              inst["capacity"],
            "MILP_cost":      f"{milp['cost']:.4f}" if not math.isinf(milp["cost"]) else "N/A",
            "MILP_status":    milp["status"],
            "MILP_MIPgap_%":  f"{milp['gap']:.4f}" if not math.isnan(milp["gap"]) else "N/A",
            "MILP_time_s":    round(milp["elapsed"], 2),
            "CW_cost":        round(cw_cost, 4),
            "SA_cost":        round(sa["cost"], 4),
            "GA_cost":        round(ga["cost"], 4),
            "MILP_routes":    len(milp["routes"]) if milp["routes"] else "N/A",
            "CW_routes":      len(cw_routes),
            "SA_routes":      len(sa["routes"]),
            "GA_routes":      len(ga["routes"]),
            "CW_gap_%":       f"{cw_gap:+.3f}" if not math.isnan(cw_gap) else "N/A",
            "SA_gap_%":       f"{sa_gap:+.3f}" if not math.isnan(sa_gap) else "N/A",
            "GA_gap_%":       f"{ga_gap:+.3f}" if not math.isnan(ga_gap) else "N/A",
            "SA_time_s":      round(sa["elapsed"], 3),
            "GA_time_s":      round(ga["elapsed"], 3),
        })
        summary.append({
            "name": name, "n": inst["n"],
            "milp": milp["cost"], "cw": cw_cost,
            "sa": sa["cost"], "ga": ga["cost"],
            "cw_gap": cw_gap, "sa_gap": sa_gap, "ga_gap": ga_gap,
            "milp_routes": milp["routes"], "cw_routes": cw_routes,
            "sa_routes": sa["routes"], "ga_routes": ga["routes"],
            "sa_hist": sa["history"], "ga_hist": ga["history"],
            "milp_status": milp["status"], "inst": inst,
        })

        # ── Plot A: Route comparison ──────────────────────────────────────────
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        fig.patch.set_facecolor("#FFFFFF")
        fig.suptitle(f"Route Comparison — {name}  (n={inst['n']}, Q={inst['capacity']})",
                     fontsize=11, y=1.01)
        if not math.isinf(milp["cost"]) and milp["routes"]:
            panels = [
                (milp["routes"], f"MILP (Gurobi) — OPTIMAL\nZ* = {milp['cost']:.2f}"),
                (sa["routes"],   f"Simulated Annealing\nCost={sa['cost']:.2f}  Gap={sa_gap:+.2f}%"),
                (ga["routes"],   f"Genetic Algorithm\nCost={ga['cost']:.2f}  Gap={ga_gap:+.2f}%"),
            ]
        else:
            panels = [
                (cw_routes,    f"Clarke-Wright\nCost={cw_cost:.2f}"),
                (sa["routes"], f"Simulated Annealing\nCost={sa['cost']:.2f}  Gap vs CW={sa_gap:+.2f}%"),
                (ga["routes"], f"Genetic Algorithm\nCost={ga['cost']:.2f}  Gap vs CW={ga_gap:+.2f}%"),
            ]
        for ax, (routes, title) in zip(axes, panels):
            draw_routes(ax, routes, inst, title)
        plt.tight_layout()
        p = os.path.join(OUTPUT_DIR, f"{safe}_route_comparison.png")
        plt.savefig(p, dpi=150, bbox_inches="tight"); plt.close()
        print(f"  >> {p}")

        # ── Plot B: Convergence ───────────────────────────────────────────────
        fig, ax = plt.subplots(figsize=(8, 4.5))
        fig.patch.set_facecolor("#FFFFFF"); ax.set_facecolor("#F8F8F6")
        if sa["history"]:
            iters=[h[0] for h in sa["history"]]; costs=[h[1] for h in sa["history"]]
            ax.plot(iters, costs, color=COLORS["SA"], lw=2,
                    label=f"SA  (final = {sa['cost']:.1f})", zorder=3)
        if ga["history"]:
            iters=[h[0] for h in ga["history"]]; costs=[h[1] for h in ga["history"]]
            ax.plot(iters, costs, color=COLORS["GA"], lw=2,
                    label=f"GA  (final = {ga['cost']:.1f})", zorder=3)
        if not math.isinf(milp["cost"]):
            ax.axhline(milp["cost"], color=COLORS["MILP"], lw=1.8, ls="--",
                       label=f"MILP  Z* = {milp['cost']:.2f}  (proven optimal)", zorder=4)
        ax.axhline(cw_cost, color=COLORS["CW"], lw=1.2, ls=":",
                   label=f"CW = {cw_cost:.2f}", zorder=2)
        suffix = f"— MILP Z* = {milp['cost']:.2f}" if not math.isinf(milp["cost"]) \
                 else "(MILP skipped — n too large)"
        ax.set_title(f"Convergence {suffix}\n{name}", fontsize=10)
        ax.set_xlabel("Iteration / Generation"); ax.set_ylabel("Best Cost Found")
        ax.legend(fontsize=9, loc="upper right"); ax.grid(True, lw=0.4, alpha=0.5)
        plt.tight_layout()
        p = os.path.join(OUTPUT_DIR, f"{safe}_convergence_vs_milp.png")
        plt.savefig(p, dpi=150, bbox_inches="tight"); plt.close()
        print(f"  >> {p}")

    # ── Master CSV ────────────────────────────────────────────────────────────
    csv_path = os.path.join(OUTPUT_DIR, "full_comparison.csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
        w.writeheader(); w.writerows(all_rows)
    print(f"\n>> Full comparison CSV: {csv_path}")

    # ── Chart 1: Cost grouped bar ─────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(12, 5.5))
    fig.patch.set_facecolor("#FFFFFF"); ax.set_facecolor("#F8F8F6")
    names = [s["name"] for s in summary]; x = np.arange(len(names)); bw = 0.20

    for xi, s in enumerate(summary):
        mv = s["milp"]
        if not math.isinf(mv):
            b = ax.bar(xi - 1.5*bw, mv, bw, color=COLORS["MILP"], alpha=0.9,
                       label="MILP (Gurobi Optimal)" if xi == 0 else "")
            ax.text(xi - 1.5*bw, mv + 1.5, f"{mv:.1f}", ha="center",
                    va="bottom", fontsize=7, color=COLORS["MILP"])
        else:
            ax.text(xi - 1.5*bw, 8, "MILP\nN/A", ha="center", va="bottom",
                    fontsize=6, color=COLORS["MILP"])

    for xi, s in enumerate(summary):
        for offset, val, col, lbl in [
                (-0.5*bw, s["cw"], COLORS["CW"], "Clarke-Wright"),
                ( 0.5*bw, s["sa"], COLORS["SA"], "Simulated Annealing"),
                ( 1.5*bw, s["ga"], COLORS["GA"], "Genetic Algorithm")]:
            ax.bar(xi + offset, val, bw, color=col, alpha=0.88,
                   label=lbl if xi == 0 else "")
            ax.text(xi + offset, val + 1.5, f"{val:.1f}", ha="center",
                    va="bottom", fontsize=7)

    ax.set_xticks(x); ax.set_xticklabels(names, fontsize=9)
    ax.set_ylabel("Total Route Cost", fontsize=10)
    ax.set_title("MILP vs CW vs SA vs GA — Route Cost Comparison\n"
                 "(MILP shown only for n ≤ 15 due to Gurobi restricted license)", fontsize=11, pad=10)
    ax.legend(fontsize=9, loc="upper left"); ax.grid(axis="y", lw=0.4, alpha=0.5)
    plt.tight_layout()
    p = os.path.join(OUTPUT_DIR, "cost_comparison_bar.png")
    plt.savefig(p, dpi=150, bbox_inches="tight"); plt.close()
    print(f">> Cost bar chart: {p}")

    # ── Chart 2: Optimality gap ───────────────────────────────────────────────
    milp_s = [s for s in summary if not math.isinf(s["milp"])]
    if milp_s:
        fig, ax = plt.subplots(figsize=(8, 4.5))
        fig.patch.set_facecolor("#FFFFFF"); ax.set_facecolor("#F8F8F6")
        mi_names = [s["name"] for s in milp_s]; x = np.arange(len(mi_names)); bw = 0.26
        cw_g = [s["cw_gap"] for s in milp_s]
        sa_g = [s["sa_gap"] for s in milp_s]
        ga_g = [s["ga_gap"] for s in milp_s]
        ax.bar(x - bw, cw_g, bw, label="CW", color=COLORS["CW"], alpha=0.88)
        ax.bar(x,      sa_g, bw, label="SA", color=COLORS["SA"], alpha=0.88)
        ax.bar(x + bw, ga_g, bw, label="GA", color=COLORS["GA"], alpha=0.88)
        ax.axhline(0, color="#444", lw=0.8, ls="--")
        ax.set_xticks(x); ax.set_xticklabels(mi_names, fontsize=9)
        ax.set_ylabel("(Z_h − Z*) / Z* × 100 %", fontsize=9)
        ax.set_title("True Optimality Gap vs MILP Proven Optimal\n"
                     "(negative = heuristic beats CW baseline; 0% = matches MILP)", fontsize=10)
        ax.legend(fontsize=9); ax.grid(axis="y", lw=0.4, alpha=0.5)
        for i, (cg, sg, gg) in enumerate(zip(cw_g, sa_g, ga_g)):
            for off, g, col in [(-bw,cg,COLORS["CW"]),(0,sg,COLORS["SA"]),(bw,gg,COLORS["GA"])]:
                nudge = 0.3 if g >= 0 else -0.7
                ax.text(i+off, g+nudge, f"{g:+.1f}%", ha="center", fontsize=8, color=col)
        plt.tight_layout()
        p = os.path.join(OUTPUT_DIR, "optimality_gap_chart.png")
        plt.savefig(p, dpi=150, bbox_inches="tight"); plt.close()
        print(f">> Optimality gap chart: {p}")

    # ── Final summary table ───────────────────────────────────────────────────
    print(f"\n{'='*80}")
    print(f"  FINAL COMPARISON SUMMARY")
    print(f"{'='*80}")
    print(f"  {'Instance':<18} {'n':>3}  {'MILP Z*':>10}  {'CW':>9}  {'SA':>9}  {'GA':>9}  {'SA gap':>8}  {'GA gap':>8}")
    print(f"  {'-'*76}")
    for s in summary:
        m = f"{s['milp']:9.2f}" if not math.isinf(s["milp"]) else "       N/A"
        sg = f"{s['sa_gap']:+7.2f}%" if not math.isnan(s["sa_gap"]) else "      N/A"
        gg = f"{s['ga_gap']:+7.2f}%" if not math.isnan(s["ga_gap"]) else "      N/A"
        print(f"  {s['name']:<18} {s['n']:>3}  {m}  {s['cw']:>9.2f}  "
              f"{s['sa']:>9.2f}  {s['ga']:>9.2f}  {sg}  {gg}")
    print(f"{'='*80}")
    print(f"  Gaps for n<=15: vs proven MILP optimal.  Gaps for n>15: vs best heuristic.")
    return all_rows, summary


if __name__ == "__main__":
    tl = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    run_comparison(milp_time_limit=tl)
