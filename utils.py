import smtplib
from email.message import EmailMessage
from twilio.rest import Client
import os
import dotenv
import requests
import io
from openai import OpenAI

dotenv.load_dotenv()
openai_client = OpenAI()

SMTP_HOST = "smtpout.secureserver.net"
SMTP_PORT = 465
SMTP_USER = "saaheer@apexlinkdigital.com"
SMTP_PASSWORD = os.environ["EMAIL_PASSWORD"]

SUPPORT_EMAIL = "saaheer.purav.business@gmail.com"


def send_support_email(user_id: str, issue: str):
    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = SUPPORT_EMAIL
    msg["Subject"] = f"New Support Ticket"

    msg.set_content(
        f"New support ticket created.\n\n" f"User ID: {user_id}\n\n" f"Issue:\n{issue}"
    )

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)


def transcribe_twilio_media(media_url: str):
    """
    Download media from Twilio and transcribe using OpenAI Whisper.
    Returns transcribed text or None on failure.
    """
    try:
        account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        resp = requests.get(media_url, auth=(account_sid, auth_token), timeout=30)
        resp.raise_for_status()

        audio_bytes = resp.content
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "audio.ogg"

        transcript = openai_client.audio.transcriptions.create(
            model="whisper-1", file=audio_file, language="en"
        )

        if isinstance(transcript, dict) and "text" in transcript:
            return transcript["text"]
        return getattr(transcript, "text", None)

    except Exception as e:
        print("Transcription error:", e)
        return None


def send_twilio_message(to_number: str, msg: str):
    try:
        account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        from_number = os.environ.get("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
        client = Client(account_sid, auth_token)

        # send the answer via Twilio REST API to the user's WhatsApp number
        client.messages.create(body=msg, from_=from_number, to=to_number)
        # persist in-memory copy

    except Exception as e:
        print("Error sending delayed message:", e)
