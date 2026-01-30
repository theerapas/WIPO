import networkx as nx
from collections import defaultdict

def compute_dynamic_pps(unplaced, placed, demand, weight, cooc, w_freq=0.5, w_cooc=0.5):
    """
    Computes Placement Priority Score (PPS) for unplaced items.
    """
    freq_weight = {i: demand[i] * weight[i] for i in demand}
    max_freq_weight = max(freq_weight.values()) if freq_weight else 1
    
    # Calculate max possible co-occurrence sum for normalization
    total_cooc_all = {
        i: sum(cooc.get((i, j), 0) for j in demand if j != i) for i in demand
    }
    max_total_cooc = max(total_cooc_all.values()) if total_cooc_all else 1
    
    pps = {}
    for i in unplaced:
        freq_term = freq_weight.get(i, 0) / max_freq_weight if max_freq_weight else 0
        cooc_sum = sum(cooc.get((i, j), 0) for j in placed)
        cooc_term = cooc_sum / max_total_cooc if max_total_cooc else 0
        pps[i] = w_freq * freq_term + w_cooc * cooc_term
    return pps

def compute_lsc(item_id, b, item_weight, item_k, placed_blocks, cooc, G, depot, w_depot=0.5, w_affinity=0.5):
    """
    Computes Location Cost Score (LCS) for a block candidate.
    """
    w_i = item_weight[item_id]
    k_i = item_k[item_id]
    dist_depot = nx.shortest_path_length(G, depot, b, weight="weight")
    
    # Avoid division by zero
    depot_term = w_depot * (dist_depot * w_i / k_i) if k_i else float("inf")
    
    affinity_term = 0
    for j, blocks_j in placed_blocks.items():
        for b_j in blocks_j:
            co = cooc.get((item_id, j), 0)
            dist = nx.shortest_path_length(G, b, b_j, weight="weight")
            affinity_term += co * dist
    affinity_term *= w_affinity
    
    # print(f"Block : {b} LCS : {depot_term + affinity_term}")
    return depot_term + affinity_term

def place_items_by_lsc(items, demand, weight, k_values, cooc, G, blocks, depot, pps_weights=None, lsc_weights=None):
    """
    Main heuristic loop to place items into blocks.
    """
    if pps_weights is None:
        pps_weights = {"w_freq": 0.5, "w_cooc": 0.5}
    if lsc_weights is None:
        lsc_weights = {"w_depot": 0.5, "w_affinity": 0.5}

    placed_blocks = defaultdict(list)
    block_assignment = {}
    item_placed_count = {i: 0 for i in items}
    placed_items = []
    available_blocks = blocks.copy()
    
    # While there is still demand to be filled and blocks available
    while sum(item_placed_count.values()) < sum(k_values.values()):
        if not available_blocks:
            print("Warning: Ran out of blocks before placing all items!")
            break
            
        unplaced = [i for i in items if item_placed_count[i] < k_values[i]]
        # print("I :", unplaced)
        
        pps_scores = compute_dynamic_pps(
            unplaced, 
            placed_items, 
            demand, 
            weight, 
            cooc, 
            w_freq=pps_weights.get("w_freq", 0.5), 
            w_cooc=pps_weights.get("w_cooc", 0.5)
        )
        # print("PPS :", pps_scores)
        
        if not pps_scores:
            break
            
        current_item = max(pps_scores, key=pps_scores.get)
        # print("Pick I:", current_item)
        
        # Select best block (Lowest LCS)
        best_block = min(
            available_blocks,
            key=lambda b: compute_lsc(
                current_item, 
                b, 
                weight, 
                k_values, 
                placed_blocks, 
                cooc, 
                G, 
                depot,
                w_depot=lsc_weights.get("w_depot", 0.5),
                w_affinity=lsc_weights.get("w_affinity", 0.5)
            ),
        )
        # print("Pick B:", best_block)
        
        placed_blocks[current_item].append(best_block)
        block_assignment[best_block] = current_item
        item_placed_count[current_item] += 1
        available_blocks.remove(best_block)
        
        if current_item not in placed_items:
            placed_items.append(current_item)
            
    return block_assignment, placed_blocks
