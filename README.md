# CSE573
This repo will host my project code for the ASU course CSE 573.

## Setup & Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd CSE573
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install Playwright browsers:**
    ```bash
    playwright install
    ```

## Usage

To run the scrapers:

```bash
python topcategoriesscraper.py
# or
python subpagescraping.py
```

