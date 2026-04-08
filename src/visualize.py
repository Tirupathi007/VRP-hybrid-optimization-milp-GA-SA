"""
visualize.py
Generate route maps and convergence plots for VRP solutions
IIT Course Project

Outputs PNG files to outputs/ directory.
"""

import os
import sys
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

sys.path.insert(0, os.path.dirname(__file__))
from vrp_parser       import parse_vrp, route_demand
from clarke_wright    import clarke_wright
from simulated_annealing import simulated_annealing
from genetic_algorithm   import genetic_algorithm

COLORS = ["#378ADD","#1D9E75","#D85A30","#D4537E",
          "#7F77DD","#BA7517","#639922","#E24B4A",
          "#0F6E56","#993C1D"]
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def plot_routes(routes, inst, title, filename):
    nodes = inst["nodes"]
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.set_facecolor("#F8F8F6")
    fig.patch.set_facecolor("#FFFFFF")

    depot = nodes[0]

    for k, route in enumerate(routes):
        col = COLORS[k % len(COLORS)]
        path = [depot] + [nodes[i] for i in route] + [depot]
        xs = [n["x"] for n in path]
        ys = [n["y"] for n in path]
        ax.plot(xs, ys, color=col, linewidth=1.6, alpha=0.75,
                label=f"V{k+1} (d={route_demand(route, nodes)})")
        for node in [nodes[i] for i in route]:
            ax.scatter(node["x"], node["y"], s=60, color=col,
                       edgecolors="white", linewidths=0.8, zorder=4)
            ax.annotate(str(node["id"]), (node["x"], node["y"]),
                        fontsize=7, ha="center", va="bottom",
                        xytext=(0, 5), textcoords="offset points", color="#444")

    # Depot
    ax.scatter(depot["x"], depot["y"], s=200, color="#E24B4A",
               marker="*", zorder=5, edgecolors="#A32D2D", linewidths=1)
    ax.annotate("Depot", (depot["x"], depot["y"]),
                fontsize=8, fontweight="bold", color="#A32D2D",
                xytext=(5, 5), textcoords="offset points")

    ax.set_title(title, fontsize=11, pad=10)
    ax.set_xlabel("X coordinate"); ax.set_ylabel("Y coordinate")
    ax.legend(loc="upper right", fontsize=7, framealpha=0.8,
              ncol=2 if len(routes) > 5 else 1)
    ax.grid(True, linewidth=0.4, alpha=0.5)
    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Plot saved: {path}")


def plot_convergence(histories, labels, colors, title, filename):
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.set_facecolor("#F8F8F6")
    fig.patch.set_facecolor("#FFFFFF")

    for (history, label, color) in zip(histories, labels, colors):
        if not history:
            continue
        iters = [h[0] for h in history]
        costs = [h[1] for h in history]
        ax.plot(iters, costs, color=color, linewidth=2, label=label)
        ax.scatter(iters[-1], costs[-1], color=color, s=60, zorder=5)

    ax.set_title(title, fontsize=11, pad=10)
    ax.set_xlabel("Iteration / Generation")
    ax.set_ylabel("Best Cost")
    ax.legend(fontsize=9)
    ax.grid(True, linewidth=0.4, alpha=0.5)
    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Plot saved: {path}")


def plot_comparison_bar(inst_names, cw_costs, sa_costs, ga_costs, filename):
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.set_facecolor("#F8F8F6")
    fig.patch.set_facecolor("#FFFFFF")

    x = range(len(inst_names))
    w = 0.25
    ax.bar([i - w for i in x], cw_costs, width=w, label="Clarke-Wright",
           color="#378ADD", alpha=0.85)
    ax.bar([i     for i in x], sa_costs, width=w, label="Simulated Annealing",
           color="#BA7517", alpha=0.85)
    ax.bar([i + w for i in x], ga_costs, width=w, label="Genetic Algorithm",
           color="#1D9E75", alpha=0.85)

    ax.set_xticks(list(x))
    ax.set_xticklabels(inst_names, fontsize=9)
    ax.set_ylabel("Total Route Cost")
    ax.set_title("Algorithm Comparison Across Instances", fontsize=11, pad=10)
    ax.legend(fontsize=9)
    ax.grid(axis="y", linewidth=0.4, alpha=0.5)
    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Plot saved: {path}")


def visualize_all():
    input_dir = os.path.join(os.path.dirname(__file__), "..", "input_data")
    files = sorted(f for f in os.listdir(input_dir) if f.endswith(".vrp"))

    inst_names, cw_c, sa_c, ga_c = [], [], [], []

    for fname in files:
        fp   = os.path.join(input_dir, fname)
        inst = parse_vrp(fp)
        safe = inst["name"].replace(" ", "_")
        print(f"\n--- Visualizing: {inst['name']} ---")

        cw_routes = clarke_wright(inst)
        sa_res    = simulated_annealing(inst, T0=1000, alpha=0.995, max_iter=5000)
        ga_res    = genetic_algorithm(inst, pop_size=40, generations=200)

        from vrp_parser import solution_cost
        plot_routes(cw_routes, inst,
                    f"Clarke-Wright  |  {inst['name']}  |  Cost={solution_cost(cw_routes,inst['dist']):.2f}",
                    f"{safe}_CW_routes.png")
        plot_routes(sa_res["routes"], inst,
                    f"Simulated Annealing  |  {inst['name']}  |  Cost={sa_res['cost']:.2f}",
                    f"{safe}_SA_routes.png")
        plot_routes(ga_res["routes"], inst,
                    f"Genetic Algorithm  |  {inst['name']}  |  Cost={ga_res['cost']:.2f}",
                    f"{safe}_GA_routes.png")
        plot_convergence(
            [sa_res["history"], ga_res["history"]],
            ["SA", "GA"], ["#BA7517", "#1D9E75"],
            f"Convergence  |  {inst['name']}",
            f"{safe}_convergence.png"
        )

        inst_names.append(inst["name"])
        cw_c.append(solution_cost(cw_routes, inst["dist"]))
        sa_c.append(sa_res["cost"])
        ga_c.append(ga_res["cost"])

    if len(inst_names) > 1:
        plot_comparison_bar(inst_names, cw_c, sa_c, ga_c, "all_instances_comparison.png")


if __name__ == "__main__":
    visualize_all()
