import pandas as pd
from itertools import combinations
from collections import Counter

# Load Excel file
df = pd.read_excel("RealWearhouseOrder.xlsx")

# ------------------------------
# Part 1: Item Frequency
# ------------------------------
item_frequency = df['ItemID'].value_counts().reset_index()
item_frequency.columns = ['ItemID', 'Frequency']

# Optional: Save to CSV
item_frequency.to_csv("item_frequency.csv", index=False)

# ------------------------------
# Part 2: Item Co-Occurrence
# ------------------------------

# Group by Date and CustomerID to form each "set of order"
grouped_orders = df.groupby(['Date', 'CustomerID'])['ItemID'].apply(list)

# Count co-occurrence pairs
co_occurrence_counter = Counter()
for item_list in grouped_orders:
    unique_items = set(item_list)  # Avoid duplicate items in the same order
    for item_pair in combinations(sorted(unique_items), 2):
        co_occurrence_counter[item_pair] += 1

# Convert to DataFrame
co_occurrence_df = pd.DataFrame(
    [(a, b, count) for (a, b), count in co_occurrence_counter.items()],
    columns=['ItemA', 'ItemB', 'CoOccurrence']
)

# Optional: Save to CSV
co_occurrence_df.to_csv("item_co_occurrence.csv", index=False)
