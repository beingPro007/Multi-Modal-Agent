from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from typing import List, TypedDict, Dict, Annotated
from langchain_tavily import TavilySearch
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.schema import Document
from langgraph.graph import END, StateGraph, START, add_messages

from Agent.LeadAgent.primaryRouter import question_router
from Agent.LeadAgent.secondaryRouter import vector_router
from Agent.LeadAgent.generate import format_docs, rag_chain
from Agent.LeadAgent.questionRewriter import question_rewriter
from Agent.LeadAgent.specialized_vectorstores.retriever import loaded_specialized_vectorstores

load_dotenv()

retriever: Dict[str, Chroma] = loaded_specialized_vectorstores
chat_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
llm_for_generation = ChatOpenAI(model="gpt-4o", temperature=0)
web_search_tool = TavilySearch(k=2)


class GraphState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    generation: Annotated[str, "The generated text"]
    documents: Annotated[List[Document], "Relevant documents"]
    chosen_domain: Annotated[str, "Domain chosen for reasoning"]
    chosen_route: Annotated[str, "Route/path chosen"]


def _get_latest_human_query(messages: List[BaseMessage]) -> str:
    """Get the content of the latest HumanMessage."""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            return msg.content
    return ""


def format_messages_for_llm_context(messages: List[BaseMessage]) -> str:
    """Formats a list of messages into a single string for LLM context."""
    return "\n".join(
        f"User: {m.content}" if isinstance(m, HumanMessage) else f"Assistant: {m.content}"
        for m in messages
    )


def chitchat(state: GraphState) -> Dict:
    messages = state.get("messages", [])
    latest_user_query = _get_latest_human_query(messages)
    chat_history = format_messages_for_llm_context(messages[:-1])
    
    response = chat_llm.invoke([
        SystemMessage(content="You are a friendly assistant. Answer general questions. Guide back to company topics if off-topic."),
        HumanMessage(content=f"Chat history:\n{chat_history}\nUser Query: {latest_user_query}")
    ])
    
    new_messages = messages + [AIMessage(content=response.content.strip())]
    
    return {"generation": response.content.strip(), "messages": new_messages, "documents": []}


def secondary_router_node(state: GraphState) -> Dict:
    messages = state["messages"]
    latest_user_query = _get_latest_human_query(messages)
    try:
        response = vector_router.invoke({"question": latest_user_query})
        chosen_domain = response.datasource
        print(f"[Secondary Router] Domain chosen: {chosen_domain}")
        return {"chosen_domain": chosen_domain}
    except Exception as e:
        print(f"[Secondary Router] Error determining domain: {e}")
        return {"chosen_domain": ""}


def retrieve(state: GraphState) -> Dict:
    messages = state["messages"]
    chosen_domain = state.get("chosen_domain")
    latest_user_query = _get_latest_human_query(messages)
    
    if not chosen_domain or chosen_domain not in retriever:
        print(f"[Retrieve] Invalid domain '{chosen_domain}'. Returning empty documents.")
        return {"documents": []}

    try:
        domain_retriever = retriever[chosen_domain].as_retriever(k=2)
        documents = domain_retriever.invoke(latest_user_query)
        print(f"[Retrieve] Retrieved {len(documents)} documents from '{chosen_domain}'.")
        return {"documents": documents}
    except Exception as e:
        print(f"[Retrieve] Error fetching documents: {e}")
        return {"documents": []}


def route_question(state: GraphState) -> Dict:
    messages = state["messages"]
    latest_user_query = _get_latest_human_query(messages)
    try:
        source_decision = question_router.invoke({"question": latest_user_query})
        chosen_route = source_decision.datasource
        print(f"[Primary Router] Route chosen: {chosen_route}")
        return {"chosen_route": chosen_route}
    except Exception as e:
        print(f"[Primary Router] Error determining route: {e}")
        return {"chosen_route": "chitchat"}  # default fallback


def generate(state: GraphState) -> Dict:
    messages = state["messages"]
    documents = state["documents"]
    latest_user_query = _get_latest_human_query(messages)
    docs_txt = format_docs(documents)

    if not docs_txt:
        print("[Generate] No documents available. Using fallback response.")
        response = chat_llm.invoke([
            SystemMessage(content="You are an AI Lead Agent. No docs found, respond politely that info is unavailable."),
            HumanMessage(content=latest_user_query)
        ])
        generation = response.content.strip()
    else:
        try:
            generation = rag_chain.invoke({"messages": docs_txt, "question": latest_user_query})
        except Exception as e:
            print(f"[Generate] Error during RAG generation: {e}")
            generation = "Sorry, I could not generate an answer from the knowledge base."

    new_messages = messages + [AIMessage(content=generation)]
    return {"messages": new_messages, "generation": generation}


def transform_query(state: GraphState) -> Dict:
    messages = state["messages"]
    latest_user_query = _get_latest_human_query(messages)
    try:
        better_question = question_rewriter.invoke({"question": latest_user_query})
        new_messages = messages[:-1] + [HumanMessage(content=better_question, name="rewritten_query")]
        print(f"[Transform Query] Original: '{latest_user_query}' | Transformed: '{better_question}'")
        return {"messages": new_messages}
    except Exception as e:
        print(f"[Transform Query] Error rewriting query: {e}")
        return {"messages": messages}


def web_search(state: GraphState) -> Dict:
    messages = state["messages"]
    latest_user_query = _get_latest_human_query(messages)
    try:
        docs = web_search_tool.invoke({"query": latest_user_query})
        web_doc = Document(
            page_content="\n".join([d["content"] for d in docs]),
            metadata={"source": "web_search"}
        )
        print(f"[Web Search] Retrieved {len(docs)} results.")
        return {"documents": [web_doc]}
    except Exception as e:
        print(f"[Web Search] Error during web search: {e}")
        return {"documents": []}


# --- Workflow Definition ---
def leadAgent_workflow():
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("route_question", route_question)
    workflow.add_node("chitchat", chitchat)
    workflow.add_node("web_search", web_search)
    workflow.add_node("secondary_router_node", secondary_router_node)
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("generate", generate)
    workflow.add_node("transform_query", transform_query)

    # Define edges
    workflow.add_edge(START, "route_question")
    workflow.add_conditional_edges(
        "route_question",
        lambda state: state["chosen_route"],
        {"chitchat": "chitchat", "web_search": "web_search", "vectorstore": "secondary_router_node"},
    )
    workflow.add_edge("chitchat", END)
    workflow.add_edge("web_search", "generate")
    workflow.add_edge("secondary_router_node", "retrieve")
    workflow.add_edge("retrieve", "generate")

    workflow.add_conditional_edges(
        "generate",
        lambda state: "transform_query" if not state.get("documents") else END,
        {"transform_query": "transform_query", END: END},
    )
    workflow.add_edge("transform_query", "retrieve")

    return workflow.compile()