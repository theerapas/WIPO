import networkx as nx
import re
from collections import defaultdict

def natural_keys(text):
    '''
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    '''
    return [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', str(text))]


def evaluate_solution(block_assignment, orders_df, item_sizes, item_weight, item_total_demand, G, depot, block_capacity=60):
    """
    Evaluates the block assignment based on Walking Distance and Handling Effort.
    """
    
    # Calculate block inventory (how many items fit in a block)
    block_inventory_template = {}
    for block, item in block_assignment.items():
        # Avoid division by zero if size is somehow 0, though unlikely
        size = item_sizes.get(item, 1)
        count = int(block_capacity / size) if size > 0 else 0
        block_inventory_template[block] = count

    item_to_blocklist = defaultdict(list)
    for block, item in block_assignment.items():
        item_to_blocklist[item].append(block)

    def get_sorted_blocks_for_item(item, current_inventory, amount_needed):
        # Sort blocks:
        # 1. Primary: Can fulfill entire amount? (0 = Yes, 1 = No) - "One Stop" preference
        # 2. Secondary: Distance to depot (Ascending)
        blocks = item_to_blocklist[item]
        return sorted(
            blocks,
            key=lambda b: (
                0 if current_inventory[b] >= amount_needed else 1,
                nx.shortest_path_length(G, depot, b, weight="weight"),
            ),
        )

    # 1. Total Walking Distance & Picking Effort
    total_distance = 0
    total_handling_effort = 0
    order_distances = {}
    order_efforts = {}
    order_routes = {}
    
    # Reset inventory for simulation
    simulation_inventory = block_inventory_template.copy()
    
    # Reset inventory for simulation
    simulation_inventory = block_inventory_template.copy()
    
    # Sort customers naturally (P1, P2, ... P10)
    grouped_orders = orders_df.groupby("CustomerID")
    sorted_customers = sorted(grouped_orders.groups.keys(), key=natural_keys)

    for cust in sorted_customers:
        group = grouped_orders.get_group(cust)

        item_amounts = group.groupby("ItemID")["Amount"].sum().to_dict()
        blocks_visited = []
        picked_at_block = defaultdict(float) # Track weight picked at each block
        current_order_effort = 0
        
        for item, amount_needed in item_amounts.items():
            if item not in item_to_blocklist:
                # Item not placed
                continue
                
            sorted_blocks = get_sorted_blocks_for_item(item, simulation_inventory, amount_needed)
            w_i = item_weight.get(item, 0)
            
            for block in sorted_blocks:
                if amount_needed <= 0:
                    break
                available = simulation_inventory.get(block, 0)
                if available == 0:
                    continue
                
                take = min(amount_needed, available)
                simulation_inventory[block] -= take
                amount_needed -= take
                blocks_visited.append(block)
                
                # Accumulate weight picked at this block (not needed for simple effort, but good for debug if needed)
                # picked_at_block[block] += take * w_i
                
                # Handling Effort (Simple Definition)
                # Sum of (Item Weight * Amount * Distance to Assigned Block)
                dist_to_depot = nx.shortest_path_length(G, depot, block, weight="weight")
                current_order_effort += w_i * take * dist_to_depot

        order_efforts[cust] = current_order_effort
        total_handling_effort += current_order_effort

        if not blocks_visited:
            order_distances[cust] = 0
            order_routes[cust] = [depot, depot]
            continue
            
        # Optimize route: Nearest Neighbor TSP
        unique_blocks = set(blocks_visited)
        route = [depot]
        current_loc = depot
        
        while unique_blocks:
            nearest_block = min(
                unique_blocks, 
                key=lambda b: nx.shortest_path_length(G, current_loc, b, weight="weight")
            )
            route.append(nearest_block)
            unique_blocks.remove(nearest_block)
            current_loc = nearest_block
            
        route.append(depot)
        order_routes[cust] = route
        
        # Calculate Distance (TSP Optimized)
        dist = sum(
            nx.shortest_path_length(G, route[i], route[i + 1], weight="weight")
            for i in range(len(route) - 1)
        )
            
        order_distances[cust] = dist
        total_distance += dist

    # Handling Effort is now the sum of per-order efforts (Simple Formula)
            
    return total_distance, total_handling_effort, order_distances, order_efforts, order_routes
