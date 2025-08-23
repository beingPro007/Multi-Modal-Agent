from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a helpful Lead Agent for the company AI-Vengers. "
        "Always answer using only the provided messages. "
        "Avoid markdown, bullet points, and code blocks. "
        "Keep the tone suitable for text-to-speech."
        "Answer only using the provided messages. Keep it concise and clear"
    ),
    (
        "human",
        "messages:\n{messages}\n\nQuestion:\n{question}"
    )
])

llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

rag_chain = prompt | llm | StrOutputParser()

rag_chain = prompt | llm | StrOutputParser()

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)
