# VRP Hybrid Optimization (MILP, GA, SA)

A Python project for solving the Capacitated Vehicle Routing Problem (CVRP) using:
- Clarke-Wright Savings (CW)
- Simulated Annealing (SA)
- Genetic Algorithm (GA)
- MILP benchmark (small instances, via Gurobi)

The project compares solution quality, route cost, convergence behavior, and runtime across multiple `.vrp` instances.

## Repository
- GitHub: https://github.com/Tirupathi007/VRP-hybrid-optimization-milp-GA-SA

## Project Structure

```text
VRP_Project/
  input_data/
    *.vrp
  outputs/
    *.csv, *.json, *.png, *.pdf
  src/
    main.py
    compare_all.py
    milp_solver.py
    clarke_wright.py
    simulated_annealing.py
    genetic_algorithm.py
    visualize.py
    generate_pdf.py
    vrp_parser.py
```

## Requirements
- Python 3.9+
- Recommended packages:
  - numpy
  - matplotlib
  - reportlab
  - pillow
- Optional (for exact MILP benchmark):
  - gurobipy with a valid Gurobi license

## Install

```bash
pip install numpy matplotlib reportlab pillow
```

If you want MILP runs:

```bash
pip install gurobipy
```

## How to Run

From the project root (`VRP_Project`):

1) Run all `.vrp` instances:

```bash
python src/main.py
```

2) Run one instance:

```bash
python src/main.py input_data/instance_small.vrp
```

3) Full comparison including MILP (when feasible):

```bash
python src/compare_all.py
```

4) Generate final PDF report:

```bash
python src/generate_pdf.py
```

## Outputs
Generated files are saved in `outputs/`, including:
- Per-instance summary CSVs
- Route JSONs
- SA/GA convergence CSVs
- Comparison charts (`.png`)
- Consolidated comparison CSV files
- Final report PDF

## Notes
- MILP is typically run only for smaller instances due to restricted-license variable limits.
- For larger instances, heuristic methods (CW/SA/GA) are used for scalable solutions.

## Author
Tirupathi Rao
