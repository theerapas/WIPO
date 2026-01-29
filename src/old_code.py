import networkx as nx
import pandas as pd
import numpy as np
from itertools import combinations
from collections import defaultdict

# ---------------- Step 0: Build the warehouse graph ----------------
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

# G.add_edge(depot, "j1", weight=1)

# G.add_edge("j1", "j2", weight=1)
# G.add_edge("j2", "j3", weight=1)
# G.add_edge("j3", "j4", weight=1)
# G.add_edge("j4", "j5", weight=1)

# G.add_edge("j1", "b1", weight=1)
# G.add_edge("j1", "b2", weight=1)
# G.add_edge("j2", "b3", weight=1)
# G.add_edge("j2", "b4", weight=1)
# G.add_edge("j3", "b5", weight=1)
# G.add_edge("j3", "b6", weight=1)
# G.add_edge("j4", "b7", weight=1)
# G.add_edge("j4", "b8", weight=1)
# G.add_edge("j5", "b9", weight=1)
# G.add_edge("j5", "b10", weight=1)
# ---------------- Step 1: Load Excel Input ----------------
orders_df = pd.read_excel("orders.xlsx")
item_info_df = pd.read_excel("item_info.xlsx")

# Convert to dictionaries
item_sizes = item_info_df.set_index("ItemID")["Size"].to_dict()
item_weight = item_info_df.set_index("ItemID")["Weight"].to_dict()

# ---------------- Step 2: Preprocessing ----------------
block_capacity = 60

item_demand_freq = orders_df.groupby("ItemID").size().to_dict()
item_total_demand = orders_df.groupby("ItemID")["Amount"].sum().to_dict()
item_blocks_required = {
    item: int(np.ceil(item_total_demand[item] * item_sizes[item] / block_capacity))
    for item in item_demand_freq
}

print("d:", item_demand_freq)
print("k:", item_blocks_required)

# Co-occurrence matrix
grouped_orders = orders_df.groupby("CustomerID")
co_occurrence = defaultdict(lambda: defaultdict(int))
for _, group in grouped_orders:
    items = group["ItemID"].unique()
    for i, j in combinations(items, 2):
        co_occurrence[i][j] += 1
        co_occurrence[j][i] += 1
co_occurrence_pairs = {
    (i, j): co_occurrence[i][j] for i in co_occurrence for j in co_occurrence[i]
}

print("CO:", co_occurrence_pairs)


# ---------------- Step 3: LSC-based Placement ----------------
def compute_dynamic_pps(unplaced, placed, demand, weight, cooc, w_freq=0.5, w_cooc=0.5):
    freq_weight = {i: demand[i] * weight[i] for i in demand}
    max_freq_weight = max(freq_weight.values()) if freq_weight else 1
    total_cooc_all = {
        i: sum(cooc.get((i, j), 0) for j in demand if j != i) for i in demand
    }
    max_total_cooc = max(total_cooc_all.values()) if total_cooc_all else 1
    pps = {}
    for i in unplaced:
        freq_term = freq_weight[i] / max_freq_weight if max_freq_weight else 0
        cooc_sum = sum(cooc.get((i, j), 0) for j in placed)
        cooc_term = cooc_sum / max_total_cooc if max_total_cooc else 0
        pps[i] = w_freq * freq_term + w_cooc * cooc_term
    return pps


def compute_lsc(
    item_id, b, item_weight, item_k, placed_blocks, cooc, w_depot=0.5, w_affinity=0.5
):
    w_i = item_weight[item_id]
    k_i = item_k[item_id]
    dist_depot = nx.shortest_path_length(G, depot, b, weight="weight")
    depot_term = w_depot * (dist_depot * w_i / k_i) if k_i else float("inf")
    affinity_term = 0
    for j, blocks_j in placed_blocks.items():
        for b_j in blocks_j:
            co = cooc.get((item_id, j), 0)
            dist = nx.shortest_path_length(G, b, b_j, weight="weight")
            affinity_term += co * dist
    affinity_term *= w_affinity
    print("Block :", b, "LCS :", depot_term + affinity_term)
    return depot_term + affinity_term


