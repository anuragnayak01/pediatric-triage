import hashlib
import json
import re
from pathlib import Path

import fitz
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "data" / "processed"
CHUNKS_PATH = OUT_DIR / "chunks.jsonl"
INVENTORY_PATH = OUT_DIR / "source_inventory.json"

SOURCE_URLS = {
    "WHO_ETAT_2005.pdf": "https://iris.who.int/bitstream/handle/10665/43386/9241546875_eng.pdf",
    "WHO_Pediatric_ETAT_2016.pdf": "https://iris.who.int/handle/10665/204463",
    "ESI_v4_Handbook.pdf": "https://esitriage.org/handbook.asp",
    "AAP_Fever_When_To_Call.html": "https://www.healthychildren.org/English/health-issues/conditions/fever/Pages/When-to-Call-the-Pediatrician.aspx",
    "Mayo_Fever_Children.html": "https://www.mayoclinic.org/symptom-checker/fever-in-children-child/related-factors/itt-20009075",
    "Mayo_Sick_Baby.html": "https://www.mayoclinic.org/health/healthy-baby/PR00022/",
    "Mayo_Vomiting_Children.html": "https://www.mayoclinic.org/symptom-checker/nausea-or-vomiting-in-children-child/related-factors/itt-20009075",
}

SOURCE_NAMES = {
    "WHO_ETAT_2005.pdf": "WHO ETAT Manual",
    "WHO_Pediatric_ETAT_2016.pdf": "WHO Paediatric ETAT Updated Guideline",
    "ESI_v4_Handbook.pdf": "Emergency Severity Index v4 Handbook",
    "AAP_Fever_When_To_Call.html": "HealthyChildren / AAP Fever Guidance",
    "Mayo_Fever_Children.html": "Mayo Clinic Fever in Children",
    "Mayo_Sick_Baby.html": "Mayo Clinic Sick Baby",
    "Mayo_Vomiting_Children.html": "Mayo Clinic Nausea or Vomiting in Children",
}

TOPIC_KEYWORDS = {
    "breathing": ["breath", "airway", "respiratory", "blue lips", "cyanosis", "choking"],
    "seizure_consciousness": ["seizure", "convulsion", "unconscious", "letharg", "cannot be awakened", "coma"],
    "fever": ["fever", "temperature", "100.4", "38", "104", "40"],
    "dehydration": ["dehydrat", "wet diaper", "urine", "tears", "dry mouth", "sunken"],
    "vomiting_diarrhea": ["vomit", "nausea", "diarrhea", "stool"],
    "rash_stiff_neck": ["rash", "stiff neck", "neck"],
    "trauma_poisoning": ["burn", "bleeding", "poison", "injury", "head injury"],
    "triage_framework": ["triage", "severity", "acuity", "priority", "emergency signs"],
}


