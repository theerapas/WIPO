def compute_dynamic_pps(
    available_items,  # items not yet fully placed
    placed_items,     # items already at least partially placed
    demand,
    weight,
    cooccurrence,
    w_freq=0.7,
    w_cooc=0.3
):
    all_items = list(demand.keys())

    # Frequency term
    freq_weight = {i: demand[i] * weight[i] for i in all_items}
    max_freq_weight = max(freq_weight.values()) if freq_weight else 1

    # Full co-occurrence normalization
    total_cooc_all = {
        i: sum(cooccurrence.get((i, j), 0) for j in all_items if j != i)
        for i in all_items
    }
    max_total_cooc = max(total_cooc_all.values()) if total_cooc_all else 1

    # Compute PPS
    pps_scores = {}
    for i in available_items:
        freq_term = freq_weight[i] / max_freq_weight
        cooc_term = (
            sum(cooccurrence.get((i, j), 0) for j in placed_items) / max_total_cooc
            if placed_items else 0
        )
        pps_scores[i] = w_freq * freq_term + w_cooc * cooc_term

    return pps_scores


def rank_blocks_dynamically_with_k(
    demand,
    weight,
    k_values,  # dict: item -> required number of placements
    cooccurrence,
    w_freq=0.5,
    w_cooc=0.5
):
    all_items = list(demand.keys())
    placed_items = []
    block_placement_counts = {i: 0 for i in all_items}
    total_required_blocks = sum(k_values.values())
    full_placement_order = []

    while len(full_placement_order) < total_required_blocks:
        # Only consider items not fully placed
        available_items = [i for i in all_items if block_placement_counts[i] < k_values[i]]

        # Compute PPS
        pps_scores = compute_dynamic_pps(
            available_items,
            placed_items,
            demand,
            weight,
            cooccurrence,
            w_freq,
            w_cooc
        )

        # Pick item with highest score
        next_item = max(pps_scores, key=pps_scores.get)
        full_placement_order.append(next_item)
        block_placement_counts[next_item] += 1

        # Only add to placed_items once (for cooc scoring)
        if next_item not in placed_items:
            placed_items.append(next_item)

    return full_placement_order


# Your data
demand = {'A': 5, 'B': 4, 'C': 4, 'D': 4, 'E': 3, 'F': 3, 'G': 4}
weight = {'A': 2, 'B': 8, 'C': 3, 'D': 4, 'E': 2, 'F': 6, 'G': 4}
items = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
matrix = [
    [0, 2, 2, 1, 0, 2, 0],
    [2, 0, 1, 1, 1, 1, 0],
    [2, 1, 0, 1, 0, 2, 0],
    [1, 1, 1, 0, 1, 0, 0],
    [0, 1, 0, 1, 0, 1, 0],
    [2, 1, 2, 0, 1, 0, 0],
    [0, 0, 0, 0, 0, 0, 0]
]

cooccurrence = {}
for i_idx, i in enumerate(items):
    for j_idx, j in enumerate(items):
        if i != j:
            cooccurrence[(i, j)] = matrix[i_idx][j_idx]

k_values={
    'A':3,
    'B':1,
    'C':1,
    'D':2,
    'E':1,
    'F':1,
    'G':1,
}
# Run and print result
order = rank_blocks_dynamically_with_k(demand, weight, k_values, cooccurrence)
print("Placement order:", order)
