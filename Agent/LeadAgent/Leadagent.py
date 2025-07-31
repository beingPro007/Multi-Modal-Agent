from livekit.agents import Agent
from livekit.plugins import deepgram, aws
from Agent.LeadAgent.workflow import leadAgent_workflow
from Agent.Adapters.LangchainLLMAdapter import MyLLMAdapter

_default_instruction = """
You are LeadAgent, an AI sales assistant for a SaaS product named AI-vengers.

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
            llm=MyLLMAdapter(
                graph=leadAgent_workflow()
            ),
            tts=aws.TTS(voice="Matthew", speech_engine="generative", language="en-US")
        )

    async def on_enter(self):
        await self.session.say(
            "Hi there! I'm Matthew, calling from AI‑vengers. To give you a personalized demo, may I know your company name"
        )