def clean_text(text: str) -> str:
    text = re.sub(r"-\s*\n\s*", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def prune_boilerplate(text: str) -> str:
    noisy_phrases = [
        "Cookies on mayoclinic.org",
        "Customize cookie preferences",
        "Accept additional cookies",
        "Reject additional cookies",
        "Manage cookie preferences",
        "Strictly necessary cookies",
        "Functional and Analytical Cookies",
        "Advertising Cookies",
        "Mayo Clinic does not endorse companies or products",
        "Advertising revenue supports our not-for-profit mission",
        "Skip to main content",
        "Enable accessibility",
        "Open the accessibility menu",
        "Log in | Register",
        "Our Sponsors",
        "Donate",
    ]
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            lines.append("")
            continue
        if any(phrase.lower() in stripped.lower() for phrase in noisy_phrases):
            continue
        if len(stripped) < 3:
            continue
        lines.append(stripped)
    return clean_text("\n".join(lines))


def stable_id(*parts: str) -> str:
    raw = "::".join(str(part) for part in parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def words(text: str) -> list[str]:
    return re.findall(r"\S+", text)


def split_recursive(text: str, max_words: int = 700, overlap: int = 80) -> list[str]:
    tokens = words(text)
    if len(tokens) <= max_words:
        return [text.strip()]

    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + max_words, len(tokens))
        chunks.append(" ".join(tokens[start:end]))
        if end == len(tokens):
            break
        start = max(0, end - overlap)
    return chunks


def looks_like_heading(line: str) -> bool:
    line = line.strip()
    if not line or len(line) > 120:
        return False
    if re.match(r"^(chapter|section|part)\s+\d+", line, re.I):
        return True
    if re.match(r"^\d+(\.\d+)*\s+[A-Z]", line):
        return True
    if line.isupper() and len(line.split()) <= 12:
        return True
    return False


def structural_sections(page_texts: list[dict]) -> list[dict]:
    sections = []
    current = {
        "title": "Document introduction",
        "page_start": page_texts[0]["page"] if page_texts else None,
        "page_end": page_texts[0]["page"] if page_texts else None,
        "lines": [],
    }

    for page in page_texts:
        current["page_end"] = page["page"]
        for line in page["text"].splitlines():
            line = line.strip()
            if not line:
                current["lines"].append("")
                continue
            if looks_like_heading(line) and len(" ".join(current["lines"]).split()) > 80:
                sections.append(current)
                current = {
                    "title": line,
                    "page_start": page["page"],
                    "page_end": page["page"],
                    "lines": [],
                }
            else:
                current["lines"].append(line)

    if current["lines"]:
        sections.append(current)
    return sections


def infer_topic(text: str) -> str:
    lower = text.lower()
    scores = {
        topic: sum(1 for keyword in keywords if keyword in lower)
        for topic, keywords in TOPIC_KEYWORDS.items()
    }
    best = max(scores, key=scores.get)
    return best if scores[best] else "general"


def infer_severity(text: str) -> str:
    lower = text.lower()
    emergency_terms = ["emergency", "immediate", "blue lips", "stopped breathing", "seizure", "unconscious", "poison", "heavy bleeding"]
    see_doctor_terms = ["call your doctor", "call the doctor", "pediatrician", "100.4", "38", "dehydration", "not keeping liquids"]
    mild_terms = ["home", "playing", "alert", "mild", "self-care"]
    if any(term in lower for term in emergency_terms):
        return "emergency"
    if any(term in lower for term in see_doctor_terms):
        return "see-doctor"
    if any(term in lower for term in mild_terms):
        return "mild"
    return "mixed"


def source_type(path: Path) -> str:
    if "clinical_guidelines" in path.parts:
        if path.name.startswith("ESI"):
            return "triage_framework"
        return "clinical_guideline"
    return "parent_guidance"


def extract_pdf(path: Path) -> tuple[list[dict], dict]:
    doc = fitz.open(path)
    pages = []
    char_counts = []
    for index in range(doc.page_count):
        text = clean_text(doc.load_page(index).get_text("text"))
        char_counts.append(len(text))
        if text:
            pages.append({"page": index + 1, "text": text})
    inventory = {
        "source_file": str(path.relative_to(ROOT)),
        "pages": doc.page_count,
        "extractor": "pymupdf",
        "total_extracted_chars": sum(char_counts),
        "empty_pages": sum(1 for count in char_counts if count == 0),
    }
    return pages, inventory


def extract_html(path: Path) -> tuple[list[dict], dict]:
    raw_html = path.read_text(encoding="utf-8", errors="ignore")

    # Saved browser pages include heavy navigation and cookie chrome. For the
    # parent-guidance pages, anchor extraction around article-specific content.
    if path.name == "AAP_Fever_When_To_Call.html":
        start = raw_html.lower().find("the most important things you can do")
        end = raw_html.lower().find("remember", start)
        if start != -1 and end != -1:
            raw_html = raw_html[start : end + 1200]
    elif path.name == "Mayo_Fever_Children.html":
        start = raw_html.lower().find("call your doctor if")
        end = raw_html.lower().find("</div>", start)
        if start != -1 and end != -1:
            raw_html = raw_html[start : end + 800]
    elif path.name == "Mayo_Vomiting_Children.html":
        start = raw_html.lower().find("seek emergency medical care")
        end = raw_html.lower().find("</div>", start)
        if start != -1 and end != -1:
            raw_html = raw_html[start : end + 800]

    soup = BeautifulSoup(raw_html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "img", "form", "nav", "footer", "header", "aside"]):
        tag.decompose()

    candidates = []
    if path.name.startswith("AAP"):
        candidates.extend(soup.select("#DeltaPlaceHolderMain"))
        candidates.extend(soup.select(".article"))
        candidates.extend(soup.select(".pageContent"))
    else:
        candidates.extend(soup.select("article"))
        candidates.extend(soup.select("#main-content"))
        candidates.extend(soup.select("[role=main]"))
        candidates.extend(soup.select("main"))

    candidates = [node for node in candidates if len(node.get_text(" ", strip=True)) > 500]
    if candidates:
        node = max(candidates, key=lambda item: len(item.get_text(" ", strip=True)))
        text = node.get_text("\n")
    else:
        text = soup.get_text("\n")

    text = prune_boilerplate(text)
    inventory = {
        "source_file": str(path.relative_to(ROOT)),
        "pages": None,
        "extractor": "beautifulsoup",
        "total_extracted_chars": len(text),
        "empty_pages": 0 if text else 1,
    }
    return [{"page": 1, "text": text}], inventory


