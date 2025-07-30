from dotenv import load_dotenv
from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from typing import List, Dict

# Load environment variables (e.g., OPENAI_API_KEY)
load_dotenv()
KNOWLEDGE_DOMAINS = {
    "core_ai_system_info": {
        "path": "rag_build/lead_rag_knowledge_base/core_ai_system_info",
        "collection_name": "core_ai_system_info_collection",
        "description": "Information about AI-vengers system features, customization, LLM integration, pricing, and hosting options."
    },
    "lead_generate_strategies": {
        "path": "rag_build/lead_rag_knowledge_base/lead_generate_strategies",
        "collection_name": "lead_generation_strategies_collection",
        "description": "Strategies for lead generation, qualification, nurturing, follow-up, closing techniques, objection handling, inbound and outbound tactics, and CRM usage."
    },
    "sales_enablement_support": {
        "path": "rag_build/lead_rag_knowledge_base/sales_enablement_support",
        "collection_name": "sales_enablement_support_collection",
        "description": "Resources for sales playbooks, common customer pain points, success stories, competitor overviews, product updates, FAQs, and sales tech stack guides."
    },
    "market_competitor_intelligence": {
        "path": "rag_build/lead_rag_knowledge_base/market_competitor_intelligence",
        "collection_name": "market_competitor_intelligence_collection",
        "description": "Analysis of industry trends, deep dives into competitors, market segmentation, value proposition messaging, and ideal customer profile definitions."
    },
    "agent_performance_development": {
        "path": "rag_build/lead_rag_knowledge_base/agent_performance_development",
        "collection_name": "agent_performance_development_collection",
        "description": "Metrics for agent performance, common challenges, onboarding checklists, and guides for feedback and coaching."
    },
    "compliance_data_security": {
        "path": "rag_build/lead_rag_knowledge_base/compliance_data_security",
        "collection_name": "compliance_data_security_collection",
        "description": "Policies and guidelines related to data privacy, security, and regulatory compliance for handling sensitive information."
    },
}

CHROMA_PERSIST_DIRECTORY = "./chroma_db"
ROUTING_COLLECTION_NAME = "knowledge_domain_routing"

Path(CHROMA_PERSIST_DIRECTORY).mkdir(parents=True, exist_ok=True)


def load_md_files(folder_path: str) -> List[Document]:
    """
    Loads all Markdown files from a given folder and its subfolders.
    """
    files = Path(folder_path).rglob("*.md")
    docs = []
    for file in files:
        try:
            content = file.read_text(encoding='utf-8')
            docs.append(Document(page_content=content, metadata={"source": str(file)}))
        except Exception as e:
            print(f"Error reading file {file}: {e}")
    print(f"Loaded {len(docs)} documents from {folder_path}")
    return docs

splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
embedding_model = OpenAIEmbeddings(model="text-embedding-3-small") # Explicitly define the model for clarity

specialized_vectorstores: Dict[str, Chroma] = {}

print("--- Starting Data Ingestion into Specialized Chroma Collections ---")

for domain_name, config in KNOWLEDGE_DOMAINS.items():
    print(f"\nProcessing domain: '{domain_name}'")
    
    docs_for_domain = load_md_files(config["path"])

    if not docs_for_domain:
        print(f"No Markdown documents found in '{config['path']}'. Skipping this domain.")
        continue

    split_docs_for_domain = splitter.split_documents(docs_for_domain)
    print(f"Split {len(docs_for_domain)} documents into {len(split_docs_for_domain)} chunks for '{domain_name}'.")

    try:
        vectorstore_domain = Chroma.from_documents(
            documents=split_docs_for_domain,
            embedding=embedding_model,
            persist_directory=CHROMA_PERSIST_DIRECTORY,
            collection_name=config["collection_name"] # KEY CHANGE: Assign specific collection name
        )
        specialized_vectorstores[domain_name] = vectorstore_domain
        print(f"Successfully ingested/updated data for collection: '{config['collection_name']}'")
    except Exception as e:
        print(f"Error creating/updating vectorstore for {domain_name} ({config['collection_name']}): {e}")

print("\n--- All specialized knowledge base collections processed. ---")


print("\n--- Creating/Updating the Routing Vector Database ---")
routing_docs = []
for domain_name, config in KNOWLEDGE_DOMAINS.items():
    routing_docs.append(
        Document(
            page_content=config["description"],
            metadata={
                "domain_name": domain_name,
                "collection_name": config["collection_name"]
            }
        )
    )

if not routing_docs:
    print("Warning: No routing documents were generated. Check KNOWLEDGE_DOMAINS configuration.")
else:
    try:
        routing_vectorstore = Chroma.from_documents(
            documents=routing_docs,
            embedding=embedding_model,
            persist_directory=CHROMA_PERSIST_DIRECTORY,
            collection_name=ROUTING_COLLECTION_NAME
        )
        print(f"Routing vector database created/updated in collection: '{ROUTING_COLLECTION_NAME}'")
    except Exception as e:
        print(f"Error creating/updating routing vectorstore: {e}")

print("\n--- Vector database setup complete for both specialized content and routing. ---")

# You can now conceptually think of how you would access these:
# # To get a retriever for a specific domain (e.g., Lead Generation):
# lead_gen_retriever = specialized_vectorstores["lead_generate_strategies"].as_retriever()
#
# # To get the retriever for the routing logic:
# routing_retriever = routing_vectorstore.as_retriever()