import argparse
import subprocess
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Define the script sequences for each pipeline stage
PIPELINE_MAP = {
    "scrape": [
        "CODE/scraping/topcategoriesscraper.py",
        "CODE/scraping/resultscurator.py",
        "CODE/scraping/subpagescraping.py"
    ],
    "process": [
        "CODE/processing/ingestion.py",
        "CODE/processing/reddit_ingestion.py",
        "CODE/processing/extraction.py",
        "CODE/processing/entity_resolution.py"
    ],
    "upload": [
        "CODE/database/db_integration.py",
        "CODE/database/vector_store_setup.py"
    ]
}

def run_script(script_name):
    """Runs a Python script securely and maps its output."""
    script_path = os.path.join(SCRIPT_DIR, script_name)
    if not os.path.exists(script_path):
        print(f"❌ Error: Script not found: {script_path}")
        sys.exit(1)
        
    print(f"\n{'='*50}\n🚀 RUNNING: {script_name}\n{'='*50}")
    try:
        env = os.environ.copy()
        # Ensure scripts can import both from the root and from inside CODE/
        code_dir = os.path.join(SCRIPT_DIR, "CODE")
        env["PYTHONPATH"] = f"{SCRIPT_DIR}{os.pathsep}{code_dir}"
        # We use sys.executable to ensure the same Python environment is used
        result = subprocess.run([sys.executable, script_path], check=True, env=env)
        print(f"✅ COMPLETED: {script_name}\n{'='*50}\n")
    except subprocess.CalledProcessError as e:
        print(f"❌ FAILED: {script_name} with exit code {e.returncode}\n{'='*50}\n")
        sys.exit(e.returncode)

def run_sequence(stage_name):
    """Runs all scripts mapped to a specific stage."""
    scripts = PIPELINE_MAP.get(stage_name, [])
    for script in scripts:
        run_script(script)

def main():
    parser = argparse.ArgumentParser(description="TrendScout AI Pipeline Orchestrator")
    
    parser.add_argument('--scrape', action='store_true', help='Run the LinkedIn scraping chain')
    parser.add_argument('--process', action='store_true', help='Run the intelligence chain (extraction and resolution)')
    parser.add_argument('--upload', action='store_true', help='Run the database upload chain (Neo4j and ChromaDB)')
    parser.add_argument('--all', action='store_true', help='Run the entire pipeline from start to finish')

    args = parser.parse_args()

    # If no arguments provided
    if not any(vars(args).values()):
        parser.print_help()
        sys.exit(1)

    if args.all or args.process or args.upload:
        print("\n[Orchestrator] 🛡️ Initiating automated pre-run data backup...")
        run_script("CODE/utilities/backup_manager.py")

    if args.all or args.scrape:
        print("\n=== STARTING SCRAPE PIPELINE ===")
        run_sequence("scrape")
        
    if args.all or args.process:
        print("\n=== STARTING PROCESS PIPELINE ===")
        run_sequence("process")
        
    if args.all or args.upload:
        print("\n=== STARTING UPLOAD PIPELINE ===")
        run_sequence("upload")

    print("\n🎉 Pipeline execution finished completely!")

if __name__ == "__main__":
    main()
