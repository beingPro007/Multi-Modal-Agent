#!/usr/bin/env python3

import os
import pickle
import textwrap
from pathlib import Path
from dotenv import load_dotenv
from annoy import AnnoyIndex

load_dotenv()

CHUNK_SIZE = 500
EMBED_DIM = 384  # Because all-MiniLM-L6-v2 outputs 384-dim vectors

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "lead_rag_knowledge_base"
OUT_DIR = BASE_DIR / "rag_index"
OUT_DIR.mkdir(parents=True, exist_ok=True)

INDEX_FILE = OUT_DIR / "index.annoy"
METADATA_FILE = OUT_DIR / "metadata.pkl"

# from sentence_transformers import SentenceTransformer
# embedder = SentenceTransformer("all-MiniLM-L6-v2")

from openai import OpenAI
client = OpenAI()
MODEL = "text-embedding-3-small"
EMBED_DIM = 1536

def embed_text_openai(text: str) -> list[float]:
    response = client.embeddings.create(
        model=MODEL,
        input=[text],
    )
    return response.data[0].embedding

# def embed_text_local(text: str) -> list[float]:
#     return embedder.encode(text).tolist()

def build_index():
    uid = 0
    index = AnnoyIndex(EMBED_DIM, "angular")
    metadata = {}

    md_files = list(DATA_DIR.glob("*.md"))
    if not md_files:
        print("❌ No .md files found in rag_knowledge_base/")
        return

    for file in md_files:
        with open(file, "r", encoding="utf-8") as f:
            content = f.read()

        chunks = textwrap.wrap(content, width=CHUNK_SIZE, break_long_words=False)
        for chunk in chunks:
            cleaned = chunk.strip()
            if len(cleaned) < 30:
                continue

            vector = embed_text_openai(cleaned)

            index.add_item(uid, vector)
            metadata[uid] = {
                "source_file": file.name,
                "text": cleaned,
            }
            uid += 1

    index.build(10)
    index.save(str(INDEX_FILE))

    with open(METADATA_FILE, "wb") as f:
        pickle.dump(metadata, f)

    print(f"✅ RAG index built successfully!")
    print(f"📄 {uid} chunks indexed from {len(md_files)} files")
    print(f"🧠 Annoy index saved at: {INDEX_FILE}")
    print(f"📚 Metadata saved at: {METADATA_FILE}")


if __name__ == "__main__":
    build_index()
