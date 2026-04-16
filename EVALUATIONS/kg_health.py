import os
import sys
import argparse
from datetime import datetime
from neo4j import GraphDatabase

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD

def run_metrics(output_dir):
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    metrics = []

    with driver.session() as session:
        # Node Count
        result = session.run("MATCH (n) RETURN count(n) AS v")
        v = result.single()["v"]
        metrics.append(f"Total Nodes (V): {v}")

        # Relationship Count
        result = session.run("MATCH ()-[r]->() RETURN count(r) AS e")
        e = result.single()["e"]
        metrics.append(f"Total Relationships (E): {e}")

        # Graph Density: 2E / (V * (V-1))
        density = (2 * e) / (v * (v - 1)) if v > 1 else 0
        metrics.append(f"Graph Density: {density:.6f}")

        # Isolated Nodes
        result = session.run("MATCH (n) WHERE NOT (n)--() RETURN count(n) AS iso")
        iso = result.single()["iso"]
        metrics.append(f"Isolated Nodes: {iso}")

        # Connectivity Ratio: (V - Isolated) / V
        conn_ratio = (v - iso) / v if v > 0 else 0
        metrics.append(f"Connectivity Ratio: {conn_ratio:.4f}")

        # Average Clustering Coefficient (Approximation using Vanilla Cypher)
        # Triangles: A-B, B-C, C-A 
        cypher_triangles = """
        MATCH (a)-[]-(b)-[]-(c)-[]-(a)
        WHERE id(a) < id(b) AND id(b) < id(c)
        RETURN count(*) AS triangles
        """
        result = session.run(cypher_triangles)
        triangles = result.single()["triangles"]
        
        # Triplets: A-B, B-C (Connected nodes of length 2)
        cypher_triplets = """
        MATCH (a)-[]-(b)-[]-(c)
        WHERE id(a) < id(c)
        RETURN count(*) AS triplets
        """
        result = session.run(cypher_triplets)
        triplets = result.single()["triplets"]
        
        # global clustering coefficient = 3 * triangles / triplets
        cc = (3.0 * triangles) / triplets if triplets > 0 else 0
        metrics.append(f"Triplets: {triplets}")
        metrics.append(f"Triangles: {triangles}")
        metrics.append(f"Global Clustering Coefficient (Approximate): {cc:.6f}")

    driver.close()

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "graph_metrics.txt")
    
    with open(output_path, "w") as f:
        f.write("=== NEO4J GRAPH HEALTH METRICS ===\n")
        f.write("\n".join(metrics))
    
    print(f"Graph metrics successfully written to {output_path}")
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    run_metrics(args.output_dir)
