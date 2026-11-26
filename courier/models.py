"""Data design for the courier problem (Phase 1)."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Parcel:
    """A single parcel to be delivered.

    pid          unique id, e.g. "P01"
    weight       weight in kg (integer, needed for the DP table)
    priority     business value 1..10 (10 = most important); used as knapsack value
    deadline     hours from now by which the parcel must be delivered
    destination  graph node id (customer location)
    """
    pid: str
    weight: int
    priority: int
    deadline: float
    destination: int
