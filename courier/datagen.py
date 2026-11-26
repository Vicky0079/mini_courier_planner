"""Reproducible dataset generator + CSV/JSON IO."""
import csv
import json
import random

from .models import Parcel


def generate_graph_edges(num_nodes, seed=42, extra_edge_factor=1.5):
    """Connected random road network: a random spanning tree + extra edges."""
    rnd = random.Random(seed)
    edges, seen = [], set()
    for v in range(1, num_nodes):                       # guarantees connectivity
        u = rnd.randrange(0, v)
        edges.append((u, v, round(rnd.uniform(1, 15), 1)))
        seen.add((u, v))
    for _ in range(int(num_nodes * extra_edge_factor)):
        u, v = rnd.sample(range(num_nodes), 2)
        a, b = min(u, v), max(u, v)
        if (a, b) not in seen:
            seen.add((a, b))
            edges.append((a, b, round(rnd.uniform(1, 15), 1)))
    return edges


def generate_parcels(n, num_nodes, seed=42):
    rnd = random.Random(seed)
    return [
        Parcel(
            pid=f"P{i + 1:03d}",
            weight=rnd.randint(1, 15),
            priority=rnd.randint(1, 10),
            deadline=round(rnd.uniform(1, 24), 1),
            destination=rnd.randint(1, num_nodes - 1),
        )
        for i in range(n)
    ]


def save_parcels_csv(parcels, path):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pid", "weight", "priority", "deadline", "destination"])
        for p in parcels:
            w.writerow([p.pid, p.weight, p.priority, p.deadline, p.destination])


def load_parcels_csv(path):
    with open(path, newline="") as f:
        return [Parcel(r["pid"], int(r["weight"]), int(r["priority"]),
                       float(r["deadline"]), int(r["destination"]))
                for r in csv.DictReader(f)]


def save_edges_json(edges, path, depot=0):
    with open(path, "w") as f:
        json.dump({"depot": depot, "edges": edges}, f, indent=1)


def load_edges_json(path):
    with open(path) as f:
        data = json.load(f)
    return data["depot"], [tuple(e) for e in data["edges"]]
