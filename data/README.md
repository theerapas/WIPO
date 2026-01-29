# Data Documentation

This directory contains input data for the Warehouse Item Placement Optimization project.

## File Formats

### Item Info (`item_info.csv`)
Contains physical properties of items.
- `ItemID`: Unique identifier for the item.
- `Size`: Volume per unit.
- `Weight`: Weight per unit.

### Inventory (`sample_inventory.csv`)
**[New]** Defines storage requirements.
- `ItemID`: Item identifier.
- `Amount`: Total quantity to store in the warehouse.
- **Note**: This determines how many blocks are needed and the Handling Effort.

### Orders (`orders.csv`)
Contains historical picking data.
- `CustomerID`, `ItemID`, `Amount`.
- Used for **Frequency** and **Co-occurrence** scores (affinity).

## Note
The default configuration uses the sample CSV files in this directory. You can place your own `orders.xlsx` and `item_info.xlsx` here and update the `main.py` or arguments to use them.
