import asyncio
import os
import json
from dotenv import load_dotenv
import time

from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, RoomInputOptions, ChatContext, ChatMessage, ChatRole, cli, JobProcess, AutoSubscribe, RoomOutputOptions, UserInputTranscribedEvent
from livekit.plugins import deepgram, silero, aws, openai, noise_cancellation
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

                response = await generate_modality_aware_response(session, input_modality="text")

                # Step 3: Respond based on modality
                if response["output_modality"] == "voice":
                    print("NEED TO SAY")
                    await session.say(response["message"])
                else:
                    print("NEED TO SEND TO CHAT")
                    await ctx.room.local_participant.publish_data(
                        json.dumps(response), reliable=True, topic="lk.chat"
                    )
            except Exception as e:
                print("Error in data channel:", e)
        asyncio.create_task(process_data())
    return data_handler



async def generate_modality_aware_response(session: AgentSession, input_modality: str):
    try:
        await session._agent.update_chat_ctx(session.history)
        
        prompt = (
            "You are an assistant choosing between voice or chat delivery. "
            f"User input modality: '{input_modality}'. "
            "Default to voice unless content is sensitive (passwords, OTPs, tokens). "
            "Use chat only if security reasons or user explicitly requests chat. "
            "Respond strictly with valid JSON: {\"output_modality\": \"voice\" or \"chat\", \"message\": \"...\"}."
        )
        system_msg = ChatMessage(role="system", content=[prompt])
        ctx = ChatContext(items=[system_msg] + session.history.items.copy())


        full_response = ""
        async for chunk in session.llm.chat(chat_ctx=ctx):
            if getattr(chunk, "delta", None) and getattr(chunk.delta, "content", None):
                full_response += chunk.delta.content

        print("Raw response from LLM:", full_response)

        return json.loads(full_response)

    except Exception as e:
        print("Error generating modality-aware response:", e)
        return {"output_modality": "chat", "message": "Sorry, something went wrong while generating a response."}

class MultiModalAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions="You are Gautam Rana, a helpful assistant.",
            stt=deepgram.STT(),
            llm=openai.LLM.with_cerebras(model="llama3.1-8b", temperature=0.1),
            tts=aws.TTS(voice="Ruth", speech_engine="neural", language="en-US"),
        )

    async def on_enter(self):
        await self.session.generate_reply(instructions="Hello, How can I assist you today?")

async def outbound_entrypoint(ctx: JobContext):
    try:
        await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)
        print("Connected to room:", ctx.room.name)

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

        session = AgentSession(
            vad=ctx.proc.userdata["vad"],
            turn_detection=EnglishModel()
        )

        def on_track_subscribed(participant, track):
            print(f"Track subscribed: {track.name}, kind={track.kind}")
        ctx.room.on("track_subscribed", on_track_subscribed)

        await session.start(
            room=ctx.room,
            agent=MultiModalAgent(),
            room_input_options=RoomInputOptions(
                audio_enabled=True,
                text_enabled=True,
                noise_cancellation=noise_cancellation.BVC()
            ),
        )

        @session.on("user_input_transcribed")
        def on_user_input_transcribed(event: UserInputTranscribedEvent):
            print(f"User input transcribed: {event.transcript}, final: {event.is_final}, speaker id: {event.speaker_id}")
            if event.is_final:
                session.history.add_message(role="user", content=[event.transcript])
                
                async def process():
                    response = await generate_modality_aware_response(session, input_modality="voice")
                    
                    if response["output_modality"] == "voice":
                        print("NEED TO SAY")
                        await session.say(response["message"])
                    else:
                        print("NEED TO SEND TO CHAT")
                        await ctx.room.local_participant.publish_data(
                            json.dumps(response), reliable=True, topic="lk.chat"
                        )
                asyncio.create_task(process())
                
        ctx.room.on("data_received", await handle_data_channel(ctx, session))

        def on_disconnect(participant):
            if participant.identity == user_id:
                print("SIP participant disconnected, scheduling cleanup.")
                async def cleanup():
                    try:
                        ctx.shutdown(reason="participant_disconnected")
                        print("Context shutdown initiated.")
                    except Exception as e:
                        print("Error during shutdown:", e)
                asyncio.create_task(cleanup())
        ctx.room.on("participant_disconnected", on_disconnect)
        
    except Exception as e:
        print(f"Eror occured {e}")


async def webrtc_entrypoint(ctx: JobContext):
    session = AgentSession(
            vad=ctx.proc.userdata["vad"],
            turn_detection=EnglishModel()
    )
    
    try:
        await session.start(
                room=ctx.room,
                agent=MultiModalAgent(),
                room_input_options=RoomInputOptions(
                    audio_enabled=True,
                    text_enabled=True,
                    noise_cancellation=noise_cancellation.BVC()
                ),
        )
    except Exception as e:
        print(f"Session failed to start: {e}")


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

if __name__ == "__main__":
    cli.run_app(WorkerOptions(prewarm_fnc=prewarm, entrypoint_fnc=outbound_entrypoint, agent_name="adaptive-multimodal-agent"))
