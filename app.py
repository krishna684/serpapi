# scrape.py
import os
import json
import time
import pandas as pd
from datetime import datetime
from pathlib import Path
from serpapi import GoogleSearch  # from google-search-results

# =========================
# CONFIG
# =========================
API_KEY = os.getenv("SERPAPI_API_KEY")

QUERIES = [
    "What are the symptoms of long COVID?",
    "How much vitamin D should I take daily?",
    "Can melatonin supplements improve sleep quality?",
    "Is intermittent fasting safe for people with type/2 diabetes?",
    "How long does it take to recover from hip replacement surgery??",
    "What are the side effects of flu vaccines??",
    "Can air purifiers reduce indoor allergy symptoms?",
    "How early can you detect pregnancy with a home test?",
    "Why do I get migraines after drinking wine?",
    "Is it normal to experience heart palpitations during menopause?"
    
]

LOCALES = {
      "Los_Angeles": "Los Angeles, California, United States",
  "Houston": "Houston, Texas, United States",
  "Miami": "Miami, Florida, United States",
  "New_York_City": "New York City, New York, United States"
   
}

LANGUAGES = {
    "en": "en",
    "es": "es"
}



GL = "us"
NO_CACHE = False
SLEEP_SECONDS = 2
RETRY = 2

# =========================
# Date-stamped OUT_DIR
# =========================
DATE_STR = datetime.now().strftime("%m_%d")  # e.g., "09_30"
OUT_DIR = Path(f"ai_audit_results_{DATE_STR}")
OUT_DIR.mkdir(exist_ok=True)

# =========================
# Helpers
# =========================
def _safe_join_str(xs, sep=", "):
    if isinstance(xs, (list, tuple)):
        return sep.join(str(x) for x in xs)
    return str(xs or "")

def _flatten_text_blocks(text_blocks):
    out = []
    for b in text_blocks or []:
        btype = (b.get("type") or "").strip()
        snippet = (b.get("snippet") or "").strip()
        if btype == "list":
            for it in (b.get("list") or []):
                t = (it.get("title") or "").strip()
                s = (it.get("snippet") or "").strip()
                if t:
                    out.append(f"- {t}")
                if s:
                    out.append(s)
        else:
            if snippet:
                out.append(snippet)
    return "\n".join([line for line in out if line])

def _collect_reference_indexes(text_blocks):
    s = set()
    for b in text_blocks or []:
        for i in (b.get("reference_indexes") or []):
            try:
                s.add(int(i))
            except Exception:
                pass
    return sorted(s)

def _build_reference_columns(refs, used_indexes):
    by_idx = {}
    for r in refs or []:
        idx = r.get("index")
        if idx is not None:
            try:
                by_idx[int(idx)] = r
            except Exception:
                pass

    cols = {}
    for col_i, idx in enumerate(used_indexes, start=1):
        r = by_idx.get(idx, {}) or {}
        cols[f"Reference entry {col_i}_title"]   = r.get("title", "")
        cols[f"Reference entry {col_i}_link"]    = r.get("link", "") or r.get("url", "")
        cols[f"Reference entry {col_i}_snippet"] = r.get("snippet", "")
        cols[f"Reference entry {col_i}_source"]  = r.get("source", "")
        cols[f"Reference entry {col_i}_index"]   = idx
    return cols

def _google_search(params):
    last_err = None
    for _ in range(RETRY + 1):
        try:
            return GoogleSearch(params).get_dict()
        except Exception as e:
            last_err = e
            time.sleep(1.0)
    raise last_err

# =========================
# SerpAPI fetchers
# =========================
def fetch_google_results(query, location, lang):
    return _google_search({
        "engine": "google",
        "q": query,
        "location": location,
        "gl": GL,
        "hl": lang,
        "api_key": API_KEY,
        "no_cache": str(NO_CACHE).lower()
    })

def fetch_ai_overview_detail(page_token):
    return _google_search({
        "engine": "google_ai_overview",
        "page_token": page_token,
        "api_key": API_KEY,
        "no_cache": str(NO_CACHE).lower()
    })

# =========================
# AI Overview extraction (3 paths)
# =========================
def extract_primary_ao(res):
    ao = res.get("ai_overview") or {}
    return {
        "text_blocks": ao.get("text_blocks") or [],
        "references": ao.get("references") or [],
        "snippet_highlighted_words": ao.get("snippet_highlighted_words") or [],
        "type": ao.get("type", ""),
        "page_token": ao.get("page_token"),
    }

def extract_detail_ao(detail_res):
    ao = detail_res.get("ai_overview") or {}
    return {
        "text_blocks": ao.get("text_blocks") or [],
        "references": ao.get("references") or [],
        "snippet_highlighted_words": ao.get("snippet_highlighted_words") or [],
        "type": ao.get("type", ""),
    }

