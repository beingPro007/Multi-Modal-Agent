from livekit.agents import Agent, function_tool, RunContext
from livekit.plugins import aws, deepgram, openai
from utils.rag_utils import search_docs
from collections.abc import AsyncIterable
from typing import cast
from pydantic_core import from_json
from livekit.agents.llm.llm import ChatChunk
from livekit.agents import ChatContext, FunctionTool, ModelSettings
from livekit.plugins import openai

_default_instruction = """
You are LeadAgent, an AI sales assistant for a SaaS product named AI-vengers.

You have access to internal documentation via the `query_product_info` tool.

Your behavior rules:
- ALWAYS call the `query_product_info` tool whenever the user asks about technical topics like SIP setup, pricing, Twilio integration, or product features.
- EVEN IF you think you know the answer, still call the tool first.
- On Every tool call, check the result:
  - If the result is in JSON format or looks incomplete or like `None`, call `query_product_info` again with the same query.
  - Repeat this until you get a proper, clear response string.

Then, summarize the result in a speech-friendly and helpful tone.

In each chat:
1. Greet and ask about the user’s needs.
2. Use the tool if there’s a product-related or technical question.
3. Keep responses clear and concise.
4. Ask about the user's budget or next steps.
5. Confirm before ending.

Never output markdown, long blocks, or raw JSON.
Always act like a friendly, helpful voice agent.
"""

class LeadAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=_default_instruction,
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=aws.TTS(voice="Matthew", speech_engine="neural", language="en-US")
        )

    async def on_enter(self):
        await self.session.say(
            "Hi there! I'm Matthew, calling from AI‑vengers. Would you like an agent to automate business tasks?"
        )

    @function_tool()
    async def query_product_info(
        self,
        context: RunContext,
        query: str,
    ) -> str:
        results = search_docs(query)
        print("RAG Result: ", results)
        return results

    async def llm_node(
        self,
        chat_ctx: ChatContext,
        tools: list[FunctionTool],
        model_settings: ModelSettings,
    ) -> AsyncIterable[str]:
        llm = cast(openai.LLM, self.llm)
        tool_choice = model_settings.tool_choice if model_settings else NOT_GIVEN

        full_response = ""
        async with llm.chat(
            chat_ctx=chat_ctx,
            tools=tools,
            tool_choice=tool_choice,
        ) as stream:
            async for chunk in stream:
                # full_response += chunk.delta.content
                yield chunk

            # Post-process: if the LLM output looks like function call JSON
            try:
                parsed = from_json(full_response)
                if isinstance(parsed, dict) and parsed.get("name") == "query_product_info":
                    query_txt = parsed["parameters"]["query"]
                    self.logger.info(f"Detected tool call skip; re-invoking manually for '{query_txt}'")
                    tool_res = await self.query_product_info(chat_ctx, query_txt)
                    yield f"Here's what I found: {tool_res}"
            except Exception:
                pass