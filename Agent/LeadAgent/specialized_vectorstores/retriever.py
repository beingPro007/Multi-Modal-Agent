from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from typing import Dict


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
    "agent_tools_operations": {
        "path": "rag_build/lead_rag_knowledge_base/agent_tools_operations",
        "collection_name": "agent_tools_operations_collection",
        "description": "Information on API integrations, troubleshooting common technical issues, and best practices for version control of agent assets."
    },
}
CHROMA_PERSIST_DIRECTORY = "/home/appuser/rag_build/chroma_db"

embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")

loaded_specialized_vectorstores: Dict[str, Chroma] = {}
print("Loading specialized Chroma collections for LangGraph...")
for domain_name, config in KNOWLEDGE_DOMAINS.items():
    try:
        loaded_specialized_vectorstores[domain_name] = Chroma(
            persist_directory=CHROMA_PERSIST_DIRECTORY,
            embedding_function=embedding_model,
            collection_name=config["collection_name"]
        )
        print(f"Loaded collection: '{config['collection_name']}' for domain '{domain_name}'")
    except Exception as e:
        print(f"ERROR: Could not load collection '{config['collection_name']}': {e}")
