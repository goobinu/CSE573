import os
import json
from neo4j import GraphDatabase

from config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, FINAL_KNOWLEDGE_PATH, SCHEMA_CONFIG

def ingest_data():
    if not all([NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD]):
        print("Missing Neo4j credentials in config/environment variables.")
        return

    # Initialize Neo4j driver connection
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    
    file_path = FINAL_KNOWLEDGE_PATH
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return
        
    total_nodes = 0
    total_relationships = 0

    try:
        with driver.session() as session:
            for item in data:
                entities = item.get("entities", [])
                relationships = item.get("relationships", [])
                
                # Nodes: MERGE the node based on name, dynamically assign label based on type
                for entity in entities:
                    name = entity.get("name")
                    # Clean up the type to be a valid label
                    label = str(entity.get("type", "Entity")).replace(" ", "_").replace("-", "_")
                    if not label:
                        label = "Entity"
                    sentiment = entity.get("sentiment", "neutral")
                    
                    if not name:
                        continue
                        
                    if label not in SCHEMA_CONFIG["NODE_LABELS"]:
                        print(f"Skipping node '{name}': Label '{label}' not in allowed schema.")
                        continue
                        
                    query = f"""
                    MERGE (n:`{label}` {{name: $name}})
                    SET n.sentiment = $sentiment
                    """
                    session.run(query, name=name, sentiment=sentiment)
                    total_nodes += 1
                
                # Relationships: MATCH source and target by name, MERGE relationship
                for rel in relationships:
                    source = rel.get("source")
                    target = rel.get("target")
                    # Clean up the relation to be a valid cypher relation type
                    relation_type = str(rel.get("relation", "RELATED_TO")).replace(" ", "_").replace("-", "_").upper()
                    if not relation_type:
                        relation_type = "RELATED_TO"
                        
                    if not source or not target:
                        continue
                        
                    if relation_type not in SCHEMA_CONFIG["RELATIONSHIP_TYPES"]:
                        print(f"Skipping relation {source}-[{relation_type}]->{target}: Type not in allowed schema.")
                        continue
                        
                    query = f"""
                    MATCH (s {{name: $source}})
                    MATCH (t {{name: $target}})
                    MERGE (s)-[r:`{relation_type}`]->(t)
                    """
                    session.run(query, source=source, target=target)
                    total_relationships += 1
                    
        print(f"Successfully processed {len(data)} items.")
        print(f"Total node MERGE queries executed: {total_nodes}")
        print(f"Total relationship MERGE queries executed: {total_relationships}")
        
    except Exception as e:
        print(f"An error occurred during ingestion: {e}")
    finally:
        # Robustness: Ensure driver is properly closed
        driver.close()
        print("Neo4j driver connection closed.")

def init_chromadb():
    """
    Placeholder function for ChromaDB initialization.
    This is where we will embed the raw text from master_dataset_cleaned.csv.
    We aren't building the vector store yet.
    """
    pass

if __name__ == "__main__":
    ingest_data()
