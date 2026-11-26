"""Phase 2a - Parcel prioritisation.

Merge sort is used as the 'best' sorting algorithm: O(n log n) in the best,
average AND worst case, and it is STABLE, so parcels with equal keys keep
their original order. Insertion sort / bubble sort are included only so that
Phase 4 can compare their runtime against merge sort.
"""


def priority_key(parcel):
    """Earlier deadline first; ties broken by higher priority; then by id."""
    return (parcel.deadline, -parcel.priority, parcel.pid)


def merge_sort(items, key=priority_key):
    """Return a new sorted list. Time O(n log n), space O(n)."""
    if len(items) <= 1:
        return list(items)
    mid = len(items) // 2
    left = merge_sort(items[:mid], key)
    right = merge_sort(items[mid:], key)
    return _merge(left, right, key)


def _merge(left, right, key):
    merged, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        if key(left[i]) <= key(right[j]):      # <= keeps the sort stable
            merged.append(left[i]); i += 1
        else:
            merged.append(right[j]); j += 1
    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged


def insertion_sort(items, key=priority_key):
    """Baseline for comparison. Time O(n^2) worst/average, O(n) best."""
    arr = list(items)
    for i in range(1, len(arr)):
        cur = arr[i]
        j = i - 1
        while j >= 0 and key(arr[j]) > key(cur):
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = cur
    return arr


def bubble_sort(items, key=priority_key):
    """Baseline for comparison. Time O(n^2)."""
    arr = list(items)
    n = len(arr)
    for i in range(n - 1):
        swapped = False
        for j in range(n - 1 - i):
            if key(arr[j]) > key(arr[j + 1]):
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swapped = True
        if not swapped:
            break
    return arr
