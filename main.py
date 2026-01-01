from fastapi import FastAPI, Request, Response, BackgroundTasks
from twilio.twiml.messaging_response import MessagingResponse

from db import update_msg_history, get_message_history, get_user, create_user, append_media
from ai import agent, is_slow_intent
from context import current_user_id
from utils import send_twilio_message, transcribe_twilio_media

app = FastAPI()
"""
uvicorn main:app --reload
"""



def send_delayed_message(to_number: str, messages_payload: list, user_id: str):
    res = agent.invoke({"messages": messages_payload})
    answer = res["messages"][-1].content

    temp_msgs = messages_payload.copy()

    send_twilio_message(to_number, answer)
    temp_msgs.append({"role": "assistant", "content": answer})
    update_msg_history(user_id, temp_msgs)

    print("Sending Delayed Msg ", answer)



@app.get("/")
def home():
    return {"Hello": "World"}



@app.post("/chat")
async def chat_response(request: Request, background_tasks: BackgroundTasks):
    form = await request.form()
    data = dict(form)
    response = MessagingResponse()

    user_id = data["WaId"]
    current_user_id.set(user_id)
    if(get_user(user_id) == None): create_user(user_id, data["From"].replace("whatsapp:", ""), data["ProfileName"], "en")

    # detect and store any incoming media (WhatsApp voice notes arrive as media with audio content types)
    msg = data.get("Body", "")
    num_media = int(data.get("NumMedia", "0"))
    is_audio = False

    if num_media > 0:
        # append all incoming media URLs to the user's `media` list
        for i in range(num_media):
            media_url = data.get(f"MediaUrl{i}")
            if media_url:
                append_media(user_id, media_url)
                # flag if any content type is audio
                if data.get(f"MediaContentType{i}", "").startswith("audio"):
                    is_audio = True

        # transcribe the first audio media (if any)
        transcript = None
        if is_audio:
            for i in range(num_media):
                if data.get(f"MediaContentType{i}", "").startswith("audio"):
                    audio_url = data.get(f"MediaUrl{i}")
                    transcript = transcribe_twilio_media(audio_url)
                    break

            # if audio found but transcription failed, reply with helpful message
            if transcript is None:
                response.message("Sorry, I couldn't transcribe your voice message. Please try again or send text.")
                return Response(
                    content=str(response), media_type="application/xml", status_code=200
                )

            msg = transcript

    messages = get_message_history(user_id)
    messages.append({"role": "user", "content": msg})

    if is_slow_intent(msg) or is_audio:
        # schedule background task to generate and send the full reply via Twilio REST API

        messages_copy = messages.copy()

        background_tasks.add_task(send_delayed_message, data["From"], messages_copy, user_id)
        response.message("Processing your request...")

        return Response(
            content=str(response), media_type="application/xml", status_code=200
        )
    
    else:
        res = agent.invoke({"messages": messages})

        answer = res["messages"][-1].content

        response.message(answer)
        messages.append({"role": "assistant", "content": answer})
        update_msg_history(user_id, messages)

        return Response(
            content=str(response), media_type="application/xml", status_code=200
        )



"""@app.post("/dummypath")
async def get_body(request: Request):
    form = await request.form()
    data = dict(form)
    print(data["WaId"])
    return "abc"   
"""
