import asyncio
import os
import json
from dotenv import load_dotenv
import time

from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, RoomInputOptions, cli, JobProcess, AutoSubscribe, RoomOutputOptions
from livekit.plugins import deepgram, silero, aws, openai, noise_cancellation, cartesia
from livekit.rtc import DataPacket
from livekit.plugins.turn_detector.english import EnglishModel
from livekit import api

load_dotenv()

outbound_trunk_id = os.getenv("SIP_OUTBOUND_TRUNK_ID")
if not outbound_trunk_id or not outbound_trunk_id.startswith("ST_"):
    raise ValueError("SIP_OUTBOUND_TRUNK_ID is not set or invalid")

async def handle_data_channel(ctx: JobContext, session: AgentSession):
    def data_handler(packet: DataPacket):
        async def process_data():
            try:
                text = packet.data.decode("utf-8")
                print("[DATA RECEIVED]", text)
                session.history.add_message(role="user", content=[text])
                await session._agent.update_chat_ctx(session.history)

                full_resp = ""
                async for chunk in session.llm.chat(chat_ctx=session.history):
                    if getattr(chunk, 'delta', None) and getattr(chunk.delta, 'content', None):
                        full_resp += chunk.delta.content

                await ctx.room.local_participant.publish_data(full_resp, reliable=True, topic="lk.chat")
            except Exception as e:
                print("Error in data channel:", e)
        asyncio.create_task(process_data())
    return data_handler

class MultiModalAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions=(
                "You are Yash Tamakuwala, a representative of Propelius Technologies, speaking on behalf of the company. "
                "Propelius is a boutique software studio with around 50 team members, based in Surat, India. "
                "You help startups and enterprises launch MVPs and new features through 90-day fixed-price sprints, "
                "or by embedding senior React, Node.js, and AI engineers into their teams. "
                "Your role is to explain Propelius's offerings, answer any questions, and guide potential clients clearly and professionally. "
                "You specialize in web and mobile development, SaaS platforms, UI/UX, QA, AI automation, cloud scalability, and blockchain solutions. "
                "You communicate with confidence, clarity, and a helpful attitude, representing the company with professionalism."
            )
        )

    async def on_enter(self):
        await self.session.generate_reply(
            instructions="Hi, this is Yash from Propelius Technologies. I wanted to check if you'd be interested in collaborating with us on any upcoming tech initiatives. How can I help you today?"
        )


async def outbound_entrypoint(ctx: JobContext):
    try:
        await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)
        print("Connected to room:", ctx.room.name)

        # Initiate SIP call
        metadata = json.loads(ctx.job.metadata or "{}")
        phone = metadata.get("phone_number")
        if not phone:
            raise ValueError("Missing phone_number in metadata")

        user_id = "outbound_callee"
        await ctx.api.sip.create_sip_participant(api.CreateSIPParticipantRequest(
            room_name=ctx.room.name,
            sip_trunk_id=outbound_trunk_id,
            sip_call_to=phone,
            participant_identity=user_id,
        ))

        participant = await ctx.wait_for_participant(identity=user_id)
        start = time.time()
        while True:
            status = participant.attributes.get("sip.callStatus")
            if status == "active":
                break
            if status in ["terminated", "rejected"]:
                print(f"Call status {status}, aborting.")
                return
            if status == "ringing" and time.time() - start > 10:
                await ctx.api.room.delete_room(api.DeleteRoomRequest(room=ctx.room.name))
                return
            await asyncio.sleep(0.5)

        # Create a fresh AgentSession per call
        session = AgentSession(
            stt=deepgram.STT(),
            llm=openai.LLM.with_cerebras(model="llama3.1-8b", temperature=0.1),
            tts=cartesia.TTS(),
            vad=ctx.proc.userdata["vad"],
            turn_detection=EnglishModel()
        )

        # Subscribe to track events correctly
        def on_track_subscribed(participant, track):
            print(f"Track subscribed: {track.name}, kind={track.kind}")
        ctx.room.on("track_subscribed", on_track_subscribed)

        # Start session with audio enabled explicitly
        await session.start(
            room=ctx.room,
            agent=MultiModalAgent(),
            room_input_options=RoomInputOptions(
                audio_enabled=True,
                text_enabled=True,
                noise_cancellation=noise_cancellation.BVC()
            ),
            room_output_options=RoomOutputOptions(transcription_enabled=True)
        )

        # Log transcriptions
        @session.on("user_input_transcribed")
        def on_transcribed(evt):
            print("RECOGNIZED:", evt.transcript, "final?", evt.is_final)

        # Handle data channel
        ctx.room.on("data_received", await handle_data_channel(ctx, session))

        # Clean up on disconnect using a synchronous handler that schedules an async task
        def on_disconnect(participant):
            if participant.identity == user_id:
                print("SIP participant disconnected, scheduling cleanup.")
                async def cleanup():
                    # Gracefully shutdown the agent session via LiveKit context
                    try:
                        ctx.shutdown(reason="participant_disconnected")
                        print("Context shutdown initiated.")
                    except Exception as e:
                        print("Error during shutdown:", e)
                asyncio.create_task(cleanup())
        ctx.room.on("participant_disconnected", on_disconnect)
    except Exception as e:
        print(f"Eror occured {e}")

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

if __name__ == "__main__":
    cli.run_app(WorkerOptions(prewarm_fnc=prewarm, entrypoint_fnc=outbound_entrypoint, agent_name="adaptive-multimodal-agent"))
