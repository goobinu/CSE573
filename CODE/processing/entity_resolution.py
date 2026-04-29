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

def resolve_batches(uncertain_pairs, checkpoint_state, checkpoint_file):
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
                    pid = res.get("pair_id")
                    pair = next((p for p in chunk if p["id"] == pid), None)
                    if pair:
                        decision_record = {
                            "is_same": res.get("is_same", False),
                            "canonical_name": res.get("canonical_name"),
                            "e1": pair["e1"],
                            "e2": pair["e2"]
                        }
                        resolved_decisions.append(decision_record)
                        
                        pair_key = f"{pair['e1']}|||{pair['e2']}"
                        checkpoint_state[pair_key] = decision_record
                
                with open(checkpoint_file, "w") as f:
                    json.dump(checkpoint_state, f, indent=2)
                print(f"💾 Checkpoint saved: {len(checkpoint_state)} total entities resolved.")
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
    # First, collect ALL unique names from the entire dataset to avoid redundant N^2 comparisons
    all_raw_names = set()
    for doc in data:
        for ent in doc.get("entities", []):
            if ent.get("name"):
                all_raw_names.add(ent["name"])
    
    print(f"Phase 1: Found {len(all_raw_names)} unique entity names to resolve.")
    
    from tqdm import tqdm
    name_mapping = {}
    canonical_names = []
    uncertain_pairs_raw = []

    # Sort names by length (longer names first often make better canonical names)
    sorted_names = sorted(list(all_raw_names), key=len, reverse=True)

    for name in tqdm(sorted_names, desc="Resolving Entities Locally"):
        if name in name_mapping:
            continue
            
        matched = False
        # Only compare against existing canonical names
        for c_name in canonical_names:
            # Quick check: if lengths are wildly different, jaro-winkler won't be high
            if abs(len(name) - len(c_name)) > 10:
                continue
                
            sim = jellyfish.jaro_winkler_similarity(name.lower(), c_name.lower())
            
            if sim > 0.98:
                name_mapping[name] = c_name
                matched = True
                break
            elif 0.85 <= sim <= 0.98:
                uncertain_pairs_raw.append((name, c_name))
        
        if not matched:
            name_mapping[name] = name
            canonical_names.append(name)

    print(f"Phase 1: Resolved {len(all_raw_names)} names down to {len(canonical_names)} canonical entities locally.")
    
    # State Initialization & Recovery
    from utilities.checkpoint_manager import CheckpointManager
    # We use INPUT_FILE as the source to track if extraction data changed
    checkpoint_mgr = CheckpointManager("entity_resolution", INPUT_FILE)
    
    # We need to save the entire dictionary of decisions, so we'll slightly adapt usage
    # or just use it to track if we've completed the phase.
    # For now, let's keep the existing checkpoint file path but use the manager's logic if possible.
    # Actually, the existing logic in entity_resolution is quite specific to the pair_key mapping.
    
    checkpoint_file = checkpoint_mgr.checkpoint_path
    checkpoint_state = {}
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, "r") as f:
            checkpoint_state = json.load(f)
        # Check if hash matches
        if checkpoint_state.get("source_hash") != checkpoint_mgr.source_hash:
            print("⚠️ Source file changed. Resetting checkpoint.")
            checkpoint_state = {}
        else:
            print(f"Loaded {len(checkpoint_state) - 1} previously resolved pairs from checkpoint.")
    
    # Filter Workload
    remaining_pairs_raw = []
    decisions = []
    
    for e1, e2 in uncertain_pairs_raw:
        pair_key = f"{e1}|||{e2}"
        if pair_key in checkpoint_state:
            decisions.append(checkpoint_state[pair_key])
        else:
            remaining_pairs_raw.append((e1, e2))

    uncertain_pairs = []
    for idx, (e1, e2) in enumerate(remaining_pairs_raw):
        uncertain_pairs.append({"id": idx+1, "e1": e1, "e2": e2})
        
    print(f"{len(uncertain_pairs)} pairs remaining to be processed by LLM.")

    # Phase 2: Batched LLM Resolution
    if uncertain_pairs:
        # We pass the checkpoint_mgr.save_checkpoint logic indirectly or update resolve_batches
        def save_state(state):
            state["source_hash"] = checkpoint_mgr.source_hash
            with open(checkpoint_file, "w") as f:
                json.dump(state, f, indent=2)

        # Update resolve_batches to use this
        new_decisions = resolve_batches(uncertain_pairs, checkpoint_state, checkpoint_file)
        decisions.extend(new_decisions)
        
    # Apply decisions
    for d in decisions:
        if d.get("is_same", False):
            e1 = d.get("e1")
            e2 = d.get("e2")
            c_name = d.get("canonical_name")
            
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

    if os.path.exists(checkpoint_file):
        os.remove(checkpoint_file)
        print("Removed checkpoint file as processing is complete.")

if __name__ == "__main__":
    main()
