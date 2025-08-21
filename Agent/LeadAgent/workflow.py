from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from dotenv import load_dotenv
from typing import List, Literal, Dict
from typing_extensions import TypedDict
from langchain_tavily import TavilySearch
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain.schema import Document
from langgraph.graph import END, StateGraph, START

from Agent.LeadAgent.primaryRouter import question_router
from Agent.LeadAgent.secondaryRouter import vector_router 
from Agent.LeadAgent.generate import format_docs, rag_chain
from Agent.LeadAgent.questionRewriter import question_rewriter
from Agent.LeadAgent.trustBenchMarking import trust_scorer

from Agent.LeadAgent.specialized_vectorstores.retriever import loaded_specialized_vectorstores

load_dotenv()

retriever: Dict[str, Chroma] = loaded_specialized_vectorstores

chat_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0) # For chitchat
llm_for_generation = ChatOpenAI(model="gpt-4o", temperature=0) # For RAG generation
web_search_tool = TavilySearch(k=2)

class GraphState(TypedDict):
    messages: List[BaseMessage]
    generation: str
    documents: List[Document]
    chosen_domain: str 
    chosen_route: str
    trust_score: float

def _get_latest_human_query(messages: List[BaseMessage]) -> str:
    """Extracts the content of the latest HumanMessage from a list of messages."""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            return msg.content
    return "" # Should ideally not happen if graph starts with a user query

def format_messages_for_llm_context(messages: List[BaseMessage]) -> str:
    """
    Formats a list of BaseMessages into a string suitable for LLM context,
    often used for chat history or combining with documents.
    """
    formatted_str = ""
    for msg in messages:
        if isinstance(msg, HumanMessage):
            formatted_str += f"User: {msg.content.strip()}\n"
        elif isinstance(msg, AIMessage):
            formatted_str += f"Assistant: {msg.content.strip()}\n"
    return formatted_str.strip()

def chitchat(state: GraphState) -> GraphState:
    print("---CHITCHAT / GENERAL CONVERSATION---")
    messages = state.get("messages", [])
    latest_user_query = _get_latest_human_query(messages)
    
    chat_history_for_llm = format_messages_for_llm_context(messages[:-1])
    
    response = chat_llm.invoke([
        SystemMessage(content="You are a friendly and concise general assistant for our company. Respond conversationally to greetings or out-of-scope questions. Do not use markdown formatting. Politely guide the user back to company-related topics if the conversation veers too far."),
        HumanMessage(content=f"Chat History:\n{chat_history_for_llm}\nUser Query: {latest_user_query}")
    ])

    new_messages = messages + [AIMessage(content=response.content.strip())]
    
    return {
        **state,
        "generation": response.content.strip(),
        "messages": new_messages,
        "documents": []
    }
    
def secondary_router_node(state: GraphState) -> GraphState:
    print("--SECONDARY ROUTER---")
    messages = state["messages"]
    
    latest_user_query = _get_latest_human_query(messages)

    response = vector_router.invoke({"question": latest_user_query})
    chosen_domain = response.datasource # Access the 'datasource' attribute from the Pydantic model
    
    print(f"Secondary router chose domain: '{chosen_domain}'")
    
    return {**state, "chosen_domain": chosen_domain}
    
def retrieve(state: GraphState) -> GraphState:
    """
    Retrieves documents from the specific Chroma collection chosen by the secondary router.
    """
    print("---RETRIEVING DOCUMENTS FROM SPECIFIC DOMAIN---")
    messages = state["messages"]
    chosen_domain = state.get("chosen_domain")

    latest_user_query = _get_latest_human_query(messages)
    
    if not chosen_domain or chosen_domain not in retriever:
        print(f"Error: Invalid or un-loaded domain '{chosen_domain}' for retrieval. Returning empty documents.")
        return {**state, "documents": []}

    domain_retriever = retriever[chosen_domain].as_retriever(k=2)

    documents = domain_retriever.invoke(latest_user_query)
    print(f"Retrieved {len(documents)} documents from '{chosen_domain}' collection.")
    
    return {**state, "documents": documents} 

def route_question(state: GraphState) -> Literal["chitchat", "web_search", "vectorstore"]:
    """
    Primary Router (first level): Routes the query to chitchat, web search, or the internal vectorstore (generic).
    Uses 'question_router' (from primaryRouter.py).
    """
    print("---PRIMARY ROUTING---")
    messages = state["messages"]
    latest_user_query = _get_latest_human_query(messages)
    
    source_decision = question_router.invoke({"question": latest_user_query})
    chosen_route = source_decision.datasource
    
    print(f"Primary router chose: '{chosen_route}'")
    state["chosen_route"] = chosen_route
    return state

