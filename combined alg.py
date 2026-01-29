# Redefine after kernel reset


def compute_dynamic_pps(
    unplaced_items, placed_items, demand, weight, cooccurrence, w_freq=0.7, w_cooc=0.3
):
    print("Inputs:", unplaced_items, placed_items, demand, weight, cooccurrence)
    all_items = list(demand.keys())
    freq_weight = {i: demand[i] * weight[i] for i in all_items}
    max_freq_weight = max(freq_weight.values()) if freq_weight else 1

    print("Freq_weight:", freq_weight)
    print("Max Freq Weight:", max_freq_weight)
    total_cooc_all = {
        i: sum(cooccurrence.get((i, j), 0) for j in all_items if j != i)
        for i in all_items
    }
    max_total_cooc = max(total_cooc_all.values()) if total_cooc_all else 1
    print("total_cooc_all:", total_cooc_all)
    print("max_total_cooc:", max_total_cooc)
    pps_scores = {}
    for i in unplaced_items:
        freq_term = freq_weight[i] / max_freq_weight if max_freq_weight else 0
        cooc_sum = sum(cooccurrence.get((i, j), 0) for j in placed_items)
        cooc_term = cooc_sum / max_total_cooc if max_total_cooc else 0
        print(i, w_freq, freq_term, w_cooc, cooc_term)
        pps_scores[i] = w_freq * freq_term + w_cooc * cooc_term

    print(pps_scores)
    return pps_scores


def compute_lsc(
    item_id,
    candidate_block,
    depot_distances,
    item_weight,
    item_k,
    placed_blocks,
    cooccurrence,
    block_distances,
    w_depot=0.5,
    w_affinity=0.5,
):
    w_i = item_weight[item_id]
    k_i = item_k[item_id]
    dist_depot = depot_distances[candidate_block]
    depot_term = w_depot * (dist_depot * w_i / k_i) if k_i != 0 else float("inf")

    affinity_term = 0
    for j, block_list in placed_blocks.items():
        for block_j in block_list:
            co = cooccurrence.get((item_id, j), 0)
            dist = block_distances.get((candidate_block, block_j), 0)
            affinity_term += co * dist
    affinity_term *= w_affinity

    return depot_term + affinity_term


def place_items_by_pps_lsc(
    items,
    demand,
    weight,
    k_values,
    cooccurrence,
    candidate_blocks,
    depot_distances,
    block_distances,
    w_freq=0.7,
    w_cooc=0.3,
    w_depot=0.5,
    w_affinity=0.5,
):
    placed_blocks = {}  # item_id -> list of assigned blocks
    block_assignment = {}  # block_id -> item_id
    item_placed_count = {i: 0 for i in items}
    placed_items = []
    available_blocks = candidate_blocks.copy()

    while sum(item_placed_count[i] for i in items) < sum(k_values[i] for i in items):
        unplaced_items = [i for i in items if item_placed_count[i] < k_values[i]]
        pps_scores = compute_dynamic_pps(
            unplaced_items, placed_items, demand, weight, cooccurrence, w_freq, w_cooc
        )
        current_item = max(pps_scores, key=pps_scores.get)

        best_block = None
        best_lsc = float("inf")
        for block in available_blocks:
            lsc = compute_lsc(
                current_item,
                block,
                depot_distances,
                weight,
                k_values,
                placed_blocks,
                cooccurrence,
                block_distances,
                w_depot,
                w_affinity,
            )
            if lsc < best_lsc:
                best_lsc = lsc
                best_block = block

        if current_item not in placed_blocks:
            placed_blocks[current_item] = []
        placed_blocks[current_item].append(best_block)
        block_assignment[best_block] = current_item
        item_placed_count[current_item] += 1
        available_blocks.remove(best_block)

        if current_item not in placed_items:
            placed_items.append(current_item)

    return block_assignment, placed_blocks


# Your data
items = ["A", "B", "C", "D", "H", "I"]
demand = {"A": 3, "B": 2, "C": 1, "D": 4, "H": 3, "I": 2}
weight = {"A": 2, "B": 8, "C": 3, "D": 4, "H": 2, "I": 5}
k_values = {
    "A": 2,
    "B": 1,
    "C": 1,
    "D": 2,
    "H": 3,
    "I": 1,
}

matrix = [
    [0, 1, 0, 0, 1, 1],
    [1, 0, 0, 1, 1, 0],
    [0, 0, 0, 1, 1, 0],
    [0, 1, 1, 0, 2, 1],
    [1, 1, 1, 2, 0, 0],
    [1, 0, 0, 1, 0, 0],
]

cooccurrence = {}
for i_idx, i in enumerate(items):
    for j_idx, j in enumerate(items):
        if i != j:
            cooccurrence[(i, j)] = matrix[i_idx][j_idx]

blocks = [f"b{i}" for i in range(1, 11)]
distance_matrix = [
    [0, 2, 3, 3, 4, 4, 5, 5, 6, 6, 2],
    [2, 0, 3, 3, 4, 4, 5, 5, 6, 6, 2],
    [3, 3, 0, 2, 3, 3, 4, 4, 5, 5, 3],
    [3, 3, 2, 0, 3, 3, 4, 4, 5, 5, 3],
    [4, 4, 3, 3, 0, 2, 3, 3, 4, 4, 4],
    [4, 4, 3, 3, 2, 0, 3, 3, 4, 4, 4],
    [5, 5, 4, 4, 3, 3, 0, 2, 3, 3, 5],
    [5, 5, 4, 4, 3, 3, 2, 0, 3, 3, 5],
    [6, 6, 5, 5, 4, 4, 3, 3, 0, 2, 6],
    [6, 6, 5, 5, 4, 4, 3, 3, 2, 0, 6],
]

block_distances = {}
depot_distances = {}

for i, bi in enumerate(blocks):
    for j, bj in enumerate(blocks):
        block_distances[(bi, bj)] = distance_matrix[i][j]
    depot_distances[bi] = distance_matrix[i][-1]


block_assignment, placed_blocks = place_items_by_pps_lsc(
    items=items,
    demand=demand,
    weight=weight,
    k_values=k_values,
    cooccurrence=cooccurrence,
    candidate_blocks=blocks,
    depot_distances=depot_distances,
    block_distances=block_distances,
)


print("📦 Block Assignments (block → item):")
for block, item in block_assignment.items():
    print(f"Block {block} → Item {item}")

print("\n📦 Items Placed In Blocks:")
for item, blocks in placed_blocks.items():
    print(f"Item {item} → {blocks}")
