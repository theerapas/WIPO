# Data Documentation

This directory contains input data for the Warehouse Item Placement Optimization project.

## File Formats

### Item Info (`item_info.csv` or `sample_item_info.csv`)
Contains physical properties of items.
- `ItemID`: Unique identifier for the item (string).
- `Size`: Volume or space occupied by one unit of the item (numeric).
- `Weight`: Weight of one unit of the item (numeric).

### Orders (`orders.csv` or `sample_orders.csv`)
Contains historical order data for demand analysis.
- `CustomerID`: Unique identifier for the customer/order (string).
- `ItemID`: Identifier of the item ordered (must match `item_info.csv`).
- `Amount`: Quantity of the item ordered (integer).

## Note
The default configuration uses the sample CSV files in this directory. You can place your own `orders.xlsx` and `item_info.xlsx` here and update the `main.py` or arguments to use them.
