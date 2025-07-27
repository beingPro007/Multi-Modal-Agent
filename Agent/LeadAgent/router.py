from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

from pydantic import BaseModel, Field

class RouteQuery(BaseModel):
    """Route a user query to the most relevant datasource."""

    datasource: Literal["vectorstore", "web_search"] = Field(
        ...,
        description="Given a user question choose to route it to web search or a vectorstore.",
    )


llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
structured_llm_router = llm.with_structured_output(RouteQuery)

system = system = """You are an expert at routing user questions to the appropriate data source.

You have access to two data sources:
1. **Vectorstore** — it contains internal documentation related to the company's services, technical documentation, and agent capabilities, including:
   - Creating, customizing, and deploying AI agents
   - Supporting multimodal input/output (e.g. voice, image, chat)
   - Pricing plans, onboarding, and usage instructions
   - Hosting (managed vs. self-hosted), integrations like Twilio
   - Use cases of agents in different domains
   - Vision, goals, and features of the company

2. **Web search** — use only for current events, general world knowledge, third-party services, or topics unrelated to the company.

The company specializes in creating **multimodal AI agents** that can reason, communicate, and interact with users across different channels (voice, chat, visual).

If the question is **even remotely related** to the company’s platform, capabilities, pricing, features, or how to use it — route to **vectorstore**.

Only use **web_search** if the question is clearly unrelated to the platform.
"""
route_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "{question}"),
    ]
)

question_router = route_prompt | structured_llm_router