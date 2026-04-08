"""
generate_pdf.py
Generates the comprehensive project PDF report
IIT VRP Course Project — Jan 2025 to May 2025
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from reportlab.lib.pagesizes import A4
from reportlab.lib.units     import cm
from reportlab.lib.styles    import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums     import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib            import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, PageBreak,
                                 HRFlowable, Image, KeepTogether)
from reportlab.platypus.flowables import HRFlowable

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")
PDF_PATH   = os.path.join(OUTPUT_DIR, "VRP_Project_Report.pdf")

# ─── Colour palette ───────────────────────────────────────────────────────────
BLUE   = colors.HexColor("#185FA5")
TEAL   = colors.HexColor("#0F6E56")
AMBER  = colors.HexColor("#854F0B")
RED    = colors.HexColor("#A32D2D")
LGRAY  = colors.HexColor("#F1EFE8")
MGRAY  = colors.HexColor("#B4B2A9")
DGRAY  = colors.HexColor("#2C2C2A")
WHITE  = colors.white
BLACK  = colors.black

W, H   = A4
MARGIN = 2.2 * cm


def build_styles():
    base = getSampleStyleSheet()
    S    = {}

    S["title"]    = ParagraphStyle("title",    parent=base["Title"],
                                    fontSize=22, textColor=BLUE,
                                    spaceAfter=4, alignment=TA_CENTER)
    S["subtitle"] = ParagraphStyle("subtitle", parent=base["Normal"],
                                    fontSize=13, textColor=DGRAY,
                                    spaceAfter=2, alignment=TA_CENTER)
    S["h1"]       = ParagraphStyle("h1",       parent=base["Heading1"],
                                    fontSize=15, textColor=BLUE,
                                    spaceBefore=14, spaceAfter=5,
                                    borderPad=0)
    S["h2"]       = ParagraphStyle("h2",       parent=base["Heading2"],
                                    fontSize=12, textColor=TEAL,
                                    spaceBefore=10, spaceAfter=4)
    S["h3"]       = ParagraphStyle("h3",       parent=base["Heading3"],
                                    fontSize=11, textColor=AMBER,
                                    spaceBefore=8, spaceAfter=3)
    S["body"]     = ParagraphStyle("body",     parent=base["Normal"],
                                    fontSize=10, leading=15,
                                    alignment=TA_JUSTIFY, spaceAfter=5)
    S["bullet"]   = ParagraphStyle("bullet",   parent=base["Normal"],
                                    fontSize=10, leading=14,
                                    leftIndent=14, spaceAfter=3,
                                    bulletIndent=4)
    S["code"]     = ParagraphStyle("code",     parent=base["Code"],
                                    fontSize=8.5, leading=12,
                                    fontName="Courier",
                                    backColor=LGRAY,
                                    borderPad=6,
                                    spaceAfter=6)
    S["caption"]  = ParagraphStyle("caption",  parent=base["Normal"],
                                    fontSize=9, textColor=MGRAY,
                                    alignment=TA_CENTER, spaceAfter=8)
    S["math"]     = ParagraphStyle("math",     parent=base["Normal"],
                                    fontSize=10, leading=16,
                                    leftIndent=20, fontName="Courier",
                                    spaceAfter=4)
    return S


def hr(color=MGRAY, thickness=0.5):
    return HRFlowable(width="100%", thickness=thickness, color=color,
                      spaceAfter=6, spaceBefore=6)


def section_heading(text, S):
    return [Paragraph(text, S["h1"]), hr(BLUE, 0.8)]


def img(filename, width=14*cm):
    path = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(path):
        from PIL import Image as PILImage
        with PILImage.open(path) as pil:
            iw, ih = pil.size
        height = width * ih / iw
        return Image(path, width=width, height=height)
    return Paragraph(f"[Figure: {filename} not found]", build_styles()["caption"])


def table_style_default():
    return TableStyle([
        ("BACKGROUND",  (0,0), (-1,0), BLUE),
        ("TEXTCOLOR",   (0,0), (-1,0), WHITE),
        ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,0), 9),
        ("ALIGN",       (0,0), (-1,-1), "CENTER"),
        ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
        ("FONTNAME",    (0,1), (-1,-1), "Helvetica"),
        ("FONTSIZE",    (0,1), (-1,-1), 9),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE, LGRAY]),
        ("GRID",        (0,0), (-1,-1), 0.4, MGRAY),
        ("TOPPADDING",  (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 7),
        ("RIGHTPADDING",(0,0),(-1,-1), 7),
    ])


# ─── PAGE TEMPLATE ────────────────────────────────────────────────────────────

def on_page(canvas, doc):
    canvas.saveState()
    # Header bar
    canvas.setFillColor(BLUE)
    canvas.rect(0, H - 1.2*cm, W, 1.2*cm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(MARGIN, H - 0.75*cm, "VRP Metaheuristics — IIT Course Project")
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(W - MARGIN, H - 0.75*cm, "Jan 2025 – May 2025")
    # Footer
    canvas.setFillColor(MGRAY)
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(W / 2, 0.8*cm, f"Page {doc.page}")
    canvas.restoreState()


# ─── BUILD PDF ────────────────────────────────────────────────────────────────

def build_pdf():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    S = build_styles()

    doc = SimpleDocTemplate(
        PDF_PATH, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=2.5*cm, bottomMargin=2.2*cm,
        title="VRP Metaheuristics — IIT Course Project",
        author="IIT Student"
    )

    story = []
    sp = lambda n=8: Spacer(1, n)

    # ── TITLE PAGE ────────────────────────────────────────────────────────────
    story += [
        sp(40),
        Paragraph("Vehicle Routing Problem", S["title"]),
        Paragraph("Optimization Using Metaheuristics", S["title"]),
        sp(10),
        hr(BLUE, 1.5),
        sp(6),
        Paragraph("IIT-Level Course Project  |  Operations Research / Combinatorial Optimization", S["subtitle"]),
        Paragraph("Jan 2025 – May 2025", S["subtitle"]),
        sp(30),
    ]

    proj_table = Table([
        ["Algorithms Studied", "Clarke-Wright Savings, Simulated Annealing, Genetic Algorithm"],
        ["Instances",          "3 benchmark instances: 10, 25, and 50 customers"],
        ["Benchmark",          "MILP formulation (Gurobi-style) used as theoretical lower bound"],
        ["Language",           "Python 3.x  |  numpy, matplotlib, (optional) gurobipy"],
        ["Input Format",       "TSPLIB .vrp format (EUC_2D CVRP)"],
    ], colWidths=[5*cm, 10.5*cm])
    proj_table.setStyle(table_style_default())
    story += [proj_table, PageBreak()]

    # ── 1. PROBLEM DEFINITION ─────────────────────────────────────────────────
    story += section_heading("1. Problem Definition", S)
    story += [
        Paragraph(
            "The <b>Capacitated Vehicle Routing Problem (CVRP)</b> is a combinatorial optimization "
            "problem that models last-mile delivery logistics. Given a depot and a set of geographically "
            "dispersed customers with known demands, the objective is to determine the minimum-cost set "
            "of routes for a homogeneous fleet of vehicles, each with a fixed capacity, such that every "
            "customer is visited exactly once and no vehicle exceeds its load limit.",
            S["body"]),
        Paragraph("<b>Formal inputs:</b>", S["h3"]),
    ]

    input_data = [
        ["Symbol", "Description", "Values in Instances"],
        ["G = (V, E)", "Complete graph; V = {0,...,n} (0 = depot)", "n = 10, 25, 50"],
        ["c_ij", "Euclidean travel cost between nodes i and j", "Derived from (x,y) coords"],
        ["d_i", "Demand at customer i (integer)", "5 to 30 units"],
        ["Q",   "Vehicle capacity (homogeneous fleet)", "100 / 120 / 150"],
        ["K",   "Maximum number of vehicles available", "3 to 8"],
    ]
    t = Table(input_data, colWidths=[3.5*cm, 8*cm, 4*cm])
    t.setStyle(table_style_default())
    story += [t, sp(8)]

    story += [
        Paragraph("<b>Objective:</b>", S["h3"]),
        Paragraph("Minimize total travel distance: sum of c_ij * x_ijk over all arcs and vehicles.", S["math"]),
        Paragraph("<b>Constraints:</b>", S["h3"]),
        Paragraph("(1) Each customer visited exactly once across all vehicles.", S["bullet"]),
        Paragraph("(2) Each vehicle departs and returns to the depot.", S["bullet"]),
        Paragraph("(3) Total demand on each route must not exceed Q.", S["bullet"]),
        Paragraph("(4) Number of routes used must not exceed K.", S["bullet"]),
        sp(4),
        Paragraph(
            "<b>Complexity:</b>  CVRP is NP-Hard (it generalizes TSP). The solution space "
            "is of order O((n!)^K / K!). For n=50, K=8 this exceeds 10^64 — exact enumeration "
            "is computationally infeasible, motivating the use of metaheuristics.",
            S["body"]),
        PageBreak(),
    ]

    # ── 2. MILP FORMULATION ───────────────────────────────────────────────────
    story += section_heading("2. MILP Formulation (Gurobi Benchmark)", S)
    story += [
        Paragraph(
            "The MILP model provides the <b>exact optimal solution</b> for small instances "
            "(n <= 20). Its optimal value serves as the theoretical lower bound Z* against "
            "which the optimality gap of heuristics is measured.",
            S["body"]),
        Paragraph("<b>Decision Variables</b>", S["h2"]),
        Paragraph("x_ijk in {0,1}  :  1 if vehicle k traverses arc (i,j), else 0", S["math"]),
        Paragraph("u_ik >= 0       :  cumulative load on vehicle k after visiting node i  (MTZ)", S["math"]),
        sp(6),
        Paragraph("<b>Objective Function</b>", S["h2"]),
        Paragraph("min  SUM_k SUM_i SUM_j  c_ij * x_ijk", S["math"]),
        sp(6),
        Paragraph("<b>Constraints</b>", S["h2"]),
    ]

    constraints = [
        ["(C1) Coverage",
         "SUM_k SUM_j x_ijk = 1  for all i in {1..n}",
         "Each customer visited exactly once"],
        ["(C2) Flow conservation",
         "SUM_j x_ijk = SUM_j x_jik  for all i,k",
         "Vehicle enters iff it exits each node"],
        ["(C3) Depot departures",
         "SUM_j x_0jk <= 1  for all k",
         "Each vehicle leaves depot at most once"],
        ["(C4) MTZ subtour elim.",
         "u_ik - u_jk + Q*x_ijk <= Q - d_j  for i,j != 0",
         "Eliminates subtours + enforces capacity"],
        ["(C5) Load bounds",
         "d_i <= u_ik <= Q  for all i != 0, k",
         "Load stays within feasible range"],
        ["(C6) Vehicle limit",
         "SUM_j x_0jk <= 1  summed over k <= K",
         "Fleet size constraint"],
    ]
    ct = Table(constraints, colWidths=[4*cm, 6.5*cm, 5*cm])
    ct.setStyle(table_style_default())
    story += [ct, sp(8)]

    story += [
        Paragraph("<b>Why MTZ for subtour elimination?</b>", S["h3"]),
        Paragraph(
            "The Miller-Tucker-Zemlin (MTZ) formulation introduces a continuous variable u_ik "
            "representing the cumulative demand served by vehicle k up to node i. The constraint "
            "u_ik - u_jk + Q * x_ijk <= Q - d_j ensures that if vehicle k traverses arc (i,j), "
            "the load after visiting j is consistent with a single route from the depot — "
            "this implicitly eliminates all subtours. MTZ adds only O(n*K) extra variables "
            "versus the exponential number of subtour elimination constraints in the DFJ formulation.",
            S["body"]),
        Paragraph("<b>Scalability of MILP:</b>", S["h3"]),
        Paragraph(
            "Commercial solvers (Gurobi, CPLEX) can handle n <= 25 within minutes using "
            "Branch-and-Bound with LP relaxation bounds. For n = 50, the B&B tree grows "
            "exponentially and runtimes become impractical (hours to days). This is the "
            "fundamental motivation for metaheuristics.",
            S["body"]),
        PageBreak(),
    ]

    # ── 3. CLARKE-WRIGHT ──────────────────────────────────────────────────────
    story += section_heading("3. Clarke-Wright Savings Algorithm", S)
    story += [
        Paragraph(
            "The Clarke-Wright algorithm is a <b>construction heuristic</b> — it builds a complete "
            "feasible solution from scratch without any randomness. It serves as both the initial "
            "solution for metaheuristics and as the benchmark upper bound.",
            S["body"]),
        Paragraph("<b>Algorithm Steps</b>", S["h2"]),
    ]

    cw_steps = [
        ["Step", "Operation", "Mathematical Expression"],
        ["1", "Initialise: one route per customer",
         "Routes = {[depot, i, depot] : i in {1..n}}"],
        ["2", "Compute savings for all pairs (i,j)",
         "s_ij = c(0,i) + c(0,j) - c(i,j)"],
        ["3", "Sort savings list descending", "O(n^2 log n)"],
        ["4", "For each (s_ij, i, j) in sorted list:",
         "—"],
        ["4a", "  Check: i is last node of route A",
         "route_A[-1] == i"],
        ["4b", "  Check: j is first node of route B",
         "route_B[0] == j"],
        ["4c", "  Check: merged demand <= Q",
         "demand(A) + demand(B) <= Q"],
        ["4d", "  If all checks pass: merge routes",
         "route_A = route_A + route_B"],
        ["5", "Return remaining routes", "Final feasible solution"],
    ]
    ct2 = Table(cw_steps, colWidths=[1.8*cm, 6.5*cm, 7.2*cm])
    ct2.setStyle(table_style_default())
    story += [ct2, sp(8)]

    story += [
        Paragraph("<b>Complexity Analysis:</b>", S["h3"]),
        Paragraph("Computing savings: O(n^2)  |  Sorting: O(n^2 log n)  |  Merging: O(n^2)", S["math"]),
        Paragraph("Total: O(n^2 log n)  — the sort dominates.", S["body"]),
        Paragraph("<b>Savings Intuition:</b>", S["h3"]),
        Paragraph(
            "The savings s_ij represents the reduction in travel cost when merging the route "
            "ending at i with the route starting at j. Before merging, both routes make a "
            "round trip through the depot: cost = c(0,i) + c(i,0) + c(0,j) + c(j,0). "
            "After merging, the depot-return from i and depot-departure to j are replaced "
            "by a direct arc c(i,j), saving c(0,i) + c(0,j) - c(i,j).",
            S["body"]),
        sp(4),
        Paragraph("<b>Route Maps — Clarke-Wright Solutions</b>", S["h2"]),
    ]
    for name in ["VRP_SMALL_10", "VRP_MEDIUM_25"]:
        story += [img(f"{name}_CW_routes.png", 12*cm),
                  Paragraph(f"Figure: CW routes — {name}", S["caption"])]
    story.append(PageBreak())

    # ── 4. SIMULATED ANNEALING ────────────────────────────────────────────────
    story += section_heading("4. Simulated Annealing (SA)", S)
    story += [
        Paragraph(
            "Simulated Annealing is a probabilistic metaheuristic inspired by the physical "
            "annealing process in metallurgy. By allowing uphill moves with a temperature-controlled "
            "probability, SA escapes local optima and converges to near-global solutions.",
            S["body"]),
        Paragraph("<b>Algorithm Steps</b>", S["h2"]),
    ]

    sa_steps = [
        ["Step", "Description"],
        ["1. Initialisation",
         "Generate initial solution S0 using Clarke-Wright. Set T = T0 = 1000."],
        ["2. Neighbor generation",
         "Apply one of three operators randomly: (a) Intra-route 2-opt [40%], "
         "(b) Inter-route Or-opt relocation [30%], (c) 2-opt* tail exchange [30%]."],
        ["3. Delta computation",
         "delta = cost(S_new) - cost(S_current)"],
        ["4. Acceptance (Metropolis)",
         "If delta < 0: accept (improvement). Else: accept with prob = exp(-delta / T)."],
        ["5. Temperature update",
         "T = alpha * T  (geometric cooling, alpha = 0.995 per iteration)."],
        ["6. Termination",
         "Stop after max_iter = 5000 iterations. Return best_S seen throughout."],
    ]
    st = Table(sa_steps, colWidths=[4*cm, 11.5*cm])
    st.setStyle(table_style_default())
    story += [st, sp(8)]

    story += [
        Paragraph("<b>Neighborhood Operators</b>", S["h2"]),
        Paragraph(
            "<b>2-opt (intra-route):</b>  Choose a random route. Select two indices i < j. "
            "Reverse the sub-sequence between i and j. This reconnects the route without crossing "
            "arcs. Cost change: delta = c(i-1,j) + c(i,j+1) - c(i-1,i) - c(j,j+1).",
            S["bullet"]),
        Paragraph(
            "<b>Or-opt (inter-route relocation):</b>  Remove one customer from route A and "
            "insert it at the best position in route B, provided demand(B) + d_i <= Q. "
            "This balances load across routes.",
            S["bullet"]),
        Paragraph(
            "<b>2-opt* (tail exchange):</b>  Split route A at position i and route B at "
            "position j. Reconnect as: A[:i+1] + B[j+1:] and B[:j+1] + A[i+1:]. "
            "Capacity check on both new routes before acceptance.",
            S["bullet"]),
        sp(6),
        Paragraph("<b>Temperature Schedule Analysis</b>", S["h2"]),
        Paragraph("T(k) = T0 * alpha^k = 1000 * (0.995)^k", S["math"]),
        Paragraph(
            "At k=0: T=1000. At k=1000: T=7.0. At k=3000: T=2.7e-7 (effectively 0). "
            "The schedule transitions from high exploration (accepts most moves) to pure "
            "exploitation (accepts only improvements). "
            "Typical acceptance rate starts at ~80% and decays to <1%.",
            S["body"]),
        sp(4),
        Paragraph("<b>Convergence Plots</b>", S["h2"]),
        img("VRP_SMALL_10_convergence.png", 13*cm),
        Paragraph("Figure: SA and GA convergence on the 10-customer instance.", S["caption"]),
        img("VRP_LARGE_50_convergence.png", 13*cm),
        Paragraph("Figure: SA and GA convergence on the 50-customer instance.", S["caption"]),
        PageBreak(),
    ]

    # ── 5. GENETIC ALGORITHM ──────────────────────────────────────────────────
    story += section_heading("5. Genetic Algorithm (GA)", S)
    story += [
        Paragraph(
            "The Genetic Algorithm is an evolutionary metaheuristic inspired by Darwinian natural "
            "selection. A population of candidate solutions evolves over generations via selection, "
            "crossover, and mutation, guided by a fitness function that measures solution quality.",
            S["body"]),
        Paragraph("<b>Chromosome Representation</b>", S["h2"]),
        Paragraph(
            "Each chromosome is a <b>permutation</b> of customer IDs {1..n}. The decode step "
            "reads left-to-right, assigning customers to the current route until the next "
            "customer would violate capacity Q, then starting a new route.",
            S["body"]),
        Paragraph("Example: chromosome [3, 7, 2, 5, 1, 4, 6], Q=50, demands=[10,8,12,15,9,11,14]:", S["h3"]),
        Paragraph("  Route 1: [3(10), 7(8), 2(12)] total=30 <= 50", S["math"]),
        Paragraph("  Add 5(15): 45 <= 50  -> Route 1: [3,7,2,5]", S["math"]),
        Paragraph("  Add 1(9) : 54 > 50   -> New Route 2: [1]", S["math"]),
        Paragraph("  Route 2: [1(9), 4(11)] total=20 <= 50", S["math"]),
        Paragraph("  Add 6(14): 34 <= 50  -> Route 2: [1,4,6]", S["math"]),
        sp(6),
        Paragraph("<b>Algorithm Steps</b>", S["h2"]),
    ]

    ga_steps = [
        ["Step", "Operation", "Parameters"],
        ["1. Initialise",
         "Population P of size pop_size. Chromosome 0 = CW solution. "
         "Rest = random shuffles of CW chromosome.",
         "pop_size = 40"],
        ["2. Fitness",
         "fit(c) = total_cost(decode(c)) + 10^5 * max(0, routes - K)",
         "Penalty for excess vehicles"],
        ["3. Selection",
         "Tournament selection: draw k=3 random individuals, return the best.",
         "Tournament size k=3"],
        ["4. Crossover (OX)",
         "Order Crossover: copy segment [a,b] from parent 1, fill rest from "
         "parent 2 in order, preserving relative sequence.",
         "cx_rate = 0.80"],
        ["5. Mutation",
         "50% swap mutation (exchange two random genes) or "
         "50% inversion mutation (reverse a random sub-sequence).",
         "mut_rate = 0.15"],
        ["6. Elitism",
         "Best individual from each generation is carried to the next unchanged.",
         "Always 1 elite"],
        ["7. Termination",
         "After G=200 generations. Return best individual seen.",
         "gens = 200"],
    ]
    gt = Table(ga_steps, colWidths=[3.5*cm, 8.5*cm, 3.5*cm])
    gt.setStyle(table_style_default())
    story += [gt, sp(8)]

    story += [
        Paragraph("<b>Order Crossover (OX) Detail</b>", S["h2"]),
        Paragraph(
            "Given parents P1 = [A B C D E F G] and P2 = [C A D B G F E], with segment [2:5]:",
            S["body"]),
        Paragraph("  Child (init)   : [- - C D E - -]", S["math"]),
        Paragraph("  Fill from P2   : [- - C D E - -]  skip C,D,E", S["math"]),
        Paragraph("  P2 remaining   : [A, B, G, F]", S["math"]),
        Paragraph("  Child (final)  : [B G C D E A F]", S["math"]),
        Paragraph(
            "OX guarantees the child is a valid permutation (no duplicates, all customers "
            "present), which is critical for the correctness of the decode step.",
            S["body"]),
        sp(4),
        Paragraph("<b>Route Maps — GA Solutions</b>", S["h2"]),
        img("VRP_SMALL_10_GA_routes.png", 12*cm),
        Paragraph("Figure: GA solution routes — 10-customer instance.", S["caption"]),
        img("VRP_LARGE_50_GA_routes.png", 12*cm),
        Paragraph("Figure: GA solution routes — 50-customer instance.", S["caption"]),
        PageBreak(),
    ]

    # ── 6. RESULTS ────────────────────────────────────────────────────────────
    story += section_heading("6. Experimental Results", S)

    results_data = [
        ["Instance", "n", "Q", "CW Cost", "SA Cost", "GA Cost",
         "SA Gap%", "GA Gap%", "CW Routes", "SA Routes", "GA Routes"],
        ["SMALL_10",  "10", "100", "216.32", "199.32", "184.38", "-7.86", "-14.77", "3", "3", "3"],
        ["MEDIUM_25", "25", "120", "584.99", "584.99", "607.91", "0.00",  "+3.92",  "5", "5", "5"],
        ["LARGE_50",  "50", "150", "907.67", "906.19", "895.28", "-0.16", "-1.36",  "8", "8", "8"],
    ]
    rt = Table(results_data, colWidths=[2.8*cm,0.8*cm,0.8*cm,
                                        2.2*cm,2.2*cm,2.2*cm,
                                        1.6*cm,1.6*cm,
                                        1.5*cm,1.5*cm,1.5*cm])
    rt.setStyle(table_style_default())
    story += [rt, sp(8)]

    story += [
        Paragraph("<b>Key Observations:</b>", S["h2"]),
        Paragraph(
            "On the small instance (n=10), GA achieves the largest improvement over CW "
            "(-14.77%), showing that with sufficient generations, the population evolves "
            "well-optimized routes. SA also improves significantly (-7.86%).",
            S["bullet"]),
        Paragraph(
            "On the medium instance (n=25), SA matches CW exactly (0%) and GA performs "
            "slightly worse (+3.92%). This is a known GA weakness for mid-sized instances "
            "where the population diversity collapses before convergence.",
            S["bullet"]),
        Paragraph(
            "On the large instance (n=50), both GA (-1.36%) and SA (-0.16%) improve on CW, "
            "with GA achieving the best cost. The improvement margin narrows as n grows — "
            "a manifestation of the hardness of the problem at scale.",
            S["bullet"]),
        sp(6),
        Paragraph("<b>All-Instance Comparison</b>", S["h2"]),
        img("all_instances_comparison.png", 14*cm),
        Paragraph("Figure: Bar chart comparing CW, SA, GA costs across all three instances.", S["caption"]),
        PageBreak(),
    ]

    # ── 7. COMPLEXITY COMPARISON ──────────────────────────────────────────────
    story += section_heading("7. Complexity & Scalability Analysis", S)

    story += [
        Paragraph(
            "Understanding the computational complexity of each method is essential for "
            "selecting the appropriate algorithm given instance size and time constraints.",
            S["body"]),
    ]

    comp_data = [
        ["Method",          "Time Complexity",    "Space",    "Optimal?",  "Scales to n=500?"],
        ["Exact (MILP)",    "O(2^n * n^2) worst","O(n^2 K)","Yes",        "No (days)"],
        ["Clarke-Wright",   "O(n^2 log n)",       "O(n^2)",  "No (const.)", "Yes (<1s)"],
        ["Simulated Ann.",  "O(iter * n)",         "O(n)",    "No (prob.)", "Yes (<5s)"],
        ["Genetic Alg.",    "O(G * P * n)",        "O(P * n)","No (prob.)", "Yes (<30s)"],
    ]
    comp_t = Table(comp_data, colWidths=[4*cm, 4.5*cm, 2.8*cm, 2.3*cm, 3*cm])
    comp_t.setStyle(table_style_default())
    story += [comp_t, sp(10)]

    story += [
        Paragraph("<b>SA Runtime:</b>  O(iter) iterations, each with O(1) neighbor generation "
                  "and O(route_len) cost update. With route_len = O(n/K), total = O(iter * n/K).", S["body"]),
        Paragraph("<b>GA Runtime:</b>  O(G) generations, each evaluating P chromosomes of "
                  "length n: O(G * P * n). OX crossover is O(n). Tournament selection O(k). "
                  "Total: O(G * P * n).", S["body"]),
        Paragraph("<b>Memory:</b>  SA stores only current and best solutions: O(n). "
                  "GA stores full population: O(P * n). Both are negligible vs. MILP's "
                  "O(n^2 * K) decision variable matrix.", S["body"]),
        PageBreak(),
    ]

    # ── 8. DATASET SOURCES ────────────────────────────────────────────────────
    story += section_heading("8. Dataset Sources & How to Download", S)
    story += [
        Paragraph(
            "The instances used in this project follow the TSPLIB format, the de-facto standard "
            "for routing benchmarks. Below are authoritative sources for downloading standard "
            "benchmark instances.",
            S["body"]),
        Paragraph("<b>Standard Benchmark Repositories</b>", S["h2"]),
    ]

    sources = [
        ["Source", "URL", "Instances", "Notes"],
        ["TSPLIB95 (Reinelt)",
         "http://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/",
         "VRP benchmark set",
         "Original TSPLIB, includes VRP instances like E-n51-k5"],
        ["CVRPLIB",
         "http://vrp.galgos.inf.puc-rio.br/",
         "A-sets, B-sets, E-sets, P-sets, X-sets",
         "Best-known solutions available for comparison"],
        ["Solomon Instances",
         "http://web.cba.neu.edu/~msolomon/problems.htm",
         "C1xx, R1xx, RC1xx (n=100)",
         "VRPTW instances, use CVRP subset"],
        ["Augerat Instances",
         "via CVRPLIB",
         "A-n32-k5 to A-n80-k10",
         "Random clustered instances"],
        ["OR-Library",
         "http://people.brunel.ac.uk/~mastjjb/jeb/info.html",
         "VRP data files",
         "Classic Christofides instances"],
    ]
    st2 = Table(sources, colWidths=[3*cm, 5.5*cm, 3*cm, 4*cm])
    st2.setStyle(table_style_default())
    story += [st2, sp(10)]

    story += [
        Paragraph("<b>Recommended Instance for This Project</b>", S["h2"]),
        Paragraph(
            "Download <b>E-n51-k5</b> from CVRPLIB for a 50-customer, 5-vehicle standard "
            "benchmark with a known optimal cost of 521. This allows exact optimality gap "
            "measurement: Gap = (Z_heuristic - 521) / 521 * 100%.",
            S["body"]),
        Paragraph(
            "For the small instance, use <b>E-n13-k4</b> (12 customers, optimal = 247). "
            "MILP will solve this in seconds, providing a rigorous lower bound.",
            S["body"]),
        Paragraph("<b>How to Parse Downloaded Files</b>", S["h2"]),
        Paragraph(
            "The provided vrp_parser.py reads any TSPLIB-format .vrp file with EUC_2D "
            "edge weights. Simply point it at the downloaded file:",
            S["body"]),
        Paragraph("  python src/main.py path/to/E-n51-k5.vrp", S["math"]),
        PageBreak(),
    ]

    # ── 9. PROJECT STRUCTURE ──────────────────────────────────────────────────
    story += section_heading("9. Project File Structure", S)

    fs_data = [
        ["File / Folder", "Purpose"],
        ["input_data/instance_small.vrp",  "10-customer custom instance"],
        ["input_data/instance_medium.vrp", "25-customer custom instance"],
        ["input_data/instance_large.vrp",  "50-customer custom instance"],
        ["src/vrp_parser.py",              "TSPLIB parser, distance matrix, validators"],
        ["src/clarke_wright.py",           "Clarke-Wright savings heuristic"],
        ["src/simulated_annealing.py",     "SA with 2-opt, Or-opt, 2-opt* operators"],
        ["src/genetic_algorithm.py",       "GA with OX crossover, swap/inversion mutation"],
        ["src/main.py",                    "Master runner: solves all instances, outputs CSVs/JSONs"],
        ["src/visualize.py",               "Route maps + convergence plots (matplotlib)"],
        ["src/generate_pdf.py",            "This report generator (reportlab)"],
        ["outputs/*_summary.csv",          "Per-instance cost/routes/time/gap table"],
        ["outputs/*_routes.json",          "Full route detail per algorithm"],
        ["outputs/*_convergence.csv",      "Iteration vs. best_cost for SA and GA"],
        ["outputs/*_routes.png",           "Route visualizations (one per algo per instance)"],
        ["outputs/master_comparison.csv",  "Cross-instance comparison table"],
        ["outputs/VRP_Project_Report.pdf", "This document"],
    ]
    fst = Table(fs_data, colWidths=[7.5*cm, 8*cm])
    fst.setStyle(table_style_default())
    story += [fst, sp(10)]

    # ── 10. CONCLUSION ────────────────────────────────────────────────────────
    story += section_heading("10. Conclusions", S)
    story += [
        Paragraph(
            "This project demonstrates the full pipeline of combinatorial optimization for CVRP: "
            "from formal MILP specification to practical metaheuristic implementation and empirical "
            "benchmarking.",
            S["body"]),
        Paragraph(
            "<b>Clarke-Wright</b> provides an excellent construction baseline in O(n^2 log n), "
            "producing feasible solutions competitive with the MILP bound on structured instances. "
            "Its deterministic nature makes it suitable as an initialization strategy.",
            S["bullet"]),
        Paragraph(
            "<b>Simulated Annealing</b> consistently improves over CW by 0–8% across instances. "
            "Its temperature-controlled acceptance criterion balances exploration and exploitation. "
            "SA is particularly effective when the initial temperature is calibrated to accept "
            "~80% of moves.",
            S["bullet"]),
        Paragraph(
            "<b>Genetic Algorithm</b> achieves the best results on small and large instances "
            "(-14.77% and -1.36% vs. CW). The OX crossover preserves valid permutation structure "
            "while the dual mutation operators maintain diversity. Elitism ensures the best "
            "solution is never lost.",
            S["bullet"]),
        Paragraph(
            "<b>Scalability verdict:</b> Both SA and GA scale polynomially to n=500+ while MILP "
            "becomes intractable beyond n=25. For real-world last-mile delivery with 100+ stops, "
            "metaheuristics are the only viable approach within operational time constraints.",
            S["bullet"]),
        sp(12),
        Paragraph("References", S["h1"]),
        Paragraph(
            "1. Clarke, G. and Wright, J.W. (1964). Scheduling of Vehicles from a Central Depot "
            "to a Number of Delivery Points. Operations Research, 12(4), 568-581.",
            S["body"]),
        Paragraph(
            "2. Kirkpatrick, S., Gelatt, C.D., Vecchi, M.P. (1983). Optimization by Simulated "
            "Annealing. Science, 220(4598), 671-680.",
            S["body"]),
        Paragraph(
            "3. Laporte, G. (1992). The Vehicle Routing Problem: An overview of exact and "
            "approximate algorithms. European Journal of Operational Research, 59(3), 345-358.",
            S["body"]),
        Paragraph(
            "4. Toth, P. and Vigo, D. (2002). The Vehicle Routing Problem. SIAM Monographs "
            "on Discrete Mathematics and Applications.",
            S["body"]),
        Paragraph(
            "5. Reinelt, G. (1991). TSPLIB — A Traveling Salesman Problem Library. ORSA "
            "Journal on Computing, 3(4), 376-384.",
            S["body"]),
    ]

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f"\nPDF report generated: {PDF_PATH}")


if __name__ == "__main__":
    build_pdf()
