"""Phase 4 - performance testing and runtime charts."""
import time
import random

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .datagen import generate_graph_edges, generate_parcels
from .graph import build_graph, dijkstra, nearest_neighbor_tsp, two_opt
from .knapsack import knapsack_dp
from .planner import plan
from .sorting import merge_sort, insertion_sort, bubble_sort


def _time(fn, repeat=3):
    best = float("inf")
    for _ in range(repeat):
        s = time.perf_counter()
        fn()
        best = min(best, time.perf_counter() - s)
    return best


def bench_sorting(sizes):
    rows = []
    for n in sizes:
        parcels = generate_parcels(n, 50, seed=1)
        row = {"n": n, "merge": _time(lambda: merge_sort(parcels))}
        row["insertion"] = _time(lambda: insertion_sort(parcels)) if n <= 3000 else None
        row["bubble"] = _time(lambda: bubble_sort(parcels), 1) if n <= 2000 else None
        rows.append(row)
    return rows


def bench_knapsack(sizes, capacity=100):
    return [{"n": n, "time": _time(lambda: knapsack_dp(generate_parcels(n, 50, 2), capacity), 2)}
            for n in sizes]


def bench_graph(sizes):
    rows = []
    for v in sizes:
        edges = generate_graph_edges(v, seed=3)
        g = build_graph(edges)
        stops = random.Random(5).sample(range(1, v), min(20, v - 1))
        rows.append({"v": v, "e": len(edges),
                     "dijkstra": _time(lambda: dijkstra(g, 0)),
                     "tsp": _time(lambda: nearest_neighbor_tsp(g, 0, stops), 2)})
    return rows


def bench_pipeline(configs, capacity=100):
    """configs: (num_parcels, num_nodes). Returns per-step timings."""
    rows = []
    for n, v in configs:
        parcels = generate_parcels(n, v, seed=7)
        edges = generate_graph_edges(v, seed=7)
        best = None
        for _ in range(3):
            r = plan(parcels, edges, 0, capacity)
            if best is None or sum(r["timings"].values()) < sum(best["timings"].values()):
                best = r
        rows.append({"n": n, "v": v, **best["timings"], "tour_km": best["total_km"],
                     "stops": len(best["stops"])})
    return rows


def bench_two_opt(v=60, n=40, capacity=100):
    parcels = generate_parcels(n, v, seed=11)
    edges = generate_graph_edges(v, seed=11)
    r = plan(parcels, edges, 0, capacity)
    improved, imp_len = two_opt(r["graph"], r["order"])
    return r["total_km"], imp_len, len(r["stops"])


def make_charts(out_dir):
    out = {}
    sort_rows = bench_sorting([100, 250, 500, 1000, 2000, 3000, 5000, 10000])
    knap_rows = bench_knapsack([50, 100, 200, 400, 800])
    graph_rows = bench_graph([50, 100, 200, 400, 800])
    pipe_rows = bench_pipeline([(10, 15), (50, 40), (200, 100), (1000, 300)])
    out.update(sort=sort_rows, knap=knap_rows, graph=graph_rows, pipe=pipe_rows)

    fig, ax = plt.subplots(2, 2, figsize=(12, 9))

    a = ax[0][0]
    a.plot([r["n"] for r in sort_rows], [r["merge"] for r in sort_rows], "o-", label="Merge sort")
    pts = [r for r in sort_rows if r["insertion"] is not None]
    a.plot([r["n"] for r in pts], [r["insertion"] for r in pts], "s-", label="Insertion sort")
    pts = [r for r in sort_rows if r["bubble"] is not None]
    a.plot([r["n"] for r in pts], [r["bubble"] for r in pts], "^-", label="Bubble sort")
    a.set(title="Sorting: runtime vs parcels", xlabel="Number of parcels (n)", ylabel="Seconds")
    a.legend(); a.grid(alpha=.3)

    a = ax[0][1]
    a.plot([r["n"] for r in knap_rows], [r["time"] for r in knap_rows], "o-", color="tab:green")
    a.set(title="0/1 Knapsack DP (capacity 100): runtime vs n", xlabel="Number of parcels (n)", ylabel="Seconds")
    a.grid(alpha=.3)

    a = ax[1][0]
    a.plot([r["v"] for r in graph_rows], [r["dijkstra"] for r in graph_rows], "o-", label="Dijkstra (1 source)")
    a.plot([r["v"] for r in graph_rows], [r["tsp"] for r in graph_rows], "s-", label="Nearest-neighbour TSP (20 stops)")
    a.set(title="Graph algorithms: runtime vs nodes", xlabel="Number of nodes (V)", ylabel="Seconds")
    a.legend(); a.grid(alpha=.3)

    a = ax[1][1]
    labels = [f"{r['n']}p/{r['v']}n" for r in pipe_rows]
    bottom = [0] * len(pipe_rows)
    for step, col in [("sorting", "tab:blue"), ("knapsack", "tab:green"),
                      ("graph_build", "tab:orange"), ("routing", "tab:red")]:
        vals = [r[step] for r in pipe_rows]
        a.bar(labels, vals, bottom=bottom, label=step, color=col)
        bottom = [b + v for b, v in zip(bottom, vals)]
    a.set(title="Full pipeline: time per step", xlabel="parcels / nodes", ylabel="Seconds")
    a.legend(); a.grid(alpha=.3, axis="y")

    fig.tight_layout()
    fig.savefig(f"{out_dir}/runtime_charts.png", dpi=130)
    plt.close(fig)
    return out
