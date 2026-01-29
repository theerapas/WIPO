import networkx as nx

def build_warehouse_graph(layout_data):
    """
    Constructs the warehouse graph topology from a layout dictionary.
    
    Args:
        layout_data (dict): Dictionary containing 'nodes' and 'edges'.
        
    Returns:
        tuple: (G, depot, junctions, blocks)
            G (nx.Graph): The warehouse graph with weighted edges.
            depot (str): Node ID of the depot.
            junctions (list): List of junction node IDs.
            blocks (list): List of block node IDs.
    """
    G = nx.Graph()
    depot = None
    junctions = []
    blocks = []
    
    # Add nodes
    for node in layout_data["nodes"]:
        nid = node["id"]
        ntype = node["type"]
        G.add_node(nid, type=ntype)
        
        if ntype == "depot":
            depot = nid
        elif ntype == "junction":
            junctions.append(nid)
        elif ntype == "block":
            blocks.append(nid)
            
    # Add edges
    for edge in layout_data["edges"]:
        G.add_edge(edge["source"], edge["target"], weight=edge["weight"])
        
    return G, depot, junctions, blocks
