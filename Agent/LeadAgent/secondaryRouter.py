from typing import Literal, Dict, Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables (e.g., OPENAI_API_KEY)
load_dotenv()

# --- Configuration for Knowledge Domains (Crucial for the router's context) ---
# This dictionary must be accessible to your routing logic.
# It's assumed to be the same KNOWLEDGE_DOMAINS dict from your ingestion script.
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

DomainLiterals = Literal[tuple(KNOWLEDGE_DOMAINS.keys())]

class VectorRouteQuery(BaseModel):
    """Route a user query to the most relevant knowledge domain."""

    datasource: Literal[
        "core_ai_system_info",
        "lead_generate_strategies",
        "sales_enablement_support",
        "market_competitor_intelligence",
        "agent_performance_development",
        "compliance_data_security",
        "agent_tools_operations"
    ] = Field(
        ...,
        description="The most relevant knowledge domain from the available options that best answers the user's question.",
    )

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
structured_llm_router = llm.with_structured_output(VectorRouteQuery)

domain_descriptions_for_prompt = "\n".join([
    f"- **{name}**: {data['description']}"
    for name, data in KNOWLEDGE_DOMAINS.items()
])

system_prompt = f"""
You are an intelligent routing assistant for an AI Lead Agent. Your primary task is to categorize user queries into the most relevant knowledge domain from a predefined set. You must select only one domain.

Here are the available knowledge domains and a brief description of the type of information they contain:

{domain_descriptions_for_prompt}

Analyze the user's question carefully and choose the single domain that is most likely to contain the answer. Focus on the core intent of the question.
"""

route_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{question}"),
    ]
)
vector_router = route_prompt | structured_llm_router