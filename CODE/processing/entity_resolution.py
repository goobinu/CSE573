import json
import os
import jellyfish
from openai import OpenAI
from dotenv import load_dotenv

from config import EXTRACTED_KNOWLEDGE_PATH, FINAL_KG_PATH, VOYAGER_API_KEY, VOYAGER_BASE_URL

INPUT_FILE = EXTRACTED_KNOWLEDGE_PATH
OUTPUT_FILE = FINAL_KG_PATH

api_key = VOYAGER_API_KEY.strip().strip('"').strip("'")  # Strip spaces/quotes just in case

if not api_key.startswith("sk-"):
    raise ValueError(f"CRITICAL: API Key must start with 'sk-'. Currently it is: '{api_key[:4]}...'")

# Configure OpenAI client for ASU Voyager
client = OpenAI(
    api_key=api_key,
    base_url=VOYAGER_BASE_URL
)

def resolve_batches(uncertain_pairs):
    resolved_decisions = []
    
    # Chunking: 20 per chunk
    chunk_size = 20
    chunks = [uncertain_pairs[i:i + chunk_size] for i in range(0, len(uncertain_pairs), chunk_size)]
    
    print(f"Total uncertain pairs: {len(uncertain_pairs)}. Processing in {len(chunks)} chunks...")
    
    for c_idx, chunk in enumerate(chunks):
        print(f"Processing chunk {c_idx+1}/{len(chunks)}...")
        
        # Build prompt payload
        pairs_payload = []
        for pair in chunk:
            pairs_payload.append({
                "pair_id": pair["id"],
                "entity1": pair["e1"],
                "entity2": pair["e2"]
            })
            
        prompt = f"""Here is a JSON list of {len(chunk)} entity pairs. Identify which pairs mean the exact same thing in a business/tech context. 
Return ONLY a JSON object with a single key "results" that contains an array of objects in this format:
{{
  "results": [
    {{"pair_id": 1, "is_same": true, "canonical_name": "Best Name"}},
    ...
  ]
}}

Entity Pairs:
{json.dumps(pairs_payload, indent=2)}"""

        try:
            response = client.chat.completions.create(
                model="qwen3-235b-a22b-instruct-2507",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            
            result_str = response.choices[0].message.content
            payload = json.loads(result_str)
            
            results = payload.get("results", [])
            if isinstance(results, list):
                for res in results:
                    resolved_decisions.append(res)
            else:
                print(f"Warning: Unexpected JSON format from LLM for chunk {c_idx+1}.")
                
        except Exception as e:
            print(f"Error querying LLM for chunk {c_idx+1}: {e}")
            print("Gracefully skipping this chunk...")
            continue
            
    return resolved_decisions

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return

    print("Loading extracted knowledge...")
    with open(INPUT_FILE, "r") as f:
        data = json.load(f)

    # Pre-Processing: Apply acronyms and title casing
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

    for doc in data:
        if "entities" in doc:
            for ent in doc["entities"]:
                if "name" in ent:
                    ent["name"] = clean_name(ent["name"])
        if "relationships" in doc:
            for rel in doc["relationships"]:
                if "source" in rel:
                    rel["source"] = clean_name(rel["source"])
                if "target" in rel:
                    rel["target"] = clean_name(rel["target"])

    name_mapping = {}
    canonical_names = set()
    uncertain_pairs_raw = []

    # Phase 1: Local Exact/High-Sim Resolution
    for doc in data:
        entities = doc.get("entities", [])
        for ent in entities:
            name = ent.get("name")
            if not name or name in name_mapping:
                continue
                
            matched = False
            for c_name in list(canonical_names):
                sim = jellyfish.jaro_winkler_similarity(name.lower(), c_name.lower())
                
                if sim > 0.98:
                    name_mapping[name] = c_name
                    matched = True
                    break
                elif 0.85 <= sim <= 0.98:
                    uncertain_pairs_raw.append((name, c_name))
            
            if not matched:
                name_mapping[name] = name
                canonical_names.add(name)

    print(f"Phase 1: Resolved {len(name_mapping)} entities down to {len(canonical_names)} canonical entities locally.")
    
    uncertain_pairs = []
    for idx, (e1, e2) in enumerate(uncertain_pairs_raw):
        uncertain_pairs.append({"id": idx+1, "e1": e1, "e2": e2})
        
    # Phase 2: Batched LLM LLM Resolution
    if uncertain_pairs:
        decisions = resolve_batches(uncertain_pairs)
        
        # Apply decisions
        pair_lookup = {p["id"]: p for p in uncertain_pairs}
        
        for d in decisions:
            if d.get("is_same", False):
                pid = d.get("pair_id")
                c_name = d.get("canonical_name")
                if pid in pair_lookup:
                    e1 = pair_lookup[pid]["e1"]
                    e2 = pair_lookup[pid]["e2"]
                    
                    target_names = {name_mapping.get(e1, e1), name_mapping.get(e2, e2), e1, e2}
                    
                    for k, v in list(name_mapping.items()):
                        if v in target_names:
                            name_mapping[k] = c_name

    # Phase 3: Final Application to Data
    for doc in data:
        if "entities" in doc:
            for ent in doc["entities"]:
                old_name = ent.get("name")
                if old_name in name_mapping:
                    ent["name"] = name_mapping[old_name]
                    
            unique_ents = {}
            for ent in doc["entities"]:
                unique_ents[ent["name"]] = ent
            doc["entities"] = list(unique_ents.values())

        if "relationships" in doc:
            new_rels = []
            for rel in doc["relationships"]:
                if "source" in rel and rel["source"] in name_mapping:
                    rel["source"] = name_mapping[rel["source"]]
                if "target" in rel and rel["target"] in name_mapping:
                    rel["target"] = name_mapping[rel["target"]]
                
                # Post-Processing Filter: remove self-references
                if rel.get("source") != rel.get("target"):
                    new_rels.append(rel)
            doc["relationships"] = new_rels

    print(f"Saving normalized knowledge to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, indent=2)

    print("Normalization complete!")

if __name__ == "__main__":
    main()
