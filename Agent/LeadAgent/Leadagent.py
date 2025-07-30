from livekit.agents import Agent, function_tool, RunContext
from livekit.plugins import deepgram, openai, langchain, aws
from utils.rag_utils import search_docs
from collections.abc import AsyncIterable
from typing import cast
from pydantic_core import from_json
from livekit.agents import ChatContext, FunctionTool, ModelSettings
from livekit.plugins import openai
from Agent.LeadAgent.workflow import leadAgent_workflow
from Agent.Adapters.LangchainLLMAdapter import MyLLMAdapter

_default_instruction = """
You are Matthew, the AI-vengers sales assistant.
You can handle:
  - Casual greetings and introductions.
  - Answering your own name.
  - Then, qualifying leads by asking for company name, pain points, etc.
When you receive greetings or name questions, reply naturally and don’t invoke the lead‐gen graph.
"""

class LeadAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=_default_instruction,
            stt=deepgram.STT(),
            llm=MyLLMAdapter(
                graph=leadAgent_workflow()
            ),
            tts=aws.TTS(voice="Matthew", speech_engine="generative", language="en-US")
        )

    async def on_enter(self):
        await self.session.say(
            "Hi there! I'm Matthew, calling from AI‑vengers. Can you go ahead and tell what is real Challenges your company is currently facing."
        )