from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from dotenv import load_dotenv
from typing import List, Literal, Dict
from typing_extensions import TypedDict
from langchain_tavily import TavilySearch
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain.schema import Document
from langgraph.graph import END, StateGraph, START

# --- Import your custom routers ---
from Agent.LeadAgent.primaryRouter import question_router # This is your top-level router
from Agent.LeadAgent.secondaryRouter import vector_router # This is your domain-specific router

# --- Other necessary imports ---
from Agent.LeadAgent.generate import format_docs, rag_chain
from Agent.LeadAgent.questionRewriter import question_rewriter

# --- Import the pre-loaded specialized vectorstores ---
# This is crucial for dynamic retrieval from specific domains.
from Agent.LeadAgent.specialized_vectorstores.retriever import loaded_specialized_vectorstores

load_dotenv()

# `loaded_specialized_vectorstores` is a dictionary: {'domain_name': Chroma_instance}
# We assign it directly to `retriever` for convenience in this file.
retriever: Dict[str, Chroma] = loaded_specialized_vectorstores

chat_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0) # For chitchat
llm_for_generation = ChatOpenAI(model="gpt-4o", temperature=0) # For RAG generation
web_search_tool = TavilySearch(k=3)


class GraphState(TypedDict):
    messages: List[BaseMessage]
    generation: str
    documents: List[Document]
    chosen_domain: str 
    chosen_route: str

# --- Helper Functions ---

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
        # SystemMessage content might be included if desired for full history context
    return formatted_str.strip()


# --- LangGraph Nodes (Functions) ---

def chitchat(state: GraphState) -> GraphState:
    print("---CHITCHAT / GENERAL CONVERSATION---")
    messages = state.get("messages", [])
    latest_user_query = _get_latest_human_query(messages)
    
    chat_history_for_llm = format_messages_for_llm_context(messages[:-1]) # Exclude current query for chat history
    
    response = chat_llm.invoke([
        SystemMessage(content="You are a friendly and concise general assistant for our company. Respond conversationally to greetings or out-of-scope questions. Do not use markdown formatting. Politely guide the user back to company-related topics if the conversation veers too far."),
        HumanMessage(content=f"Chat History:\n{chat_history_for_llm}\nUser Query: {latest_user_query}")
    ])

    new_messages = messages + [AIMessage(content=response.content.strip())]
    
    return {
        "generation": response.content.strip(),
        "messages": new_messages,
        "documents": []
    }
    
def secondary_router_node(state: GraphState) -> GraphState:
    print("--SECONDARY ROUTER---")
    messages = state["messages"] # Access messages from state
    
    latest_user_query = _get_latest_human_query(messages)

    # Correct syntax for invoke and correct attribute to get the domain
    response = vector_router.invoke({"question": latest_user_query})
    chosen_domain = response.datasource # Access the 'datasource' attribute from the Pydantic model
    
    print(f"Secondary router chose domain: '{chosen_domain}'")
    
    # Correctly update the state, preserving existing fields
    return {**state, "chosen_domain": chosen_domain}
    
def retrieve(state: GraphState) -> GraphState:
    """
    Retrieves documents from the specific Chroma collection chosen by the secondary router.
    """
    print("---RETRIEVING DOCUMENTS FROM SPECIFIC DOMAIN---")
    messages = state["messages"]
    chosen_domain = state.get("chosen_domain") # Get the chosen domain from the state

    latest_user_query = _get_latest_human_query(messages)
    
    # Check if the chosen_domain is valid and loaded
    if not chosen_domain or chosen_domain not in retriever:
        print(f"Error: Invalid or un-loaded domain '{chosen_domain}' for retrieval. Returning empty documents.")
        return {**state, "documents": []} # Return empty docs but keep other state

    # Get the retriever for the SPECIFIC chosen domain from the loaded_specialized_vectorstores dictionary
    domain_retriever = retriever[chosen_domain].as_retriever(k=4) # k=4 documents

    documents = domain_retriever.invoke(latest_user_query)
    print(f"Retrieved {len(documents)} documents from '{chosen_domain}' collection.")
    
    # Update documents in state, preserve other state fields
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
    documents = state["documents"] # These can be from retrieve or web_search
    
    latest_user_query = _get_latest_human_query(messages)
    
    # Context for the RAG chain should include retrieved documents
    docs_txt = format_docs(documents) # Your helper function from generate.py
    
    # Fallback if no documents are found (e.g., retrieval failed or web search yielded nothing)
    if not docs_txt: # Check if format_docs returns empty string if documents list is empty
        print("No documents available for generation. Generating a fallback response.")
        response = chat_llm.invoke([ # Use chat_llm for a general fallback response
            SystemMessage(content="You are an AI Lead Agent assistant. You could not find specific information in your knowledge base or via web search for the user's request. Politely state that you cannot answer the question based on the available information and offer to help with other company-related queries."),
            HumanMessage(content=latest_user_query)
        ])
        generation = response.content.strip()
    else:
        # Use the powerful LLM for final RAG generation
        generation = rag_chain.invoke({"context": docs_txt, "question": latest_user_query})
    
    # Update messages in state for conversation history with the AI's response
    new_messages = messages + [AIMessage(content=generation)]
    
    # Correctly update the state, preserving existing fields
    return {**state, "messages": new_messages, "generation": generation}

