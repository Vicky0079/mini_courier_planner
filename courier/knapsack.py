"""Phase 2b - Box filling with 0/1 Knapsack (Dynamic Programming).

Each parcel is either loaded or left for another trip (0/1 choice).
Capacity = van capacity in kg, value = parcel priority, cost = parcel weight.
Time O(n * W), space O(n * W) (full table kept so it can be shown and
back-tracked to recover WHICH parcels were chosen).
"""


def knapsack_dp(parcels, capacity):
    """Return (best_value, selected_parcels, dp_table)."""
    n = len(parcels)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        p = parcels[i - 1]
        for w in range(capacity + 1):
            dp[i][w] = dp[i - 1][w]                       # skip parcel i
            if p.weight <= w:                             # or take parcel i
                dp[i][w] = max(dp[i][w], dp[i - 1][w - p.weight] + p.priority)

    # back-track to find the chosen parcels
    selected, w = [], capacity
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i - 1][w]:
            selected.append(parcels[i - 1])
            w -= parcels[i - 1].weight
    selected.reverse()
    return dp[n][capacity], selected, dp


def knapsack_bruteforce(parcels, capacity):
    """Exhaustive O(2^n) checker - used in tests to verify the DP answer."""
    best = 0
    n = len(parcels)
    for mask in range(1 << n):
        wt = val = 0
        for i in range(n):
            if mask >> i & 1:
                wt += parcels[i].weight
                val += parcels[i].priority
        if wt <= capacity and val > best:
            best = val
    return best
