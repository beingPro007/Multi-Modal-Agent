from livekit.agents import Agent
from typing import Annotated, Callable, Optional, cast
from livekit.plugins import aws, deepgram, openai

_default_instruction = """
You are LeadAgent, an AI sales assistant. In each chat:

1. Greet warmly and introduce yourself.
2. Ask 1–2 clear questions to learn their main challenge.
3. Explain in simple terms how our solution helps.
4. Check budget, timeline, and decision‑maker.
5. Propose a single clear next step (e.g., a short call or demo).
6. Wrap up by summarizing and confirming that next step.

Keep it friendly, brief, and focused.
"""

class LeadAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=_default_instruction,
            stt=deepgram.STT(),
            llm=openai.LLM.with_cerebras(model="llama3.1-8b", temperature=0.1),
            tts=aws.TTS(voice="Matthew", speech_engine="neural", language="en-US")
        )
        
    async def on_enter(self):
        self.session.say(
            "Hi there! I'm LeadAgent. Can I ask a quick question about your main challenge today?"
        )
    