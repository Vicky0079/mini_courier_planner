"""Correctness evidence. Run:  python -m unittest discover -s tests -v"""
import os, sys, unittest, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from courier.datagen import generate_graph_edges, generate_parcels
from courier.graph import build_graph, dijkstra, nearest_neighbor_tsp, two_opt, reconstruct_path
from courier.knapsack import knapsack_dp, knapsack_bruteforce
from courier.models import Parcel
from courier.planner import plan
from courier.sorting import merge_sort, insertion_sort, bubble_sort, priority_key


class TestSorting(unittest.TestCase):
    def test_matches_python_sorted(self):
        ps = generate_parcels(300, 20, seed=3)
        self.assertEqual(merge_sort(ps), sorted(ps, key=priority_key))
        self.assertEqual(insertion_sort(ps), sorted(ps, key=priority_key))
        self.assertEqual(bubble_sort(ps), sorted(ps, key=priority_key))

    def test_edge_cases(self):
        self.assertEqual(merge_sort([]), [])
        one = [Parcel("A", 1, 1, 1.0, 1)]
        self.assertEqual(merge_sort(one), one)

    def test_tie_break_higher_priority_first(self):
        a, b = Parcel("A", 1, 3, 5.0, 1), Parcel("B", 1, 9, 5.0, 2)
        self.assertEqual([p.pid for p in merge_sort([a, b])], ["B", "A"])


class TestKnapsack(unittest.TestCase):
    def test_textbook_case(self):
        ps = [Parcel("A", 1, 1, 1, 1), Parcel("B", 3, 4, 1, 1), Parcel("C", 4, 5, 1, 1),
              Parcel("D", 5, 7, 1, 1)]
        val, sel, _ = knapsack_dp(ps, 7)
        self.assertEqual(val, 9)                                  # B + C
        self.assertEqual({p.pid for p in sel}, {"B", "C"})

    def test_against_bruteforce(self):
        for seed in range(25):
            ps = generate_parcels(10, 10, seed=seed)
            cap = random.Random(seed).randint(5, 60)
            val, sel, _ = knapsack_dp(ps, cap)
            self.assertEqual(val, knapsack_bruteforce(ps, cap))
            self.assertLessEqual(sum(p.weight for p in sel), cap)
            self.assertEqual(sum(p.priority for p in sel), val)

    def test_zero_capacity(self):
        self.assertEqual(knapsack_dp(generate_parcels(5, 5), 0)[0], 0)


class TestGraph(unittest.TestCase):
    def setUp(self):
        #   0 -1- 1 -2- 2
        #   |_____10_____|    shortest 0->2 is 3 via node 1
        self.g = build_graph([(0, 1, 1), (1, 2, 2), (0, 2, 10), (2, 3, 4)])

    def test_dijkstra(self):
        dist, prev = dijkstra(self.g, 0)
        self.assertEqual(dist, {0: 0, 1: 1, 2: 3, 3: 7})
        self.assertEqual(reconstruct_path(prev, 3), [0, 1, 2, 3])

    def test_tsp_returns_to_depot(self):
        order, total, legs = nearest_neighbor_tsp(self.g, 0, [1, 2, 3])
        self.assertEqual(order, [0, 1, 2, 3, 0])
        self.assertAlmostEqual(total, 14)
        self.assertAlmostEqual(sum(l[2] for l in legs), total)

    def test_dijkstra_vs_floyd_warshall(self):
        edges = generate_graph_edges(25, seed=9)
        g = build_graph(edges)
        n = 25
        d = [[float("inf")] * n for _ in range(n)]
        for i in range(n): d[i][i] = 0
        for u, v, w in edges:
            d[u][v] = min(d[u][v], w); d[v][u] = min(d[v][u], w)
        for k in range(n):
            for i in range(n):
                for j in range(n):
                    d[i][j] = min(d[i][j], d[i][k] + d[k][j])
        for s in (0, 7, 20):
            dist, _ = dijkstra(g, s)
            for t in range(n):
                self.assertAlmostEqual(dist[t], d[s][t])

    def test_two_opt_never_worse(self):
        edges = generate_graph_edges(40, seed=4)
        g = build_graph(edges)
        order, total, _ = nearest_neighbor_tsp(g, 0, list(range(1, 15)))
        _, improved = two_opt(g, order)
        self.assertLessEqual(improved, total + 1e-9)


class TestPipeline(unittest.TestCase):
    def test_end_to_end(self):
        ps = generate_parcels(40, 30, seed=5)
        r = plan(ps, generate_graph_edges(30, seed=5), 0, 60)
        self.assertLessEqual(r["load"], 60)
        self.assertEqual(r["order"][0], 0)
        self.assertEqual(r["order"][-1], 0)
        self.assertEqual(set(r["order"][1:-1]), set(r["stops"]))
        self.assertEqual(set(r["timings"]), {"sorting", "knapsack", "graph_build", "routing"})


if __name__ == "__main__":
    unittest.main()
