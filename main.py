"""Mini-Courier Planner - command line entry point.

Usage:
    python main.py                      # run on data/ sample dataset (capacity 50 kg)
    python main.py --capacity 80
    python main.py --parcels data/parcels_small.csv --graph data/graph_small.json
    python main.py --benchmark          # also create outputs/runtime_charts.png
"""
import argparse
import os

from courier.datagen import (generate_graph_edges, generate_parcels, load_edges_json,
                             load_parcels_csv, save_edges_json, save_parcels_csv)
from courier.planner import plan, SPEED_KMH

HERE = os.path.dirname(os.path.abspath(__file__))


def make_sample_data():
    """Create the sample datasets (small = 10 parcels, large = 200 parcels)."""
    d = os.path.join(HERE, "data")
    os.makedirs(d, exist_ok=True)
    for name, n, v in [("small", 10, 12), ("large", 200, 100)]:
        save_parcels_csv(generate_parcels(n, v, seed=42), f"{d}/parcels_{name}.csv")
        save_edges_json(generate_graph_edges(v, seed=42), f"{d}/graph_{name}.json")


def show(result, capacity, max_rows=15):
    sp, sel = result["sorted_parcels"], result["selected"]
    print("=" * 72)
    print("PHASE 2a - PARCELS SORTED BY DEADLINE (then priority)  [merge sort]")
    print("=" * 72)
    print(f"{'#':>3} {'ID':<6}{'Wt(kg)':>7}{'Prio':>6}{'Deadline(h)':>13}{'Dest':>6}")
    for i, p in enumerate(sp[:max_rows], 1):
        print(f"{i:>3} {p.pid:<6}{p.weight:>7}{p.priority:>6}{p.deadline:>13}{p.destination:>6}")
    if len(sp) > max_rows:
        print(f"... ({len(sp) - max_rows} more parcels)")

    print("\n" + "=" * 72)
    print(f"PHASE 2b - BOX FILLING (0/1 knapsack DP, van capacity = {capacity} kg)")
    print("=" * 72)
    print(f"Best total priority value : {result['best_value']}")
    print(f"Load carried              : {result['load']} / {capacity} kg")
    print("Selected parcels          :", ", ".join(p.pid for p in sel))
    print(f"Left for next trip        : {len(sp) - len(sel)} parcels")
    if len(sp) <= 12 and capacity <= 30:
        print("\nDP table (rows = first i parcels, cols = capacity 0..W):")
        for i, row in enumerate(result["dp"]):
            print(f"  i={i:<2}", " ".join(f"{v:>3}" for v in row))

    print("\n" + "=" * 72)
    print("PHASE 3 - DELIVERY ROUTE (Dijkstra legs + nearest-neighbour TSP)")
    print("=" * 72)
    print("Customer stops :", result["stops"])
    print("Route order    :", " -> ".join(map(str, result["order"])), "(0 = depot)")
    for frm, to, km, path in result["legs"]:
        print(f"  leg {frm:>3} -> {to:<3} {km:>6.1f} km   roads: {' > '.join(map(str, path))}")
    print(f"Total route length: {result['total_km']:.1f} km "
          f"(~{result['total_km'] / SPEED_KMH:.2f} h at {SPEED_KMH:.0f} km/h)")

    print("\nDeadline check for the selected parcels:")
    late = 0
    for p, eta, ok in result["deliveries"]:
        late += not ok
        print(f"  {p.pid}  node {p.destination:<3} ETA {eta:5.2f} h  deadline {p.deadline:>5} h  "
              f"{'ON TIME' if ok else 'LATE'}")
    print(f"  -> {len(result['deliveries']) - late} on time, {late} late")

    print("\nStep timings (seconds):")
    for k, v in result["timings"].items():
        print(f"  {k:<12}{v:.6f}")


def main():
    ap = argparse.ArgumentParser(description="Mini-Courier Planner")
    ap.add_argument("--parcels", default=os.path.join(HERE, "data", "parcels_small.csv"))
    ap.add_argument("--graph", default=os.path.join(HERE, "data", "graph_small.json"))
    ap.add_argument("--capacity", type=int, default=50, help="van capacity in kg")
    ap.add_argument("--benchmark", action="store_true", help="run Phase 4 benchmarks")
    args = ap.parse_args()

    if not os.path.exists(args.parcels) or not os.path.exists(args.graph):
        make_sample_data()

    parcels = load_parcels_csv(args.parcels)
    depot, edges = load_edges_json(args.graph)
    result = plan(parcels, edges, depot, args.capacity)
    show(result, args.capacity)

    if args.benchmark:
        from courier.benchmark import make_charts, bench_two_opt
        out = os.path.join(HERE, "outputs")
        os.makedirs(out, exist_ok=True)
        data = make_charts(out)
        print("\n" + "=" * 72 + "\nPHASE 4 - BENCHMARK RESULTS\n" + "=" * 72)
        print("\nSorting (seconds):")
        print(f"{'n':>7}{'merge':>12}{'insertion':>12}{'bubble':>12}")
        for r in data["sort"]:
            f = lambda x: f"{x:12.5f}" if x is not None else f"{'-':>12}"
            print(f"{r['n']:>7}{r['merge']:12.5f}{f(r['insertion'])}{f(r['bubble'])}")
        print("\nKnapsack DP, capacity 100 (seconds):")
        for r in data["knap"]:
            print(f"{r['n']:>7}{r['time']:12.5f}")
        print("\nGraph algorithms (seconds):")
        print(f"{'V':>7}{'E':>7}{'dijkstra':>12}{'NN-TSP':>12}")
        for r in data["graph"]:
            print(f"{r['v']:>7}{r['e']:>7}{r['dijkstra']:12.5f}{r['tsp']:12.5f}")
        print("\nFull pipeline per step (seconds):")
        print(f"{'parcels':>8}{'nodes':>7}{'sort':>10}{'knap':>10}{'graph':>10}{'route':>10}{'tour km':>10}")
        for r in data["pipe"]:
            print(f"{r['n']:>8}{r['v']:>7}{r['sorting']:10.5f}{r['knapsack']:10.5f}"
                  f"{r['graph_build']:10.5f}{r['routing']:10.5f}{r['tour_km']:10.1f}")
        nn, opt, k = bench_two_opt()
        print(f"\nOptimisation experiment (2-opt on {k} stops): nearest-neighbour "
              f"{nn:.1f} km -> 2-opt {opt:.1f} km ({100 * (nn - opt) / nn:.1f}% shorter)")
        print(f"\nChart saved to {os.path.join(out, 'runtime_charts.png')}")


if __name__ == "__main__":
    main()
