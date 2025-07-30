from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

from pydantic import BaseModel, Field

class RouteQuery(BaseModel):
    """Route a user query to the most relevant datasource."""

    datasource: Literal["vectorstore", "web_search", "chitchat"] = Field(
        ...,
        description="Given a user question choose to route it to web search, vectorstore or straight chitchat.",
    )


llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
structured_llm_router = llm.with_structured_output(RouteQuery)

system = """
You are an expert router that assigns each user question to exactly one of three data sources:

1. **chitchat**  
   – Any small talk or chit‑chat (hi/hello/how are you)  
   – Personal intros or identity questions (“what’s your name?”)  
   – Simple general‑knowledge or trivia (“who is Cristiano Ronaldo?”, “what’s 2+2?”)  

2. **Vectorstore**  
   – Anything about our product AI‑vengers: capabilities, deployments, integrations, pricing, features, usage instructions, architecture, or internal docs  
   – Questions mentioning how to customize, deploy, or troubleshoot our multimodal AI agents  

3. **Web search**  
   – Current events, world facts, third‑party services, or topics outside the scope of AI‑vengers  
   – Anything clearly unrelated to our product or technical documentation  

Always choose **vectorstore** if the question is even remotely about AI‑vengers. Do **not** send product‑related questions to web_search.  
If ever unsure, default to **chitchat** for fastest response.

### Examples:
Q: “Hi, how are you?” → chitchat  
Q: “What’s your name?” → chitchat  
Q: “Who won the Women’s World Cup?” → chitchat  
Q: “How do I integrate Twilio voice with my AI‑vengers agent?” → vectorstore  
Q: “What’s the latest MacBook Air release?” → web_search  
"""

route_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "{question}"),
    ]
)

question_router = route_prompt | structured_llm_router