def generate(state: GraphState) -> GraphState:
    
    print("---GENERATE---")
    messages = state["messages"]
    documents = state["documents"]
    curr_trust_score = state.get("trust_score", 0.0)

    latest_user_query = _get_latest_human_query(messages)
    
    docs_txt = format_docs(documents)
    
    if not docs_txt:
        print("No documents available for generation. Generating a fallback response.")
        response = chat_llm.invoke([
            SystemMessage(content="You are an AI Lead Agent assistant. You could not find specific information in your knowledge base or via web search for the user's request. Politely state that you cannot answer the question based on the available information and offer to help with other company-related queries."),
            HumanMessage(content=latest_user_query)
        ])
        generation = response.content.strip()
    else:
        generation = rag_chain.invoke({"messages": docs_txt, "question": latest_user_query, "trust_score": curr_trust_score})
    
    new_messages = messages + [AIMessage(content=generation)]
    
    return {**state, "messages": new_messages, "generation": generation}

def trust_evaluator(state: GraphState) -> GraphState:
    print("---Evaluating the Trust Score---")
    messages = state.get("messages", [])
    generation = state.get("generation", "")
    
    score = trust_scorer.invoke({"generation": generation, "messages": messages}).score

    print(f"Trust Score Evaluated: {score}")
    
    if score >= 0.5:
        print("---------------Fetching User Email--------------")
        print("---------------Email Sent--------------")

    return {**state, "trust_score": score}
 
def escalate_to_human_agent(state: GraphState) -> GraphState:
    print("---ESCALATING TO HUMAN AGENT---")
    messages = state["messages"]
    latest_user_query = _get_latest_human_query(messages)

    escalation_message = (
        "I apologize, but I'm unable to fully assist with that request at the moment. "
        "I'm connecting you with a human expert who can provide more in-depth support. "
        "Please hold while I transfer you."
    )

    new_messages = messages + [AIMessage(content=escalation_message)]

    print("Escalation triggered. (In a real system, this would involve API calls to a human agent platform).")

    return {
        **state,
        "generation": escalation_message,
        "messages": new_messages,
        "documents": []
    }

def transform_query(state: GraphState) -> GraphState:
    """
    Rewrites the user's query if initial retrieval was not successful (e.g., no documents found).
    """
    print("---TRANSFORM QUERY---")
    messages = state["messages"]
    latest_user_query = _get_latest_human_query(messages)
    
    better_question = question_rewriter.invoke({"question": latest_user_query})
    
    new_messages = messages + [HumanMessage(content=better_question, name="rewritten_query")]
    print(f"Original query: '{latest_user_query}'")
    print(f"Transformed query: '{better_question}'")
    
    return {**state, "messages": new_messages}

def web_search(state: GraphState) -> GraphState:
    """
    Performs a web search based on the latest user query.
    """
    print("---WEB SEARCH---")
    messages = state["messages"]
    latest_user_query = _get_latest_human_query(messages)
    
    try:
        docs = web_search_tool.invoke({"query": latest_user_query})
        web_results = "\n".join([d["content"] for d in docs])
        web_doc = Document(page_content=web_results, metadata={"source": "web_search"})
        print(f"Web search retrieved {len(docs)} results.")
        
        return {**state, "documents": [web_doc]}
    except Exception as e:
        print(f"Error during web search: {e}. Returning empty documents.")
        return {**state, "documents": []}

def leadAgent_workflow():
    workflow = StateGraph(GraphState)

    workflow.add_node("route_question", route_question)
    workflow.add_node("chitchat", chitchat)
    workflow.add_node("web_search", web_search)
    workflow.add_node("secondary_router_node", secondary_router_node)
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("generate", generate)
    workflow.add_node("transform_query", transform_query)
    workflow.add_node("trust_score", trust_evaluator)

    workflow.add_edge(START, "route_question")
    workflow.add_conditional_edges(
        "route_question",
        lambda state: state["chosen_route"],
        {
            "chitchat": "chitchat",
            "web_search": "web_search",
            "vectorstore": "secondary_router_node"
        },
    )
    workflow.add_edge("chitchat", END)
    workflow.add_edge("web_search", "generate") 
    workflow.add_edge("secondary_router_node", "retrieve")
    workflow.add_edge("retrieve", "generate")

    workflow.add_conditional_edges(
        "generate",
        lambda state: "transform_query" if not state.get("documents") else "trust_score",
        {
            "transform_query": "transform_query",
            "trust_score": "trust_score",
        },
    )

    workflow.add_edge("transform_query", "retrieve") 
    workflow.add_edge("generate", "trust_score")
    workflow.add_edge("trust_score", END)
    
    return workflow.compile()