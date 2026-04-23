"""
Convert YC AI Companies CSV to JSON format
"""

import csv
import json
from pathlib import Path

def csv_to_json(csv_file: str, json_file: str, format_type: str = "array"):
    """
    Convert CSV to JSON
    
    Args:
        csv_file: Path to CSV file
        json_file: Path to output JSON file
        format_type: "array" for list of objects, "keyed" for dict by company name
    """
    companies = []
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert empty strings to None for cleaner JSON
            company = {k: (None if v == "" else v) for k, v in row.items()}
            companies.append(company)
    
    if format_type == "array":
        # List of company objects
        data = companies
    elif format_type == "keyed":
        # Dictionary keyed by company name
        data = {company['name']: company for company in companies}
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Converted {len(companies)} companies")
    print(f"Saved to: {json_file}")
    print(f"Format: {format_type}")

if __name__ == "__main__":
    csv_path = "data/yc_ai_companies.csv"
    
    # Create array format (list of objects) NOTE: chhnge path according to your local directory
    csv_to_json(csv_path, "data/yc_ai_companies.json", format_type="array")
    
    # Optionally create keyed format (dict by name) NOTE: chhnge path according to your local directory
    csv_to_json(csv_path, "data/yc_ai_companies_keyed.json", format_type="keyed")
