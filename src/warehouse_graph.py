import networkx as nx

def build_warehouse_graph():
    """
    Constructs the warehouse graph topology including depot, junctions, and blocks.
    
    Returns:
        tuple: (G, depot, junctions, blocks)
            G (nx.Graph): The warehouse graph with weighted edges.
            depot (str): Node ID of the depot.
            junctions (list): List of junction node IDs.
            blocks (list): List of block node IDs.
    """
    G = nx.Graph()
    depot = "depot"
    junctions = [f"j{i}" for i in range(1, 7)]
    blocks = [f"b{i}" for i in range(1, 13)]

    # Add nodes
    G.add_node(depot, type="depot")
    for j in junctions:
        G.add_node(j, type="junction")
    for b in blocks:
        G.add_node(b, type="block")

    # Add edges (depot distance = 3)
    G.add_edge(depot, "j1", weight=3)
    G.add_edge(depot, "j4", weight=3)

    # Left side
    G.add_edge("j1", "j2", weight=1)
    G.add_edge("j2", "j3", weight=1)
    G.add_edge("j1", "b1", weight=1)
    G.add_edge("j1", "b2", weight=1)
    G.add_edge("j2", "b3", weight=1)
    G.add_edge("j2", "b4", weight=1)
    G.add_edge("j3", "b5", weight=1)
    G.add_edge("j3", "b6", weight=1)

    # Right side
    G.add_edge("j4", "j5", weight=1)
    G.add_edge("j5", "j6", weight=1)
    G.add_edge("j4", "b7", weight=1)
    G.add_edge("j4", "b8", weight=1)
    G.add_edge("j5", "b9", weight=1)
    G.add_edge("j5", "b10", weight=1)
    G.add_edge("j6", "b11", weight=1)
    G.add_edge("j6", "b12", weight=1)
    
    return G, depot, junctions, blocks
