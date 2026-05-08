import json
from pathlib import Path

PARSED_DIR = Path("data/parsed_papers")

def get_relevant_chunks(query_keywords: list[str], max_chunks=10):
    """
    Scans all _markdown_chunks.json files and pulls chunks 
    that match clinical keywords.
    """
    all_chunks = []
    
    # Iterate through all generated chunk files
    for chunk_file in PARSED_DIR.glob("*_markdown_chunks.json"):
        with open(chunk_file, "r") as f:
            paper_chunks = json.load(f)
            
            for chunk in paper_chunks:
                text = chunk["text"].lower()
                # Simple keyword filtering for now
                if any(kw.lower() in text for kw in query_keywords):
                    all_chunks.append(chunk)
    
    # Sort or filter further if needed
    return all_chunks[:max_chunks]

# Example Test
if __name__ == "__main__":
    # If the user asks about mortality prediction:
    results = get_relevant_chunks(["mortality", "AUC", "score"])
    print(f"Found {len(results)} candidate chunks for extraction.")