def transform_query(state: GraphState) -> GraphState:
    """
    Rewrites the user's query if initial retrieval was not successful (e.g., no documents found).
    """
    print("---TRANSFORM QUERY---")
    messages = state["messages"]
    latest_user_query = _get_latest_human_query(messages)
    
    # Use question_rewriter to get a better question
    better_question = question_rewriter.invoke({"question": latest_user_query})
    
    # Append the new, rephrased question as a HumanMessage to the messages list
    # The next retrieval step will use this new message.
    new_messages = messages + [HumanMessage(content=better_question, name="rewritten_query")]
    print(f"Original query: '{latest_user_query}'")
    print(f"Transformed query: '{better_question}'")
    
    # Correctly update the state, preserving existing fields
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
        
        # Pass the web results as documents for subsequent generation
        return {**state, "documents": [web_doc]}
    except Exception as e:
        print(f"Error during web search: {e}. Returning empty documents.")
        return {**state, "documents": []}


def leadAgent_workflow():
    workflow = StateGraph(GraphState)

    # Add Nodes
    workflow.add_node("route_question", route_question) # Primary Router Node
    workflow.add_node("chitchat", chitchat)
    workflow.add_node("web_search", web_search)
    workflow.add_node("secondary_router_node", secondary_router_node) # Node for the secondary router
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("generate", generate)
    workflow.add_node("transform_query", transform_query)
    
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
        lambda state: "transform_and_retry" if not state.get("documents") else "end",
        {
            "end": END,
            # "transform_and_retry": "transform_query",
            "transform_and_retry": END
        },
    )
    
    workflow.add_edge("transform_query", "retrieve")

    return workflow.compile()

# # Compile and run the workflow
# if __name__ == "__main__":
#     app = leadAgent_workflow()

#     # Example Usage
#     print("\n--- Running Lead Agent Workflow ---")
    
#     print("\n--- TEST 1: Pricing Query (Primary: Vectorstore -> Secondary: core_ai_system_info -> Retrieve -> Generate) ---")
#     inputs1 = {"messages": [HumanMessage(content="What are the pricing plans for AI-vengers professional tier?")]}
#     # Stream the output
#     for s in app.stream(inputs1):
#         print(s)
#     print("\n--- End TEST 1 ---")

#     print("\n--- TEST 2: General Greeting (Primary: Chitchat -> End) ---")
#     inputs2 = {"messages": [HumanMessage(content="Hello there! How are you doing today?")]}
#     for s in app.stream(inputs2):
#         print(s)
#     print("\n--- End TEST 2 ---")

#     print("\n--- TEST 3: Recent News (Primary: Web Search -> Generate -> End) ---")
#     inputs3 = {"messages": [HumanMessage(content="What are the latest developments in large language models in July 2025?")]}
#     for s in app.stream(inputs3):
#         print(s)
#     print("\n--- End TEST 3 ---")

#     print("\n--- TEST 4: Lead Gen Strategy (Primary: Vectorstore -> Secondary: lead_generate_strategies -> Retrieve -> Generate) ---")
#     inputs4 = {"messages": [HumanMessage(content="What are best practices for qualifying inbound leads?")]}
#     for s in app.stream(inputs4):
#         print(s)
#     print("\n--- End TEST 4 ---")

#     print("\n--- TEST 5: Obscure Query (Primary: Vectorstore -> Secondary: ? -> Retrieve (empty) -> Transform -> Retrieve -> Generate (fallback)) ---")
#     inputs5 = {"messages": [HumanMessage(content="Tell me about the specific features of your obscure product X that nobody knows about.")]}
#     for s in app.stream(inputs5):
#         print(s)
#     print("\n--- End TEST 5 ---")

#     print("\n--- TEST 6: How do I set up Twilio? (Primary: Vectorstore -> Secondary: agent_tools_operations -> Retrieve -> Generate) ---")
#     inputs6 = {"messages": [HumanMessage(content="How do I set up Twilio for an agent?")]}
#     for s in app.stream(inputs6):
#         print(s)
#     print("\n--- End TEST 6 ---")