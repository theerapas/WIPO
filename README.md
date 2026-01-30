# Warehouse Item Placement Optimization

This project implements a graph-based optimization algorithm for assigning items to warehouse storage blocks. The goal is to minimize total walking distance for order picking and ensure balanced handling effort.

## Overview
Efficient warehouse layout is critical for reducing operational costs. This repository contains a Python implementation of a dynamic greedy heuristic that assigns items to storage blocks based on:
1. **Demand Frequency**: High-demand items are placed closer to the depot.
2. **Co-occurrence**: Items frequently ordered together are placed near each other to minimize travel between picks.

## Problem Formulation
- **Warehouse Layout**: Modeled as a graph with a central **Depot**, **Junctions**, and storage **Blocks**.
- **Nodes**:
  - `Depot`: Starting and ending point of all picking routes.
  - `Blocks`: Storage locations with fixed capacity.
  - `Junctions`: Intermediary points connecting blocks and the depot.
- **Objective**:
  - Minimize **Walking Distance** (sum of path lengths for all orders).
  - Balance **Handling Effort** (workload distribution across blocks).

## Algorithm Logic
The solution uses a **Dynamic Greedy Approach** with two key scoring metrics:

### 1. Placement Priority Score (PPS)
Determines *which item to place next*.
$$ PPS(i) = w_{\text{freq}} \cdot \frac{d_i \cdot w_i}{\max\limits_{j\in I} (d_j \cdot w_j)} + w_{\text{cooc}} \cdot \frac{\sum\limits_{j \in I_{placed}}  co(i, j)}{\max\limits_{k\in I} \sum\limits_{j \in I, j \neq k}  co(k, j)} $$
- Prioritizes items with high demand and high total co-occurrence with already placed items.
- Dynamic: Scores update as more items are placed.

### 2. Location Cost Score (LCS)
Determines *where to place the selected item*.
$$ LCS(i, b) = w_{\text{depot}} \cdot \frac{\text{Dist}(\text{Depot}, b) \cdot w_i}{k_i} + w_{\text{affinity}} \cdot \sum\limits_{j \in I_{\text{placed}}} co(i, j) \cdot \text{Dist}(b, b'_j) $$
- Selects the block `b` that minimizes this cost.
- Balances proximity to depot (for heavy/frequent items) and proximity to related items (affinity).

**Process Loop**:
1. Calculate PPS for all unplaced items.
2. Pick item with highest PPS.
3. Calculate LCS for all available blocks.
4. Assign item to block with lowest LCS.
5. Repeat until all items are placed or blocks are full.

## Modeling Assumptions
1. **Graph Topology**: Distances are fixed weights on edges (e.g., Depot-Junction=3, Junction-Block=1).
2. **Block Capacity**: Each block has a fixed volume capacity (default: 60 units).
3. **Picking Strategy**: Pickers visit assigned blocks using a **Nearest Neighbor TSP** heuristic to minimize travel distance within each order.
4. **Order Batching**: Orders are processed individually (no batching).

## Evaluation Metrics
1. **Total Walking Distance**: The sum of travel distances for all historical orders.
2. **Handling Effort**: A proxy for workload, calculated as:
   $$ Effort = \sum (Weight_i \times Amount_{block} \times Dist(Depot, Block)) $$
   Low handling effort implies heavy traffic is minimized and heavy items are easy to access.

## Reproducibility Note
- **Customer ID Sorting**: Customer IDs are processed in **natural numerical order** (e.g., P1, P2, ..., P9, P10) rather than lexicographical order. This ensures consistent evaluation as inventory is depleted sequentially.


## How to Run

### Prerequisites
- Python 3.8+
- Recommended: `pip install -r requirements.txt`

### Steps
1. **Clone the repository**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the optimization**:
   ```bash
   python src/main.py
   ```
   
   The script will:
   - Load data from `data/sample_orders.csv` and `data/sample_item_info.csv`.
   - Build the warehouse graph.
   - Run the placement algorithm.
   - Output results to console and `results/` directory.

## Results
Outputs are saved in the `results/` directory:
- `assignment.json`: Mapping of Block ID to Item ID.
- `metrics.csv`: calculated Totals for Walking Distance and Handling Effort.

### Example Output
```
Total Walking Distance: 145.00
Total Handling Effort:  320.00
```

## Limitations
- **Greedy Heuristic**: Does not guarantee a global optimum.
- **Static Placement**: Does not account for seasonal trends or changing demand over time.
- **Simplified Routing**: Actual picking routes might be more complex (TSP).

## Future Improvements
- Implement simulated annealing or genetic algorithms for comparison.
- Add support for different picking strategies (S-shape, midpoint).
- Visualize the warehouse graph and heatmaps of block activity.

## License
MIT License.
