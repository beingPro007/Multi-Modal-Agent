from typing import Any
from langchain_core.messages import BaseMessageChunk, AIMessage, HumanMessage, SystemMessage
from langgraph.pregel.protocol import PregelProtocol

from livekit.agents import llm, utils
from livekit.agents.llm.chat_context import ChatContext, ChatMessage
from livekit.agents.llm.tool_context import FunctionTool, RawFunctionTool, ToolChoice
from livekit.agents.types import (
    DEFAULT_API_CONNECT_OPTIONS,
    APIConnectOptions,
    NotGivenOr,
    NOT_GIVEN,
)
from langchain_core.runnables import RunnableConfig

def _to_chat_chunk(msg: str | Any) -> llm.ChatChunk | None:
    message_id = utils.shortuuid("LC_")
    content: str | None = None

    if isinstance(msg, str):
        content = msg
    elif isinstance(msg, AIMessage):
        content = msg.content
        if msg.id:
            message_id = msg.id
    elif isinstance(msg, BaseMessageChunk):
        content = msg.text()
        if msg.id:
            message_id = msg.id
    elif isinstance(msg, dict) and "generation" in msg and isinstance(msg["generation"], str):
        content = msg["generation"]
    else:
        print(f"Warning: Unexpected message chunk type in _to_chat_chunk: {type(msg)} - {msg}")
        return None

    if not content:
        return None

    return llm.ChatChunk(
        id=message_id,
        delta=llm.ChoiceDelta(
            role="assistant",
            content=content,
        ),
    )

class MyLangGraphStream(llm.LLMStream):
    def __init__(
        self,
        llm_adapter_instance: 'MyLLMAdapter',
        *,
        chat_ctx: ChatContext,
        tools: list[FunctionTool | RawFunctionTool],
        conn_options: APIConnectOptions,
        graph: PregelProtocol,
        config: RunnableConfig | None = None,
    ):
        super().__init__(
            llm_adapter_instance,
            chat_ctx=chat_ctx,
            tools=tools,
            conn_options=conn_options,
        )
        self._graph = graph
        self._config = config

    async def _run(self) -> None:
        state = self._llm._chat_ctx_to_state(self._chat_ctx)

        async for state_update in self._graph.astream(
            state,
            self._config,
            stream_mode="updates",
        ):
            if "generate" in state_update:
                generated_content = state_update["generate"].get("generation")
                if generated_content:
                    chat_chunk = _to_chat_chunk(generated_content)
                    if chat_chunk:
                        self._event_ch.send_nowait(chat_chunk)

class MyLLMAdapter(llm.LLM):
    def __init__(
        self,
        graph: PregelProtocol,
        *,
        config: RunnableConfig | None = None,
    ) -> None:
        super().__init__()
        self._graph = graph
        self._config = config

    def chat(
        self,
        *,
        chat_ctx: ChatContext,
        tools: list[FunctionTool | RawFunctionTool] | None = None,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
        parallel_tool_calls: NotGivenOr[bool] = NOT_GIVEN,
        tool_choice: NotGivenOr[ToolChoice] = NOT_GIVEN,
        extra_kwargs: NotGivenOr[dict[str, Any]] = NOT_GIVEN,
    ) -> MyLangGraphStream:
        return MyLangGraphStream(
            self,
            chat_ctx=chat_ctx,
            tools=tools or [],
            graph=self._graph,
            conn_options=conn_options,
            config=self._config,
        )

    # This method was originally in LangGraphStream, moved here as discussed
    def _chat_ctx_to_state(self, chat_ctx: ChatContext) -> dict[str, Any]:
        messages: list[AIMessage | HumanMessage | SystemMessage] = []
        for item in chat_ctx.items:
            if isinstance(item, ChatMessage): # Ensure ChatMessage is imported
                content = item.text_content
                if content:
                    if item.role == "assistant":
                        messages.append(AIMessage(content=content, id=item.id))
                    elif item.role == "user":
                        messages.append(HumanMessage(content=content, id=item.id))
                    elif item.role in ["system", "developer"]:
                        messages.append(SystemMessage(content=content, id=item.id))
        return {"messages": messages}