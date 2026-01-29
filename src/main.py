import os
import os
import yaml
import json
import pandas as pd
from warehouse_graph import build_warehouse_graph
from preprocess import load_data, compute_demand_metrics, build_cooccurrence_matrix
from algorithm import place_items_by_lsc
from evaluation import evaluate_solution

# Path Configuration
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
CONFIG_FILE = os.path.join(BASE_DIR, "config.yaml")

ORDERS_FILE = os.path.join(DATA_DIR, "sample_orders.csv")
ITEM_INFO_FILE = os.path.join(DATA_DIR, "sample_item_info.csv")
INVENTORY_FILE = os.path.join(DATA_DIR, "sample_inventory.csv")

if not os.path.exists(ORDERS_FILE):
    ORDERS_FILE = os.path.join(DATA_DIR, "orders.xlsx")
if not os.path.exists(ITEM_INFO_FILE):
    ITEM_INFO_FILE = os.path.join(DATA_DIR, "item_info.xlsx")

# Optional: Check if inventory file exists, if not usage is None (fallback handled in preprocess)
if not os.path.exists(INVENTORY_FILE):
    INVENTORY_FILE = None # Or maybe check for an excel version?

def load_config():
    with open(CONFIG_FILE, 'r') as f:
        return yaml.safe_load(f)

def main():
    print("------------------------------------------------------------")
    print("Warehouse Item Placement Optimization")
    print("------------------------------------------------------------")
    
    # Load Config
    print(f"[0/5] Loading configuration from {CONFIG_FILE}...")
    config = load_config()
    
    # Extract params
    params = config.get("parameters", {})
    block_capacity = params.get("block_capacity", 60)
    pps_weights = params.get("pps_weights", {"w_freq": 0.5, "w_cooc": 0.5})
    lsc_weights = params.get("lsc_weights", {"w_depot": 0.5, "w_affinity": 0.5})
    
    # Extract layout
    layout_data = config.get("layout", {})

    # 1. Build Graph
    print(f"[1/5] Building warehouse graph from config...")
    G, depot, junctions, blocks = build_warehouse_graph(layout_data)
    print(f"      Graph nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")

    # 2. Load Data
    print(f"[2/5] Loading data from {DATA_DIR}...")
    orders_df, item_info_df, inventory_df = load_data(ORDERS_FILE, ITEM_INFO_FILE, INVENTORY_FILE)
    print(f"      Orders: {len(orders_df)}, Items: {len(item_info_df)}")
    if inventory_df is not None:
        print(f"      Inventory Items: {len(inventory_df)}")

    # 3. Preprocess
    print(f"[3/5] Computing metrics and co-occurrence...")
    item_demand_freq, item_total_inventory, item_blocks_required, item_sizes, item_weight = \
        compute_demand_metrics(orders_df, item_info_df, inventory_df, block_capacity)
    
    cooc_matrix = build_cooccurrence_matrix(orders_df)
    
    # 4. Run Algorithm
    print(f"[4/5] Running PPS + LCS placement algorithm...")
    items = list(item_demand_freq.keys())
    
    block_assignment, placed_blocks = place_items_by_lsc(
        items=items,
        demand=item_demand_freq,
        weight=item_weight,
        k_values=item_blocks_required,
        cooc=cooc_matrix,
        G=G, 
        blocks=blocks, 
        depot=depot,
        pps_weights=pps_weights,
        lsc_weights=lsc_weights
    )
    print(f"      Placed {len(block_assignment)} blocks.")

    # 5. Evaluate
    print(f"[5/5] Evaluating solution...")
    total_dist, handling_effort, order_distances, order_efforts, order_routes = evaluate_solution(
        block_assignment, 
        orders_df, 
        item_sizes, 
        item_weight, 
        item_total_inventory, 
        G, 
        depot, 
        block_capacity
    )

    # --- Debug Outputs ---
    print("\n---------------- DEBUG INFO ----------------")
    print(">>> 1. Item Statistics (Inventory & Blocks)")
    print(f"{'ItemID':<10} {'TotalAmount':<15} {'BlocksRequired':<15}")
    for item in sorted(item_total_inventory.keys()):
        print(f"{item:<10} {item_total_inventory[item]:<15} {item_blocks_required.get(item, 0):<15}")

    print("\n>>> 2. Co-occurrence Matrix (Top 10 pairs)")
    # Sort by frequency desc
    sorted_cooc = sorted(cooc_matrix.items(), key=lambda x: x[1], reverse=True)[:10]
    for (i, j), val in sorted_cooc:
        print(f"({i}, {j}): {val}")

    print("\n>>> 3. Customer Order Metrics")
    print(f"{'CustomerID':<15} {'Dist':<10} {'Effort':<12} {'Path'}")
    for cust in sorted(order_distances.keys()):
        d = order_distances.get(cust, 0)
        e = order_efforts.get(cust, 0)
        r = order_routes.get(cust, [])
        path_str = "->".join(r)
        print(f"{cust:<15} {d:<10.2f} {e:<12.2f} {path_str}")
    print("--------------------------------------------")
    # ---------------------

    # Output Results
    print("\n---------------- Results ----------------")
    print(f"Total Walking Distance: {total_dist:.2f}")
    print(f"Total Handling Effort:  {handling_effort:.2f}")
    print("-----------------------------------------")

    # Save Results
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    # Save assignment
    assignment_path = os.path.join(RESULTS_DIR, "assignment.json")
    with open(assignment_path, "w") as f:
        json.dump(block_assignment, f, indent=4)
        
    # Save metrics
    metrics_path = os.path.join(RESULTS_DIR, "metrics.csv")
    metrics_df = pd.DataFrame({
        "Metric": ["Total Walking Distance", "Total Handling Effort"],
        "Value": [total_dist, handling_effort]
    })
    metrics_df.to_csv(metrics_path, index=False)
    
    print(f"\nSaved assignment to: {assignment_path}")
    print(f"Saved metrics to:    {metrics_path}")

if __name__ == "__main__":
    main()
