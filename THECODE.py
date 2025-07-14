# Full code for warehouse item placement optimization

import networkx as nx
import pandas as pd
import numpy as np
from itertools import combinations
from collections import defaultdict

# -------- Step 0: Build the warehouse graph --------
G = nx.Graph()
depot = "depot"
junctions = [f"j{i}" for i in range(1, 7)]
blocks = [f"b{i}" for i in range(1, 13)]

# Add nodes
G.add_node(depot, type="depot")
for j in junctions:
    G.add_node(j, type="junction")
for b in blocks:
    G.add_node(b, type="block")

# Add edges (depot distance = 3)
G.add_edge(depot, "j1", weight=3)
G.add_edge(depot, "j4", weight=3)

# Left side
G.add_edge("j1", "j2", weight=1)
G.add_edge("j2", "j3", weight=1)
G.add_edge("j1", "b1", weight=1)
G.add_edge("j1", "b2", weight=1)
G.add_edge("j2", "b3", weight=1)
G.add_edge("j2", "b4", weight=1)
G.add_edge("j3", "b5", weight=1)
G.add_edge("j3", "b6", weight=1)

# Right side
G.add_edge("j4", "j5", weight=1)
G.add_edge("j5", "j6", weight=1)
G.add_edge("j4", "b7", weight=1)
G.add_edge("j4", "b8", weight=1)
G.add_edge("j5", "b9", weight=1)
G.add_edge("j5", "b10", weight=1)
G.add_edge("j6", "b11", weight=1)
G.add_edge("j6", "b12", weight=1)

# -------- Step 1: Input order data --------
orders_df = pd.DataFrame(
    [
        {"CustomerID": "p1", "ItemID": "A", "Amount": 10},
        {"CustomerID": "p1", "ItemID": "B", "Amount": 3},
        {"CustomerID": "p2", "ItemID": "C", "Amount": 12},
        {"CustomerID": "p2", "ItemID": "F", "Amount": 3},
        {"CustomerID": "p3", "ItemID": "A", "Amount": 8},
        {"CustomerID": "p3", "ItemID": "C", "Amount": 4},
        {"CustomerID": "p3", "ItemID": "D", "Amount": 6},
        {"CustomerID": "p4", "ItemID": "E", "Amount": 10},
        {"CustomerID": "p4", "ItemID": "B", "Amount": 4},
        {"CustomerID": "p5", "ItemID": "D", "Amount": 10},
        {"CustomerID": "p5", "ItemID": "F", "Amount": 4},
        {"CustomerID": "p6", "ItemID": "A", "Amount": 6},
        {"CustomerID": "p6", "ItemID": "B", "Amount": 3},
        {"CustomerID": "p6", "ItemID": "E", "Amount": 3},
        {"CustomerID": "p7", "ItemID": "C", "Amount": 10},
        {"CustomerID": "p7", "ItemID": "F", "Amount": 3},
    ]
)

# -------- Step 2: Preprocessing --------
block_capacity = 10

# Frequency-based demand
item_demand_freq = orders_df.groupby("ItemID").size().to_dict()
item_blocks_required = {
    item: int(
        np.ceil(orders_df[orders_df["ItemID"] == item]["Amount"].sum() / block_capacity)
    )
    for item in item_demand_freq
}

# Co-occurrence matrix
grouped_orders = orders_df.groupby("CustomerID")
co_occurrence = defaultdict(lambda: defaultdict(int))
for _, group in grouped_orders:
    items = group["ItemID"].unique()
    for i, j in combinations(items, 2):
        co_occurrence[i][j] += 1
        co_occurrence[j][i] += 1
co_occurrence_df = pd.DataFrame(co_occurrence).fillna(0).astype(int)

# PPS Calculation
w_freq, w_cooc = 0.7, 0.3
max_demand = max(item_demand_freq.values())
demand_score = {i: item_demand_freq[i] / max_demand for i in item_demand_freq}
cooc_sum = co_occurrence_df.sum(axis=1).to_dict()
max_cooc_sum = max(cooc_sum.values()) if cooc_sum else 1
cooc_score = {i: cooc_sum.get(i, 0) / max_cooc_sum for i in item_demand_freq}
pps_score = {
    i: w_freq * demand_score[i] + w_cooc * cooc_score.get(i, 0)
    for i in item_demand_freq
}
sorted_items_by_pps = sorted(pps_score.items(), key=lambda x: -x[1])

# -------- Step 3: Compute distance from depot to each block --------
block_nodes = [f"b{i}" for i in range(1, 13)]
block_distances = {
    b: nx.shortest_path_length(G, depot, b, weight="weight") for b in block_nodes
}
sorted_blocks_by_distance = sorted(block_distances.items(), key=lambda x: x[1])

# -------- Step 4: Greedy item-to-block assignment --------
available_blocks = [b for b, _ in sorted_blocks_by_distance]
item_to_blocks = {}
used_blocks = set()
for item, _ in sorted_items_by_pps:
    k = item_blocks_required[item]
    assigned = []
    for block in available_blocks:
        if block not in used_blocks:
            assigned.append(block)
            used_blocks.add(block)
            if len(assigned) == k:
                break
    item_to_blocks[item] = assigned

block_assignment = {}
for item, blocks in item_to_blocks.items():
    for b in blocks:
        block_assignment[b] = item

# -------- Step 5: Order simulation and distance calculation --------
item_to_blocklist = defaultdict(list)
for b, i in block_assignment.items():
    item_to_blocklist[i].append(b)


def get_nearest_block(item):
    blocks = item_to_blocklist[item]
    return min(blocks, key=lambda b: block_distances[b])


total_distance = 0
order_distances = {}
for cust, group in orders_df.groupby("CustomerID"):
    items = group["ItemID"].unique().tolist()
    blocks_to_visit = [get_nearest_block(i) for i in items]
    locs = ["depot"] + blocks_to_visit
    dist_matrix = {
        (a, b): nx.shortest_path_length(G, a, b, weight="weight")
        for a in locs
        for b in locs
        if a != b
    }
    path_order = ["depot"] + blocks_to_visit + ["depot"]
    dist = sum(
        dist_matrix[(path_order[i], path_order[i + 1])]
        for i in range(len(path_order) - 1)
    )
    order_distances[cust] = dist
    total_distance += dist

(block_assignment, order_distances, total_distance)
