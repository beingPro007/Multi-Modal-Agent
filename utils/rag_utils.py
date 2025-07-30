import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

load_dotenv()

# --- Initialize OpenAI Embeddings + ChromaDB ---
embedding_model = OpenAIEmbeddings()
vector_db = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embedding_model
)

TOP_K = 3

# --- Simple RAG Search Function ---
def search_docs(query: str, top_k: int = TOP_K) -> str:
    results = vector_db.similarity_search(query, k=top_k)

    if not results:
        return "Sorry, I couldn’t find anything relevant."

    formatted = []
    for doc in results:
        source = doc.metadata.get("source", "internal")
        text = doc.page_content.strip()
        formatted.append(f"From {source}:\n{text}\n")

    return formatted[0]  # Return only top result for brevity
