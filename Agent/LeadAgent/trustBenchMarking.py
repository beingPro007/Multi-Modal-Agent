from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

class TrustScore(BaseModel):
    score: float = Field(
        description="Trust score between 0 and 1. Values > 0.5 indicate increasing trust; values <= 0.5 suggest declining or low trust."
    )

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
structured_llm_grader = llm.with_structured_output(TrustScore)

system = """You are a professional trust evaluator. 
Your task is to assign a trust score based on the user's message history, reference documents, and the latest LLM response.
The score should be a floating-point number between 0 and 1.

- A score > 0.5 indicates increasing or high trust in the product.
- A score <= 0.5 suggests low or declining trust.
Be objective and use all provided context.
"""

trust_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "LLM Generation:\n{generation}\n\nMessage History:\n{messages}")
    ]
)

trust_scorer = trust_prompt | structured_llm_grader
