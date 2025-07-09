import pickle
from pathlib import Path
from annoy import AnnoyIndex
from sentence_transformers import SentenceTransformer

INDEX_PATH = Path("rag_build/rag_index/index.annoy")
METADATA_PATH = Path("rag_build/rag_index/metadata.pkl")
EMBED_DIM = 384
TOP_K = 3

embedder = SentenceTransformer("all-MiniLM-L6-v2")
index = AnnoyIndex(EMBED_DIM, "angular")
index.load(str(INDEX_PATH))

with open(METADATA_PATH, "rb") as f:
    metadata = pickle.load(f)

def search_docs(query: str, top_k: int = TOP_K) -> str:
    query_vector = embedder.encode(query)
    ids, distances = index.get_nns_by_vector(query_vector, top_k, include_distances=True)

    results = []
    for i, dist in zip(ids, distances):
        meta = metadata.get(i, {})
        source = meta.get("source_file", "unknown")
        text = meta.get("text", "").strip()
        results.append(f"From {source}:\n{text}\n")

    if not results:
        return "Sorry, I couldn’t find anything relevant."

    return results[0]