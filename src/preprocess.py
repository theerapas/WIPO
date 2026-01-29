import pandas as pd
import numpy as np
from itertools import combinations
from collections import defaultdict
import os

def load_data(orders_path, item_info_path):
    """
    Loads orders and item info from CSV (preferred) or Excel.
    """
    if orders_path.endswith(".csv"):
        orders_df = pd.read_csv(orders_path)
    else:
        orders_df = pd.read_excel(orders_path)

    if item_info_path.endswith(".csv"):
        item_info_df = pd.read_csv(item_info_path)
    else:
        item_info_df = pd.read_excel(item_info_path)
        
    return orders_df, item_info_df

def compute_demand_metrics(orders_df, item_info_df, block_capacity=60):
    """
    Computes demand metrics required for the algorithm.
    """
    # Convert to dictionaries
    item_sizes = item_info_df.set_index("ItemID")["Size"].to_dict()
    item_weight = item_info_df.set_index("ItemID")["Weight"].to_dict()
    
    item_demand_freq = orders_df.groupby("ItemID").size().to_dict()
    item_total_demand = orders_df.groupby("ItemID")["Amount"].sum().to_dict()
    
    # Calculate blocks required
    item_blocks_required = {}
    for item in item_demand_freq:
        # Fill missing size/weight with default or error? 
        # Assuming all items in orders are in item_info.
        size = item_sizes.get(item, 1) # Default to 1 if missing for safety? Or fail? The user logic assumed exist.
        demand = item_total_demand[item]
        item_blocks_required[item] = int(np.ceil(demand * size / block_capacity))
        
    return item_demand_freq, item_total_demand, item_blocks_required, item_sizes, item_weight

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
