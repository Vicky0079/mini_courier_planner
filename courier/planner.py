"""Integration layer: sort -> knapsack -> Dijkstra -> nearest-neighbour route."""
import time

from .graph import build_graph, nearest_neighbor_tsp
from .knapsack import knapsack_dp
from .sorting import merge_sort

SPEED_KMH = 30.0


def plan(parcels, edges, depot, capacity):
    """Run the whole pipeline and return a result dict (with step timings)."""
    t = {}

    s = time.perf_counter()
    sorted_parcels = merge_sort(parcels)
    t["sorting"] = time.perf_counter() - s

    s = time.perf_counter()
    best_value, selected, dp = knapsack_dp(sorted_parcels, capacity)
    t["knapsack"] = time.perf_counter() - s

    s = time.perf_counter()
    graph = build_graph(edges)
    t["graph_build"] = time.perf_counter() - s

    stops = sorted({p.destination for p in selected})
    s = time.perf_counter()
    order, total_km, legs = nearest_neighbor_tsp(graph, depot, stops)
    t["routing"] = time.perf_counter() - s

    # ETA check: does each selected parcel arrive before its deadline?
    eta, clock = {}, 0.0
    for frm, to, km, _ in legs:
        clock += km / SPEED_KMH
        eta.setdefault(to, clock)
    deliveries = [(p, eta[p.destination], eta[p.destination] <= p.deadline)
                  for p in selected]

    return dict(sorted_parcels=sorted_parcels, best_value=best_value,
                selected=selected, dp=dp, graph=graph, stops=stops,
                order=order, total_km=total_km, legs=legs,
                deliveries=deliveries, timings=t,
                load=sum(p.weight for p in selected))
