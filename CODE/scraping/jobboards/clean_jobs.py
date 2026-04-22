"""
Merge, normalise, and deduplicate Wellfound + Greenhouse job data.
Reads:   DATA/raw/jobboards/jobs_list.csv  (Wellfound)  — or greenhouse fallback
         DATA/raw/jobboards/job_details.csv              — or greenhouse fallback
Outputs: DATA/raw/jobboards/jobs_master.csv
"""
import re
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

# ── Paths ─────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent  # CSE573/
RAW_DIR = PROJECT_ROOT / "DATA" / "raw" / "jobboards"
RAW_DIR.mkdir(parents=True, exist_ok=True)

JOBS_FILE = RAW_DIR / "jobs_list.csv"
DETAILS_FILE = RAW_DIR / "job_details.csv"
FALLBACK_JOBS_FILE = RAW_DIR / "greenhouse_jobs_list.csv"
FALLBACK_DETAILS_FILE = RAW_DIR / "greenhouse_job_details.csv"

# ── Normalisation helpers ──────────────────────────────────────────────────────
COMPANY_SUFFIXES = re.compile(
    r"\b(?:inc|inc\.|corp|corp\.|corporation|llc|ltd|limited|gmbh|plc|llp|sarl|ag|co|co\.)\b\.?\,?",
    re.I,
)

KNOWN_BRANDS = {
    "xai": "xAI", "aws": "AWS", "gcp": "GCP", "ml": "ML",
    "llm": "LLM", "ai": "AI", "nlp": "NLP", "ios": "iOS",
    "ux": "UX", "ui": "UI",
}


def normalize_text(text):
    if pd.isna(text):
        return None
    text = str(text).strip()
    text = re.sub(r"\s+", " ", text)
    return text or None


def normalize_company(company):
    company = normalize_text(company)
    if not company:
        return None
    company = COMPANY_SUFFIXES.sub("", company)
    company = re.sub(r"[\(\)\[\]]", "", company)
    company = re.sub(r"\s{2,}", " ", company).strip(" .,-")
    tokens = []
    for token in company.split():
        lower = token.lower().strip(".,")
        if lower in KNOWN_BRANDS:
            tokens.append(KNOWN_BRANDS[lower])
        elif token.isupper() and len(token) <= 4:
            tokens.append(token)
        else:
            tokens.append(token.capitalize())
    return " ".join(tokens) or company


def normalize_title(title):
    title = normalize_text(title)
    if not title:
        return None
    title = title.replace("/", " / ")
    title = re.sub(r"\s{2,}", " ", title)
    tokens = []
    for token in title.split():
        lower = token.lower().strip(".,")
        tokens.append(KNOWN_BRANDS.get(lower, token.capitalize()))
    return " ".join(tokens)


def normalize_location(location):
    location = normalize_text(location)
    if not location:
        return None
    location = re.sub(r"\s*;\s*", "; ", location)
    location = re.sub(r"\s*,\s*", ", ", location)
    return location


def normalize_employment_type(employment_type):
    employment_type = normalize_text(employment_type)
    if not employment_type:
        return None
    et = employment_type.lower()
    if "full" in et and "time" in et:
        return "Full-time"
    if "part" in et and "time" in et:
        return "Part-time"
    if "contract" in et:
        return "Contract"
    if "intern" in et:
        return "Internship"
    if "remote" in et:
        return "Remote"
    return employment_type.title()


def parse_salary(salary):
    salary = normalize_text(salary)
    if not salary:
        return None, None, None, None
    salary = salary.replace("—", "-").replace("–", "-")
    salary = re.sub(r"\s+", " ", salary)
    pattern = re.compile(
        r"(?P<currency>\$|USD|usd|EUR|€|GBP|£)?\s*(?P<min>\d{1,3}(?:[\d,]*)(?:\.\d+)?\s*[kKmM]?)"
        r"(?:\s*[-–to]+\s*(?P<max>\$?\s*\d{1,3}(?:[\d,]*)(?:\.\d+)?\s*[kKmM]?))?",
        re.I,
    )
    match = pattern.search(salary)
    if not match:
        return salary, None, None, None
    currency = match.group("currency") or ""
    min_value = _to_numeric(match.group("min"))
    max_value = _to_numeric(match.group("max")) if match.group("max") else None
    if min_value is None:
        return salary, None, None, None
    formatted = _fmt(min_value, currency)
    if max_value is not None:
        formatted = f"{formatted} - {_fmt(max_value, currency)}"
    return formatted, min_value, max_value, currency.strip().upper() if currency else None


def _to_numeric(value):
    if not value:
        return None
    value = value.strip().replace(",", "")
    multiplier = 1
    if value[-1].lower() == "k":
        multiplier = 1000
        value = value[:-1]
    elif value[-1].lower() == "m":
        multiplier = 1_000_000
        value = value[:-1]
    try:
        return int(float(value) * multiplier)
    except ValueError:
        return None