def make_chunks(path: Path, page_texts: list[dict]) -> list[dict]:
    chunks = []
    sections = structural_sections(page_texts)
    source_name = SOURCE_NAMES.get(path.name, path.stem)
    rel = str(path.relative_to(ROOT))

    for section_index, section in enumerate(sections):
        section_text = clean_text("\n".join(section["lines"]))
        if len(section_text.split()) < 40:
            continue
        parent_id = stable_id(rel, section_index, section["title"])
        splits = split_recursive(section_text)
        for split_index, split in enumerate(splits):
            method = "structural" if len(splits) == 1 else "recursive_from_structural"
            chunk = {
                "chunk_id": stable_id(rel, section_index, split_index, split[:80]),
                "source_file": rel,
                "source_name": source_name,
                "source_type": source_type(path),
                "source_url": SOURCE_URLS.get(path.name, ""),
                "page_start": section["page_start"],
                "page_end": section["page_end"],
                "chapter_title": None,
                "section_title": section["title"],
                "subsection_title": None,
                "topic": infer_topic(split),
                "severity_relevance": infer_severity(split),
                "age_group": infer_age_group(split),
                "language": "en",
                "keywords": infer_keywords(split),
                "chunking_method": method,
                "parent_section_id": parent_id,
                "split_index": split_index,
                "text": split,
            }
            if chunk["source_type"] == "parent_guidance" and chunk["topic"] == "general":
                continue
            chunks.append(chunk)
    return chunks


def infer_age_group(text: str) -> str:
    lower = text.lower()
    if "younger than 3 months" in lower or "under 3 months" in lower:
        return "infant_under_3_months"
    if "3 to 12 months" in lower or "3 months" in lower:
        return "infant_3_to_12_months"
    if "younger than 2" in lower or "under 2" in lower:
        return "child_under_2_years"
    if "2 years" in lower:
        return "child_2_years_plus"
    return "all_children"


def infer_keywords(text: str) -> list[str]:
    lower = text.lower()
    keywords = []
    for terms in TOPIC_KEYWORDS.values():
        for term in terms:
            if term in lower:
                keywords.append(term)
    return sorted(set(keywords))[:20]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    source_paths = sorted((RAW_DIR / "clinical_guidelines").glob("*.pdf"))
    source_paths += sorted((RAW_DIR / "parent_guidance").glob("*.html"))

    all_chunks = []
    inventory = []
    for path in source_paths:
        if path.suffix.lower() == ".pdf":
            page_texts, source_inventory = extract_pdf(path)
        else:
            page_texts, source_inventory = extract_html(path)
        chunks = make_chunks(path, page_texts)
        source_inventory["chunks"] = len(chunks)
        inventory.append(source_inventory)
        all_chunks.extend(chunks)

    with CHUNKS_PATH.open("w", encoding="utf-8") as handle:
        for chunk in all_chunks:
            handle.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    INVENTORY_PATH.write_text(json.dumps(inventory, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"sources: {len(inventory)}")
    print(f"chunks: {len(all_chunks)}")
    print(f"wrote: {CHUNKS_PATH.relative_to(ROOT)}")
    print(f"wrote: {INVENTORY_PATH.relative_to(ROOT)}")
    for item in inventory:
        print(f"- {item['source_file']}: {item['chunks']} chunks, {item['total_extracted_chars']} chars")


if __name__ == "__main__":
    main()
