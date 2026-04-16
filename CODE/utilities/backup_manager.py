import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

def create_backup():
    """
    Creates a zip archive of the DATA/processed/ directory and saves it 
    to DATA/db_backups/ with a timestamp.
    """
    # Define paths based on the project root (assume this script is in CODE/utilities)
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    
    processed_data_dir = project_root / 'DATA' / 'processed'
    backup_dir = project_root / 'DATA' / 'db_backups'
    
    # Ensure backup directory exists
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    if not processed_data_dir.exists():
        print(f"❌ Error: Processed data directory not found at {processed_data_dir}")
        sys.exit(1)
    
    # Generate timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = backup_dir / f"backup_processed_{timestamp}"
    
    print(f"Creating backup of {processed_data_dir}...")
    
    try:
        # Create zip archive using shutil
        archive_path = shutil.make_archive(
            base_name=str(archive_name),
            format='zip',
            root_dir=str(processed_data_dir.parent),
            base_dir='processed'
        )
        print(f"✅ Success! Backup created at: {archive_path}")
    except Exception as e:
        print(f"❌ Failed to create backup. Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_backup()
