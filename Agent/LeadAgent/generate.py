from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a helpful, Lead Agent. Use the user's trust score to guide your tone and depth knowledge for generating the best response possible for a company naming AI-Vengers.\n"
        "- If trust is low (<= 0.5), be reassuring, give examples, and speak with extra clarity.\n"
        "- If trust is high (> 0.5), be efficient and focus on just the answer.\n"
        "Always answer using only the provided messages.\n"
        "Avoid markdown, bullet points, and code blocks. Keep the tone suitable for text-to-speech."
    ),
    (
        "human",
        "messages:\n{messages}\n\nQuestion:\n{question}\n\nTrust Score: {trust_score}"
    )
])

llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
rag_chain = prompt | llm | StrOutputParser()

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)