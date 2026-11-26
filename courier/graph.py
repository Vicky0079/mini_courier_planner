"""Phase 3 - Graph processing and route making.

Graph format: weighted undirected adjacency list
    {node: [(neighbour, distance_km), ...]}
Node 0 is the depot (warehouse); every other node is a customer location.
"""
import heapq

INF = float("inf")


def build_graph(edges):
    """edges: iterable of (u, v, km). Returns an adjacency list."""
    graph = {}
    for u, v, w in edges:
        graph.setdefault(u, []).append((v, w))
        graph.setdefault(v, []).append((u, w))
    return graph


def dijkstra(graph, source):
    """Single-source shortest paths with a binary heap.
    Time O((V + E) log V). Returns (dist, prev)."""
    dist = {node: INF for node in graph}
    prev = {node: None for node in graph}
    dist[source] = 0
    heap = [(0, source)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue                      # stale heap entry
        for v, w in graph[u]:
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                prev[v] = u
                heapq.heappush(heap, (nd, v))
    return dist, prev


def reconstruct_path(prev, target):
    path = []
    while target is not None:
        path.append(target)
        target = prev[target]
    return path[::-1]


def nearest_neighbor_tsp(graph, depot, stops):
    """Approximate delivery tour: from the current location always drive to the
    closest unvisited stop (distance = Dijkstra shortest path), finally return
    to the depot. Greedy heuristic, no optimality guarantee.
    Time O(k * (V + E) log V) for k stops.

    Returns (order, total_km, legs) where legs = [(from, to, km, road_path)].
    """
    unvisited = set(stops) - {depot}
    current, order, legs, total = depot, [depot], [], 0.0
    sp_cache = {}

    def sp(src):
        if src not in sp_cache:
            sp_cache[src] = dijkstra(graph, src)
        return sp_cache[src]

    while unvisited:
        dist, prev = sp(current)
        nxt = min(unvisited, key=lambda s: (dist[s], s))   # tie -> smaller id
        legs.append((current, nxt, dist[nxt], reconstruct_path(prev, nxt)))
        total += dist[nxt]
        order.append(nxt)
        unvisited.remove(nxt)
        current = nxt

    dist, prev = sp(current)                                # return to depot
    legs.append((current, depot, dist[depot], reconstruct_path(prev, depot)))
    total += dist[depot]
    order.append(depot)
    return order, total, legs


def two_opt(graph, order):
    """OPTIONAL improvement (Phase 4 'future optimisation'): repeatedly reverse
    tour segments while that shortens the tour. Order must start/end at depot."""
    nodes = set(order)
    sp = {n: dijkstra(graph, n)[0] for n in nodes}

    def length(t):
        return sum(sp[t[i]][t[i + 1]] for i in range(len(t) - 1))

    best, best_len, improved = list(order), length(order), True
    while improved:
        improved = False
        for i in range(1, len(best) - 2):
            for j in range(i + 1, len(best) - 1):
                cand = best[:i] + best[i:j + 1][::-1] + best[j + 1:]
                cl = length(cand)
                if cl < best_len - 1e-9:
                    best, best_len, improved = cand, cl, True
    return best, best_len
