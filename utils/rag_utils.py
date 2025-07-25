import os
import pickle
from pathlib import Path
from annoy import AnnoyIndex
import openai
from dotenv import load_dotenv

load_dotenv()

MODEL = "text-embedding-3-small"
EMBED_DIM = 1536
TOP_K = 3

INDEX_PATH = Path("rag_build/rag_index/index.annoy")
METADATA_PATH = Path("rag_build/rag_index/metadata.pkl")

index = AnnoyIndex(EMBED_DIM, "angular")
index.load(str(INDEX_PATH))

with open(METADATA_PATH, "rb") as f:
    metadata = pickle.load(f)

def embed_text_openai(text: str) -> list[float]:
    response = openai.Embedding.create(
        model=MODEL,
        input=[text],
    )
    return response["data"][0]["embedding"]

def search_docs(query: str, top_k: int = TOP_K) -> str:
    query_vector = embed_text_openai(query)
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
