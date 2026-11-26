# Mini-Courier Planner
**Capstone Assignment - Design & Analysis of Algorithms (ETCCDA302)**
K.R. Mangalam University | B.Tech CSE | Faculty: Dr. Shweta Agarwal

Student name: Vicky Saini  Roll no.: 2501010212
A Python prototype that takes a list of parcels and a road network and produces
(1) a priority order, (2) an optimal van load, and (3) an ordered delivery route.

---
## Phase 1 - Problem design and planning

**Problem.** One van leaves a depot (node 0) with a weight limit. Many parcels
are waiting; not all fit. Choose the parcels worth the most, then visit their
customers using a short route, and return to the depot.

**Data design**

| Item | Format |
|---|---|
| Parcel | `pid, weight (kg, int), priority (1-10), deadline (hours), destination (node id)` - `data/parcels_*.csv` |
| Road network | Undirected weighted graph, adjacency list `{node: [(neighbour, km)]}` - `data/graph_*.json` (`depot`, `edges`) |
| Van | Capacity in kg (`--capacity`) |

**Pipeline - how the algorithms work together**

```
parcels.csv ──► MERGE SORT ──► 0/1 KNAPSACK (DP) ──► selected parcels
 (deadline,       urgent        max total priority         │ destinations
  priority)       first         within capacity            ▼
graph.json ──► adjacency list ──► DIJKSTRA (all-pairs on demand) ──► NEAREST-NEIGHBOUR TSP
                                   shortest road between stops        depot → stops → depot
                                                                      + ETA vs deadline check
```

| Step | Algorithm | Why chosen | Complexity |
|---|---|---|---|
| Prioritise | Merge sort | Guaranteed O(n log n), stable (ties keep order) | O(n log n) time, O(n) space |
| Box filling | 0/1 knapsack DP | A parcel cannot be split; greedy can be wrong; DP is exact | O(n·W) time and space |
| Shortest path | Dijkstra (binary heap) | Road distances are non-negative | O((V+E) log V) |
| Route | Nearest-neighbour TSP | TSP is NP-hard; greedy gives a fast approximation | O(k·(V+E) log V) for k stops |

Note: sorting before the knapsack does not change the optimal *value*; it makes the
parcel list readable, gives urgent parcels first in tie situations, and is the
prioritisation step the assignment asks for.

## Phase 2 - Package prioritisation and box filling
`courier/sorting.py`, `courier/knapsack.py`. Parcels are sorted by earliest deadline,
then higher priority, then id. The DP table `dp[i][w]` holds the best priority using
the first `i` parcels with `w` kg; back-tracking from `dp[n][W]` recovers the chosen parcels.
The recurrence is `dp[i][w] = max(dp[i-1][w], dp[i-1][w-wt_i] + value_i)`.
Output evidence: `outputs/sample_run_output.txt`.

## Phase 3 - Route maker and graph processing
`courier/graph.py`. The graph is an adjacency list. Dijkstra gives the shortest road
distance and the actual road path between any two nodes. Nearest-neighbour TSP starts at
the depot, repeatedly drives to the closest unvisited customer, and returns home.
Total length is the sum of Dijkstra leg distances. The program also estimates arrival time
(30 km/h) and flags parcels that would be late.

## Phase 4 - Performance testing and optimisation
Run `python main.py --benchmark`. Chart: `outputs/runtime_charts.png`; numbers in
`outputs/sample_run_output.txt`.

**Observations (measured on the machine used to build this project)**
* Sorting 2,000 parcels: merge sort 0.005 s, insertion sort 0.186 s, bubble sort 0.381 s.
  Merge sort sorted 10,000 parcels in 0.03 s - the O(n log n) vs O(n²) gap is clear.
* Knapsack time grows roughly linearly with n for fixed capacity (O(n·W)): 0.0069 s at n=400, 0.015 s at n=800.
* Dijkstra for one source is under 1 ms even at 800 nodes. Nearest-neighbour TSP is slower
  because it runs Dijkstra once per stop.
* In the full pipeline (1000 parcels / 300 nodes) routing and knapsack dominate; sorting and graph
  building are almost negligible.
* Correctness: 11 unit tests (`outputs/test_results.txt`) - merge sort equals Python's `sorted`,
  knapsack equals brute force on 25 random cases, Dijkstra equals Floyd-Warshall, tours start and end at the depot.

**Optimisation suggestions**
1. **2-opt local search** on the NN tour (implemented in `graph.two_opt`): on a 17-stop test it cut the tour
   from 211.6 km to 173.8 km (about 18% shorter). Nearest-neighbour has no optimality guarantee.
2. **Knapsack space:** keep only two rows (O(W) memory) when the chosen set is not needed, or when it
   is needed use Hirschberg-style reconstruction.
3. **Routing:** run a single multi-target Dijkstra / cache distances between all stops once, instead of
   recomputing per leg; for very large networks use A* or contraction hierarchies.
4. **Deadlines in routing:** the route ignores deadlines (see "LATE" flags in the large run). A future
   version could weight the next-stop choice by deadline or use time-window VRP heuristics.
5. **Multiple trips:** repeat the pipeline on the remaining parcels for trip 2, 3...

**Limitations (honest summary).** Knapsack maximises total priority, not "number of on-time parcels".
One van and one trip. Nearest-neighbour is only an approximation. Weights must be integers for the DP table.

## Phase 5 - How to run / demonstration

Requirements: Python 3.9+, `matplotlib` (only for charts).

```bash
python main.py                                   # small sample, capacity 50 kg
python main.py --capacity 30                     # tighter van, also prints the DP table
python main.py --parcels data/parcels_large.csv --graph data/graph_large.json --capacity 100
python main.py --benchmark                       # + runtime charts and benchmark tables
python -m unittest discover -s tests -v          # correctness tests
```

**Sample result (small dataset, 10 parcels, 50 kg):** selected P005, P003, P004, P002, P010, P006, P007
(value 40, load 49 kg); route `0 → 1 → 6 → 2 → 7 → 4 → 8 → 0`, 52.8 km, all 7 parcels on time.
Full traces: `outputs/sample_run_output.txt`, `outputs/large_run_output.txt`.

**Project layout**
```
main.py                 entry point
courier/                models, sorting, knapsack, graph, planner, datagen, benchmark
data/                   sample datasets (small: 10 parcels/12 nodes, large: 200 parcels/100 nodes)
tests/                  unit tests
outputs/                run traces, test results, runtime_charts.png
```
