from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings

VECTOR_DB_DIR = "rag_index_faiss"

def get_retriever(top_k=3):
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    db = FAISS.load_local(VECTOR_DB_DIR, embeddings, allow_dangerous_deserialization=True)
    return db.as_retriever(search_kwargs={"k": top_k})
