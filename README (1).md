# AI Audit Scraper (SerpAPI + Google AI Overview)

This project fetches Google search results and AI Overview snippets for a list of health-related queries across multiple languages and locations.  
It uses [SerpAPI](https://serpapi.com/) to query Google and extract structured AI Overview responses, saving both **CSV summaries** and **detailed JSON dumps** for auditing.

---

## 🚀 Features
- Queries multiple predefined health-related questions.
- Supports multiple **locales** (Los Angeles, Houston, Miami, New York City).
- Supports multiple **languages** (`en`, `es`).
- Extracts:
  - AI Overview text blocks
  - References (titles, links, snippets, sources)
  - Highlighted snippet words
- Saves results as:
  - `ai_audit_sum_<MM_DD>.csv` (summary sheet)
  - Per-query JSON files (raw SerpAPI response + AI Overview extraction)

---

## 📂 Output
All results are stored in a date-stamped folder:
```
ai_audit_results_MM_DD/
  ├── ai_audit_sum_MM_DD.csv
  ├── what_are_the_symptoms_of_long_covid_en_Los_Angeles_MM_DD.json
  ├── ...
```

---

## ⚙️ Setup

### 1. Clone repository or copy script
```bash
git clone <your_repo_url>
cd <your_repo>
```

### 2. Create and activate a virtual environment
It is strongly recommended to use a virtual environment to keep dependencies isolated.

**On Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows (PowerShell):**
```powershell
python -m venv venv
.env\Scriptsctivate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set environment variable
You must export your [SerpAPI API key](https://serpapi.com/manage-api-key):

**Linux/macOS**
```bash
export SERPAPI_API_KEY="your_serpapi_key_here"
```

**Windows PowerShell**
```powershell
setx SERPAPI_API_KEY "your_serpapi_key_here"
```

### 5. Run script
```bash
python test.py
```

---

## ⚠️ Notes
- Script retries failed requests up to `RETRY=2` times.
- Rate limiting: waits `SLEEP_SECONDS=2` between calls (adjustable).
- If the API key is missing, the script will raise:
  ```
  ValueError: API key is not set. In cmd: set SERPAPI_API_KEY=YOUR_KEY
  ```

---

## 📦 Dependencies
All dependencies are listed in [`requirements.txt`](./requirements.txt).  
Key external libraries include:
- `pandas` (data handling, CSV writing)
- `numpy` (required by pandas)
- `serpapi` (API client for Google search results)
- `requests` (HTTP requests used internally by serpapi)

---

## 📜 License
MIT (or your preferred license)
