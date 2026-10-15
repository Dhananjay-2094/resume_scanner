import os
import pypdf
import docx2txt
import multiprocessing
from functools import partial

# --- STEP 2A: TEXT EXTRACTION ---
def extract_text_from_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    text = ""
    try:
        if ext == ".pdf":
            with open(file_path, "rb") as f:
                reader = pypdf.PdfReader(f)
                text = " ".join([page.extract_text() for page in reader.pages if page.extract_text()])
        elif ext == ".docx":
            text = docx2txt.process(file_path)
    except Exception as e:
        # handle file corruption errors without crashing the pool process
        return f"Error reading {os.path.basename(file_path)}: {str(e)}"
    return text

# --- STEP 2B: KEYWORD SCORING ENGINE ---
def evaluate_resume(file_path, taxonomy, weights):
    text = extract_text_from_file(file_path).lower()

    # Quick sanity check for parsing issues
    if text.startswith("error reading"):
        return {"filename": os.path.basename(file_path), "score": 0, "status": "Failed Parsing"}

    score = 0.0
    matched_breakdown = {}

    for category, keywords in taxonomy.items():
        # Count how many criteria keywords appear in the document
        matches = [kw for kw in keywords if kw.lower() in text]
        matched_breakdown[category] = matches
        # Calculate category match percentage
        match_ratio = len(matches) / len(keywords) if keywords else 0
        # Factor in configured category weight
        score += match_ratio * weights.get(category, 0)

    return {
        "filename": os.path.basename(file_path),
        "score": round(score * 100, 2), # Represent as a percentage
        "breakdown": matched_breakdown,
        "status": "Success"
    }

# --- STEP 2C: MULTIPROCESSING WORKER ---
def process_single_resume(file_path, taxonomy, weights):
    #worker function
    return evaluate_resume(file_path, taxonomy, weights)

def run_parallel_screening(file_paths, taxonomy, weights):
    # Use CPU count minus 1 to prevent system lockups during computation
    num_cores = max(1, multiprocessing.cpu_count() - 1)
    
    # Fix immutable parameters using partial mapping
    worker_func = partial(process_single_resume, taxonomy=taxonomy, weights=weights)
    
    with multiprocessing.Pool(processes=num_cores) as pool:
        # Use imap or map to chunk executions through the pool workers
        results = pool.map(worker_func, file_paths)
    
    # Sort candidates by score descending to generate the leaderboard
    return sorted(results, key=lambda x: x["score"], reverse=True)