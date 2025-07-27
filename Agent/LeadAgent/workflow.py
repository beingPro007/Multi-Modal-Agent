from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
from typing import List
from typing_extensions import TypedDict
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import BaseMessage, HumanMessage
from langchain.schema import Document
from langgraph.graph import END, StateGraph, START

from Agent.LeadAgent.router import question_router
from Agent.LeadAgent.generate import format_docs, rag_chain
from Agent.LeadAgent.retreivalGrader import retrieval_grader
from Agent.LeadAgent.questionRewriter import question_rewriter
from Agent.LeadAgent.hallucinationGrader import hallucination_grader
from Agent.LeadAgent.answeGrader import answer_grader

load_dotenv()

embedding_model = OpenAIEmbeddings()
vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embedding_model
)
retriever = vectorstore.as_retriever()
web_search_tool = TavilySearchResults(k=3)

class GraphState(TypedDict):
    messages: List[BaseMessage]
    generation: str
    documents: List[Document]

def retrieve(state):
    print("---RETRIEVE---")
    print(state["messages"])
    messages = state["messages"]
    print()
    latest_user_query = [msg.content for msg in messages if isinstance(msg, HumanMessage)][-1]
    print("----------Latest User Query----------", latest_user_query)
    documents = retriever.invoke(latest_user_query)
    return {"documents": documents, "question": messages}

def route_question(state):
    print("---ROUTE QUESTION---")
    print(state["messages"])
    messages = state["messages"]
    latest_user_query = [msg.content for msg in messages if isinstance(msg, HumanMessage)][-1]
    print("Latest user query: ", latest_user_query)
    source = question_router.invoke({"question": latest_user_query})
    if source.datasource == "web_search":
        print("---ROUTE QUESTION TO WEB SEARCH---")
        return "web_search"
    elif source.datasource == "vectorstore":
        print("---ROUTE QUESTION TO RAG---")
        return "vectorstore"

def generate(state):
    print("---GENERATE---")
    messages = state["messages"]
    documents = state["documents"]
    latest_user_query = [msg.content for msg in messages if isinstance(msg, HumanMessage)][-1]
    docs_txt = format_docs(documents)
    generation = rag_chain.invoke({"context": docs_txt, "question": latest_user_query})
    return {"documents": documents, "question": messages, "generation": generation, "text_generation": True}

def grade_documents(state):
    print("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
    messages = state["messages"]
    documents = state["documents"]
    latest_user_query = [msg.content for msg in messages if isinstance(msg, HumanMessage)][-1]
    filtered_docs = []
    for d in documents:
        score = retrieval_grader.invoke({"question": latest_user_query, "document": d.page_content})
        if score.binary_score == "yes":
            print("---GRADE: DOCUMENT RELEVANT---")
            filtered_docs.append(d)
        else:
            print("---GRADE: DOCUMENT NOT RELEVANT---")
    return {"documents": filtered_docs, "question": messages}

def finalize_output(state: GraphState) -> GraphState:
    final_answer = state["generation"]
    print("\n--- FINAL OUTPUT ---")
    print(final_answer)
    return {"generation": final_answer, "messages": state["messages"], "documents": []}

def transform_query(state):
    print("---TRANSFORM QUERY---")
    messages = state["messages"]
    documents = state["documents"]
    latest_user_query = [msg.content for msg in messages if isinstance(msg, HumanMessage)][-1]
    better_question = question_rewriter.invoke({"question": latest_user_query})
    new_messages = messages + [HumanMessage(content=better_question)]
    return {"documents": documents, "question": new_messages}

def web_search(state):
    print("---WEB SEARCH---")
    messages = state["messages"]
    latest_user_query = [msg.content for msg in messages if isinstance(msg, HumanMessage)][-1]
    docs = web_search_tool.invoke({"query": latest_user_query})
    web_results = "\n".join([d["content"] for d in docs])
    web_doc = Document(page_content=web_results)
    return {"documents": [web_doc], "question": messages}

def decide_to_generate(state):
    print("---ASSESS GRADED DOCUMENTS---")
    filtered_documents = state["documents"]
    if not filtered_documents:
        print("---DECISION: ALL DOCUMENTS ARE NOT RELEVANT TO QUESTION, TRANSFORM QUERY---")
        return "transform_query"
    else:
        print("---DECISION: GENERATE---")
        return "generate"

def grade_generation_v_documents_and_question(state):
    print("---CHECK HALLUCINATIONS---")
    messages = state["messages"]
    documents = state["documents"]
    generation = state["generation"]

    hallucination_score = hallucination_grader.invoke({
        "documents": documents,
        "generation": generation
    }).binary_score

    if hallucination_score == "yes":
        latest_user_query = [msg.content for msg in messages if isinstance(msg, HumanMessage)][-1]
        answer_score = answer_grader.invoke({
            "question": latest_user_query,
            "generation": generation
        }).binary_score
        if answer_score == "yes":
            print("---DECISION: GENERATION ADDRESSES QUESTION---")
            return "useful"
        else:
            print("---DECISION: GENERATION DOES NOT ADDRESS QUESTION---")
            return "not useful"
    else:
        print("---DECISION: GENERATION IS NOT GROUNDED IN DOCUMENTS, RE-TRY---")
        return "not supported"

def leadAgent_workflow():
    workflow = StateGraph(GraphState)
    workflow.add_node("web_search", web_search)
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("grade_documents", grade_documents)
    workflow.add_node("generate", generate)
    workflow.add_node("transform_query", transform_query)

    workflow.add_conditional_edges(
        START,
        route_question,
        {
            "web_search": "web_search",
            "vectorstore": "retrieve",
        },
    )
    workflow.add_edge("web_search", "generate")
    workflow.add_edge("retrieve", "grade_documents")
    workflow.add_conditional_edges(
        "grade_documents",
        decide_to_generate,
        {
            "transform_query": "transform_query",
            "generate": "generate",
        },
    )
    workflow.add_edge("transform_query", "retrieve")
    workflow.add_conditional_edges(
        "generate",
        grade_generation_v_documents_and_question,
        {
            "not supported": "generate",
            "useful": END,
            "not useful": "transform_query",
        },
    )

    return workflow.compile()


