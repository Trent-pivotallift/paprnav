from __future__ import annotations

from collections.abc import Collection, Mapping


def first_cycle_node(graph: Mapping[str, Collection[str]]) -> str | None:
    """Return one back-edge target, or None, without using the Python call stack."""
    colors = {node: 0 for node in graph}
    for root in sorted(graph):
        if colors[root] != 0:
            continue
        colors[root] = 1
        stack = [(root, iter(sorted(graph[root])))]
        while stack:
            node, targets = stack[-1]
            try:
                target = next(targets)
            except StopIteration:
                colors[node] = 2
                stack.pop()
                continue
            if colors[target] == 1:
                return target
            if colors[target] == 0:
                colors[target] = 1
                stack.append((target, iter(sorted(graph[target]))))
    return None