def extract_embedded_ao_from_related(res):
    for rq in res.get("related_questions") or []:
        if (rq.get("type") or "").lower() == "ai_overview":
            return {
                "text_blocks": rq.get("text_blocks") or [],
                "references": rq.get("references") or [],
                "snippet_highlighted_words": rq.get("snippet_highlighted_words") or [],
                "type": rq.get("type", ""),
                "page_token": rq.get("page_token"),
            }
    return None

def combine_ao(primary, detail=None, embedded=None):
    if primary.get("text_blocks"):
        return primary
    if detail and detail.get("text_blocks"):
        if not detail.get("snippet_highlighted_words") and primary.get("snippet_highlighted_words"):
            detail["snippet_highlighted_words"] = primary["snippet_highlighted_words"]
        if not detail.get("type") and primary.get("type"):
            detail["type"] = primary["type"]
        return detail
    if embedded and embedded.get("text_blocks"):
        return embedded
    return {"text_blocks": [], "references": [], "snippet_highlighted_words": [], "type": ""}

# =========================
# Row builder
# =========================
def build_row(query, location, lang, combined_ao, raw_html_url):
    text_blocks = combined_ao.get("text_blocks", []) or []
    references  = combined_ao.get("references", [])  or []

    ai_text = _flatten_text_blocks(text_blocks)
    used_indexes = _collect_reference_indexes(text_blocks)

    row = {
        "Query_language_location": f"{query}_{lang}_{location}",
        "Raw_HTML_URL": raw_html_url or "",
        "Has_AI_Overview": bool(text_blocks),
        "Num_References_Used": len(used_indexes),
        "AI_overview_text_blocks": ai_text,
        "AI_overview_type_snippet": combined_ao.get("type", "") or "",
        "AI_overview_snippet_highlighted": _safe_join_str(combined_ao.get("snippet_highlighted_words", []) or []),
        "Reference_indexes": _safe_join_str(used_indexes),
    }
    row.update(_build_reference_columns(references, used_indexes))
    return row

# =========================
# Main
# =========================
def main():
    if not API_KEY or API_KEY == "your_serpapi_key_here":
        raise ValueError("API key is not set. In cmd: set SERPAPI_API_KEY=YOUR_KEY")

    rows = []
    json_buffer = []

    for lang_code in LANGUAGES:
        for loc_label, location in LOCALES.items():
            for query in QUERIES:
                try:
                    res_primary = fetch_google_results(query, location, lang_code)
                    primary_ao = extract_primary_ao(res_primary)

                    raw_html_url = (res_primary.get("search_metadata") or {}).get("raw_html_file", "")

                    detail_ao = None
                    if not primary_ao["text_blocks"] and primary_ao.get("page_token"):
                        try:
                            res_detail = fetch_ai_overview_detail(primary_ao["page_token"])
                            detail_ao = extract_detail_ao(res_detail)
                        except Exception as e:
                            print(f"[warn] detail fetch failed: {e}")

                    embedded_ao = extract_embedded_ao_from_related(res_primary)

                    combined_ao = combine_ao(primary_ao, detail_ao, embedded_ao)
                    rows.append(build_row(query, location, lang_code, combined_ao, raw_html_url))
                    print(f"[] {query} | {lang_code} | {loc_label}")

                    json_buffer.append({
                        "timestamp": datetime.utcnow().isoformat(),
                        "query": query,
                        "location": location,
                        "language": lang_code,
                        "ai_overview": combined_ao,
                        "raw_response": res_primary,
                        "raw_html_url": raw_html_url
                    })

                    time.sleep(SLEEP_SECONDS)
                except Exception as e:
                    print(f"[x] Error: {query} | {lang_code} | {loc_label} -> {e}")

    # 6) CSV first
    csv_filename = OUT_DIR / f"ai_audit_sum_{DATE_STR}.csv"
    pd.DataFrame(rows).to_csv(csv_filename, index=False, encoding="utf-8")
    print(f"[] CSV saved: {csv_filename}")

    # 7) JSON after CSV
    for item in json_buffer:
        label = item["query"].lower().replace("?", "").replace(" ", "_")[:40]
        loc_for_file = item["location"].replace(',', '').replace(' ', '_')
        json_filename = OUT_DIR / f"{label}_{item['language']}_{loc_for_file}_{DATE_STR}.json"
        json_filename.write_text(
            json.dumps(item, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
    print(f"[] JSON saved to: {OUT_DIR.resolve()}")

if __name__ == "__main__":
    main()
