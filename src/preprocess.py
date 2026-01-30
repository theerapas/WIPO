import pandas as pd
import numpy as np
from itertools import combinations
from collections import defaultdict
import os

def load_data(orders_path, item_info_path, inventory_path=None):
    """
    Loads orders, item info, and optional inventory from CSV (preferred) or Excel.
    """
    if orders_path.endswith(".csv"):
        orders_df = pd.read_csv(orders_path)
    else:
        orders_df = pd.read_excel(orders_path)

    if item_info_path.endswith(".csv"):
        item_info_df = pd.read_csv(item_info_path)
    else:
        item_info_df = pd.read_excel(item_info_path)
        
    inventory_df = None
    if inventory_path:
        if inventory_path.endswith(".csv"):
            inventory_df = pd.read_csv(inventory_path)
        else:
            # Assuming support for excel for inventory too if needed
            inventory_df = pd.read_excel(inventory_path)
            
    return orders_df, item_info_df, inventory_df

def compute_demand_metrics(orders_df, item_info_df, inventory_df, block_capacity=60):
    """
    Computes demand metrics required for the algorithm.
    inventory_df overrides order demand for block calculation and handling effort.
    """
    # Convert to dictionaries
    item_sizes = item_info_df.set_index("ItemID")["Size"].to_dict()
    item_weight = item_info_df.set_index("ItemID")["Weight"].to_dict()
    
    # Frequency and co-occurrence still come from orders (historical data)
    item_demand_freq = orders_df.groupby("ItemID").size().to_dict()
    
    # If inventory is provided, use it for total quantity (blocks needed) and effort
    if inventory_df is not None:
        item_total_inventory = inventory_df.set_index("ItemID")["Amount"].to_dict()
    else:
        # Fallback to orders if no inventory file (backward compatibility/legacy mode)
        item_total_inventory = orders_df.groupby("ItemID")["Amount"].sum().to_dict()
    
    # Calculate blocks required based on INVENTORY
    item_blocks_required = {}
    
    # We iterate over items that are in inventory OR orders (union)?
    # Logic: If item is in orders but not inventory -> We can't store it? Or assume 0?
    # Logic: If item is in inventory but not orders -> It has 0 freq, but needs storage.
    
    all_items = set(item_demand_freq.keys()) | set(item_total_inventory.keys())
    
    for item in all_items:
        # Ensure item is in demand_freq (default 0 if only in inventory)
        if item not in item_demand_freq:
            item_demand_freq[item] = 0
            
        size = item_sizes.get(item, 1) 
        inventory_amount = item_total_inventory.get(item, 0)
        
        # Only calculate if we have something to store
        if inventory_amount > 0:
            item_blocks_required[item] = int(np.ceil(inventory_amount * size / block_capacity))
        else:
            item_blocks_required[item] = 0
            
    return item_demand_freq, item_total_inventory, item_blocks_required, item_sizes, item_weight

def build_cooccurrence_matrix(orders_df):
    """
    Builds the co-occurrence matrix for items in orders.
    """
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
    return co_occurrence_pairs
