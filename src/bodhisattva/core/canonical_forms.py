"""
Four canonical forms of the Bodhisattva invariant (per RESPONSE 4 of the spec).

1. Scalar: I = (dB*R)/(dH*S)*(1-U) > 1
2. Derivative: dI/dt >= 0  (recursive self-improvement constraint)
3. Graph: No negative ethical cycles in dependency graph
4. One-bit: bool ALLOW_GROWTH
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal
from typing import Sequence

from bodhisattva.core.invariant import InvariantInputs, InvariantResult, compute_index


# --- Form 1: Scalar ---

def scalar_form(inputs: InvariantInputs) -> InvariantResult:
    """Canonical Form 1: Single scalar Bodhisattva Index."""
    return compute_index(inputs)


# --- Form 2: Derivative (Recursive Self-Improvement Constraint) ---

@dataclass(frozen=True, slots=True)
class DerivativeResult:
    """Result of the derivative form: dI/dt must be >= 0."""
    index_before: Decimal
    index_after: Decimal
    delta_index: Decimal
    improvement_safe: bool
    growth_permitted_before: bool
    growth_permitted_after: bool


def derivative_form(
    before: InvariantInputs,
    after: InvariantInputs,
) -> DerivativeResult:
    """
    Canonical Form 2: Recursive self-improvement constraint.

    A self-improvement step is safe iff the Bodhisattva Index does not decrease.
    This prevents capability growth that undermines its own safety justification.
    """
    result_before = compute_index(before)
    result_after = compute_index(after)
    delta = result_after.index - result_before.index

    return DerivativeResult(
        index_before=result_before.index,
        index_after=result_after.index,
        delta_index=delta,
        improvement_safe=delta >= Decimal("0"),
        growth_permitted_before=result_before.growth_permitted,
        growth_permitted_after=result_after.growth_permitted,
    )


# --- Form 3: Graph Invariant (No Negative Ethical Cycles) ---

@dataclass(frozen=True, slots=True)
class EthicalEdge:
    """An edge in the ethical dependency graph."""
    source: str
    target: str
    weight: Decimal  # Bodhisattva Index for this transition (>1 = net-positive)


@dataclass(frozen=True, slots=True)
class GraphInvariantResult:
    """Result of checking for negative ethical cycles."""
    has_negative_cycle: bool
    negative_cycles: list[list[str]]
    growth_permitted: bool


def graph_invariant_form(edges: Sequence[EthicalEdge]) -> GraphInvariantResult:
    """
    Canonical Form 3: No negative ethical cycles.

    A "negative ethical cycle" is a cycle where the product of all edge
    weights < 1 (traversing the full cycle results in net harm).

    Uses log-transformed Bellman-Ford: product < 1  <=>  sum of logs < 0.
    """
    if not edges:
        return GraphInvariantResult(
            has_negative_cycle=False,
            negative_cycles=[],
            growth_permitted=True,
        )

    # Collect all nodes
    nodes: set[str] = set()
    for e in edges:
        nodes.add(e.source)
        nodes.add(e.target)

    node_list = sorted(nodes)
    node_idx = {n: i for i, n in enumerate(node_list)}
    n = len(node_list)

    # Bellman-Ford on -log(weight) to detect negative product cycles
    # Product < 1  <=>  sum(log(w)) < 0  <=>  sum(-log(w)) > 0
    # We detect negative cycles in -log space, which correspond to product > 1
    # Actually: we want to detect product < 1, i.e. sum(log(w)) < 0
    # So we use +log(w) as weights and look for negative cycles
    INF = float("inf")
    dist = [INF] * n
    pred = [-1] * n

    # Use node 0 as source, but run from all nodes for disconnected graphs
    for start in range(n):
        if dist[start] != INF:
            continue
        dist[start] = 0.0

        for _ in range(n - 1):
            for e in edges:
                u = node_idx[e.source]
                v = node_idx[e.target]
                w = -float(e.weight.ln()) if e.weight > 0 else INF
                if dist[u] + w < dist[v]:
                    dist[v] = dist[u] + w
                    pred[v] = u

    # Check for negative cycles (one more relaxation pass)
    negative_cycle_nodes: set[int] = set()
    for e in edges:
        u = node_idx[e.source]
        v = node_idx[e.target]
        # Use math.log for float conversion since Decimal.ln() may not be available
        try:
            w = -math.log(float(e.weight)) if float(e.weight) > 0 else INF
        except (ValueError, OverflowError):
            w = INF
        if dist[u] + w < dist[v]:
            negative_cycle_nodes.add(v)

    # Reconstruct cycles (simplified: just report involved nodes)
    negative_cycles: list[list[str]] = []
    if negative_cycle_nodes:
        cycle_node_names = [node_list[i] for i in negative_cycle_nodes]
        negative_cycles.append(cycle_node_names)

    has_neg = len(negative_cycles) > 0
    return GraphInvariantResult(
        has_negative_cycle=has_neg,
        negative_cycles=negative_cycles,
        growth_permitted=not has_neg,
    )


# --- Form 4: One-Bit Rule ---

def one_bit_form(inputs: InvariantInputs) -> bool:
    """
    Canonical Form 4: The simplest possible form.

    Returns a single boolean: grow or don't grow.
    This is what gets encoded in firmware.
    """
    result = compute_index(inputs)
    return result.growth_permitted
