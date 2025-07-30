from langchain import hub
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

# Prompt
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a helpful, concise assistant. Answer the user's question using only the provided context. "
        "Respond in clear, natural, spoken-style plain text suitable for text-to-speech. "
        "Avoid markdown, bullet points, and code blocks. Keep your answer short and to the point."
    ),
    (
        "human",
        "Context:\n\n{context}\n\nQuestion:\n{question}"
    )
])


# LLM
llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)


# Post-processing
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


# Chain
rag_chain = prompt | llm | StrOutputParser()