import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(SCRIPT_DIR, "data", "normalized_knowledge.json")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "data", "final_knowledge_graph.json")

ACRONYMS = {
    "LLM": "Large Language Models",
    "LLMS": "Large Language Models",
    "AI": "Artificial Intelligence",
    "GENAI": "Generative AI",
    "RAG": "Retrieval-Augmented Generation",
    "ML": "Machine Learning",
    "NLP": "Natural Language Processing"
}

import re

def clean_name(name):
    if not name:
        return name
    upper_name = str(name).strip().upper()
    if upper_name in ACRONYMS:
        name = ACRONYMS[upper_name]
    
    name = str(name).title()
    
    # Fix specific casing issues caused by .title()
    name = re.sub(r'\bAi\b', 'AI', name)
    name = re.sub(r'\bOpenai\b', 'OpenAI', name)
    name = re.sub(r'\bGenai\b', 'GenAI', name)
    name = re.sub(r'\bLlm\b', 'LLM', name)
    name = re.sub(r'\bLlms\b', 'LLMs', name)
    name = re.sub(r'\bNlp\b', 'NLP', name)
    name = re.sub(r'\bMl\b', 'ML', name)
    name = re.sub(r'\bRag\b', 'RAG', name)
    
    return name

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return

    print("Loading normalized knowledge...")
    with open(INPUT_FILE, "r") as f:
        data = json.load(f)

    for doc in data:
        # Update entities
        if "entities" in doc:
            for ent in doc["entities"]:
                if "name" in ent:
                    ent["name"] = clean_name(ent["name"])

            # Deduplicate in case casing caused collisions
            unique_ents = {}
            for ent in doc["entities"]:
                unique_ents[ent["name"]] = ent
            doc["entities"] = list(unique_ents.values())

        # Update relationships
        if "relationships" in doc:
            new_rels = []
            for rel in doc["relationships"]:
                source = clean_name(rel.get("source", ""))
                target = clean_name(rel.get("target", ""))
                
                rel["source"] = source
                rel["target"] = target
                
                # Filter out self-references
                if source and target and source != target:
                    new_rels.append(rel)
            
            doc["relationships"] = new_rels

    print(f"Saving final knowledge graph to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, indent=2)

    print("Post-processing complete!")

if __name__ == "__main__":
    main()
