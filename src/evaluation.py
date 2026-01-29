import networkx as nx
from collections import defaultdict

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

    def get_sorted_blocks_for_item(item, current_inventory):
        # Sort blocks by distance to depot (greedy approach for picking)
        # Also could consider remaining inventory, but original code used distance + inventory check
        blocks = item_to_blocklist[item]
        return sorted(
            blocks,
            key=lambda b: (
                nx.shortest_path_length(G, depot, b, weight="weight"),
                current_inventory[b], # Tie breaker? Original code had this in key tuple
            ),
        )

    # 1. Total Walking Distance & Picking Effort
    total_distance = 0
    order_distances = {}
    order_efforts = {}
    order_routes = {}
    
    # Reset inventory for simulation
    simulation_inventory = block_inventory_template.copy()
    
    for cust, group in orders_df.groupby("CustomerID"):
        item_amounts = group.groupby("ItemID")["Amount"].sum().to_dict()
        blocks_visited = []
        current_order_effort = 0
        
        for item, amount_needed in item_amounts.items():
            if item not in item_to_blocklist:
                # Item not placed
                continue
                
            sorted_blocks = get_sorted_blocks_for_item(item, simulation_inventory)
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
                
                # Picking Effort for this part of the order
                dist_to_depot = nx.shortest_path_length(G, depot, block, weight="weight")
                current_order_effort += w_i * take * dist_to_depot

        order_efforts[cust] = current_order_effort

        if not blocks_visited:
            order_distances[cust] = 0
            order_routes[cust] = [depot, depot]
            continue
            
        # Optimize route: Nearest Neighbor TSP
        # Start at depot, always go to the nearest unvisited unique block
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
        
        dist = sum(
            nx.shortest_path_length(G, route[i], route[i + 1], weight="weight")
            for i in range(len(route) - 1)
        )
        order_distances[cust] = dist
        total_distance += dist

    # 2. Handling Effort (Placement/Stocking Effort)
    # This remains as the global layout metric
    handling_effort = 0
    
    # Recompute average filling for handling effort calculation
    for item, blocks in item_to_blocklist.items():
        total_demand = item_total_demand.get(item, 0)
        total_blocks = len(blocks)
        if total_blocks == 0: continue
            
        avg_amount = total_demand // total_blocks
        leftover = total_demand % total_blocks

        for idx, block in enumerate(blocks):
            amount_in_block = avg_amount + (1 if idx < leftover else 0)
            dist = nx.shortest_path_length(G, depot, block, weight="weight")
            effort = item_weight.get(item, 0) * amount_in_block * dist
            handling_effort += effort
            
    return total_distance, handling_effort, order_distances, order_efforts, order_routes