def place_items_by_lsc(items, demand, weight, k_values, cooc):
    placed_blocks = defaultdict(list)
    block_assignment = {}
    item_placed_count = {i: 0 for i in items}
    placed_items = []
    available_blocks = blocks.copy()
    while sum(item_placed_count.values()) < sum(k_values.values()):
        unplaced = [i for i in items if item_placed_count[i] < k_values[i]]
        print("I :", unplaced)
        pps_scores = compute_dynamic_pps(unplaced, placed_items, demand, weight, cooc)
        print("PPS :", pps_scores)
        current_item = max(pps_scores, key=pps_scores.get)
        print("Pick I:", current_item)
        print("Available Blocks:", available_blocks)
        best_block = min(
            available_blocks,
            key=lambda b: compute_lsc(
                current_item, b, weight, k_values, placed_blocks, cooc
            ),
        )
        print("Pick B:", best_block)
        placed_blocks[current_item].append(best_block)
        block_assignment[best_block] = current_item
        item_placed_count[current_item] += 1
        available_blocks.remove(best_block)
        if current_item not in placed_items:
            placed_items.append(current_item)
    return block_assignment, placed_blocks


block_assignment, placed_blocks = place_items_by_lsc(
    items=list(item_demand_freq.keys()),
    demand=item_demand_freq,
    weight=item_weight,
    k_values=item_blocks_required,
    cooc=co_occurrence_pairs,
)

# ---------------- Step 4: Evaluation ----------------
block_inventory = {
    block: block_capacity / item_sizes[block_assignment[block]]
    for block in block_assignment
}
# print(block_inventory)
item_to_blocklist = defaultdict(list)
for block, item in block_assignment.items():
    item_to_blocklist[item].append(block)


def get_sorted_blocks_for_item(item):
    return sorted(
        item_to_blocklist[item],
        key=lambda b: (
            nx.shortest_path_length(G, depot, b, weight="weight"),
            block_inventory[b],
        ),
    )


total_distance = 0
order_distances = {}

for cust, group in orders_df.groupby("CustomerID"):
    item_amounts = group.groupby("ItemID")["Amount"].sum().to_dict()
    # print(item_amounts)
    blocks_visited = []

    for item, amount_needed in item_amounts.items():
        for block in get_sorted_blocks_for_item(item):
            if amount_needed == 0:
                break
            available = block_inventory[block]
            if available == 0:
                continue
            take = min(amount_needed, available)
            block_inventory[block] -= take
            amount_needed -= take
            blocks_visited.append(block)

    route = ["depot"] + blocks_visited + ["depot"]
    # print(route)
    dist = sum(
        nx.shortest_path_length(G, route[i], route[i + 1], weight="weight")
        for i in range(len(route) - 1)
    )
    order_distances[cust] = dist
    total_distance += dist

# ---------------- Step 5: Handling Effort ----------------
handling_effort = 0

# First, recompute how much each block actually holds
# Assumption: the blocks are evenly filled based on item demand
item_remaining = item_total_demand.copy()

for item, blocks in item_to_blocklist.items():
    total_demand = item_total_demand[item]
    total_blocks = len(blocks)
    avg_amount = total_demand // total_blocks
    leftover = total_demand % total_blocks

    for idx, block in enumerate(blocks):
        # Distribute leftover to the first few blocks
        amount_in_block = avg_amount + (1 if idx < leftover else 0)
        dist = nx.shortest_path_length(G, depot, block, weight="weight")
        effort = item_weight[item] * amount_in_block * dist
        handling_effort += effort

print("Block Assignments:", block_assignment)
print("Order Distance:", order_distances)
print("Total Distance:", total_distance)
print("Total Handling Effort:", handling_effort)