def _fmt(value, currency):
    text = f"{value:,}"
    if currency == "$":
        return f"${text}"
    if currency.upper() == "USD":
        return f"USD {text}"
    if currency.upper() in {"EUR", "€"}:
        return f"€{text}"
    if currency.upper() in {"GBP", "£"}:
        return f"£{text}"
    return text


def infer_company_from_url(url):
    if not isinstance(url, str):
        return None
    try:
        path = urlparse(url).path
    except Exception:
        return None
    parts = [p for p in path.split("/") if p]
    if "companies" in parts:
        idx = parts.index("companies")
        if idx + 1 < len(parts):
            return normalize_company(parts[idx + 1].replace("-", " "))
    for part in parts:
        if part and part.lower() not in {"jobs", "remote"}:
            return normalize_company(part.replace("-", " "))
    return None


def deduce_role_category(title):
    if not isinstance(title, str):
        return "Other"
    t = title.lower()
    if "machine learning" in t or "ml engineer" in t:
        return "ML Engineer"
    if "data scientist" in t:
        return "Data Scientist"
    if "software engineer" in t or "backend" in t or "frontend" in t or "full stack" in t:
        return "Software Engineer"
    if "research engineer" in t or "research scientist" in t:
        return "AI Research"
    if "product manager" in t:
        return "Product"
    if "designer" in t:
        return "Design"
    if "devops" in t or "platform" in t or "infra" in t or "infrastructure" in t:
        return "Infrastructure"
    if "data center" in t or "datacenter" in t:
        return "Data Center"
    return "Other"


def load_jobs():
    if JOBS_FILE.exists() and JOBS_FILE.stat().st_size > 0:
        try:
            return pd.read_csv(JOBS_FILE)
        except pd.errors.EmptyDataError:
            pass
    if FALLBACK_JOBS_FILE.exists() and FALLBACK_JOBS_FILE.stat().st_size > 0:
        print("Warning: jobs_list.csv missing or empty — using greenhouse_jobs_list.csv fallback.")
        return pd.read_csv(FALLBACK_JOBS_FILE)
    raise FileNotFoundError(f"Missing both {JOBS_FILE} and {FALLBACK_JOBS_FILE}.")


def load_details():
    if DETAILS_FILE.exists() and DETAILS_FILE.stat().st_size > 0:
        try:
            return pd.read_csv(DETAILS_FILE)
        except pd.errors.EmptyDataError:
            pass
    if FALLBACK_DETAILS_FILE.exists() and FALLBACK_DETAILS_FILE.stat().st_size > 0:
        print("Warning: job_details.csv missing or empty — using greenhouse_job_details.csv fallback.")
        return pd.read_csv(FALLBACK_DETAILS_FILE)
    raise FileNotFoundError(f"Missing both {DETAILS_FILE} and {FALLBACK_DETAILS_FILE}.")


def clean_jobs():
    jobs = load_jobs()
    details = load_details()

    if "source" not in jobs.columns:
        jobs["source"] = None
    if "scraped_at" not in jobs.columns:
        jobs["scraped_at"] = None

    df = jobs.merge(details, on="job_url", how="left")

    for col in ["title", "company", "location", "description", "salary", "employment_type"]:
        if col in df.columns:
            df[col] = df[col].apply(normalize_text)

    df["company"] = df.apply(
        lambda row: normalize_company(row["company"]) or infer_company_from_url(row.get("job_url", "")),
        axis=1,
    )
    if "title" in df.columns:
        df["title"] = df["title"].apply(normalize_title)
    if "location" in df.columns:
        df["location"] = df["location"].apply(normalize_location)
    if "employment_type" in df.columns:
        df["employment_type"] = df["employment_type"].apply(normalize_employment_type)

    salary_parsed = pd.DataFrame(
        [parse_salary(x) for x in df["salary"]] if "salary" in df.columns else [],
        columns=["salary_normalized", "salary_min", "salary_max", "salary_currency"],
    )
    if not salary_parsed.empty:
        df = pd.concat([df.reset_index(drop=True), salary_parsed.reset_index(drop=True)], axis=1)
    else:
        df[["salary_normalized", "salary_min", "salary_max", "salary_currency"]] = None

    df["role_category"] = df["title"].apply(deduce_role_category)
    df["dedup_key"] = (
        df["company"].fillna("") + "|" + df["title"].fillna("") + "|" + df["job_url"].fillna("")
    ).str.lower()
    df = df.drop_duplicates(subset=["dedup_key"])

    output_file = RAW_DIR / "jobs_master.csv"
    df.to_csv(output_file, index=False, encoding="utf-8")
    print(f"Saved cleaned dataset with {len(df)} rows to {output_file}.")
    return df


if __name__ == "__main__":
    clean_jobs()
