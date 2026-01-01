# Copilot / Agent Instructions for this repository ✅

Purpose: Help AI coding agents (Copilot, assistants) be productive quickly by documenting the architecture, developer workflows, conventions, and integration points discovered in the codebase.

---

## Quick start (local) 🔧
- Set required environment variables in a `.env` file at project root:
  - PINECONE_API_KEY
  - EMAIL_PASSWORD
  - TWILIO_ACCOUNT_SID
  - TWILIO_AUTH_TOKEN
  - TWILIO_WHATSAPP_NUMBER (optional — default used if not set)
  - OPENAI_API_KEY (required for voice message transcription when using Whisper / OpenAI Speech-to-Text)
  - AWS credentials (for boto3/DynamoDB) via the usual environment variables or shared credentials file.
- Run locally (dev): `uvicorn main:app --reload` (or use Dockerfile described below).
- To test Twilio webhook locally: expose `http://localhost:80/chat` using ngrok and configure your Twilio webhook to point to the public URL.

## Build & Docker 🐳
- Image build and run (from project root):
  - `docker build -t agent-container .`
  - `docker run -p 80:80 --env-file .env agent-container`
- Dockerfile uses Python 3.12 and runs `uvicorn main:app --host 0.0.0.0 --port 80`.

## High-level architecture & major components 🏗️
- FastAPI app in `main.py` exposes:
  - `POST /chat` — Twilio webhook that accepts WhatsApp messages (form-data) and returns TwiML.
  - `GET /` — simple health endpoint.
- Agent layer in `ai.py`:
  - Uses LangChain agents (`create_agent`) and tools (decorated with `@tool`).
  - Vector store for RAG is Pinecone via `PineconeVectorStore` and `OpenAIEmbeddings`.
  - Primary agent model: `gpt-4o-mini` (defined in `ai.py`).
  - Important tools: `list_all_products`, `create_order`, `lookup_order_status`, `create_support_ticket`.
- Persistence & state in `db.py`:
  - DynamoDB tables: `users`, `orders`, `products`.
  - `orders` has a GSI `user_id-index` used in `get_order(user_id)`.
  - User state includes `message_history` (list of chat messages) and a `SYSTEM_PROMPT` injected when history is empty.
- Utilities in `utils.py`:
  - `send_twilio_message` (Twilio REST client)
  - `send_support_email` (SMTP client, uses `EMAIL_PASSWORD` env var)
- Concurrency context:
  - `context.current_user_id` is a ContextVar used to pass user id into tool logic without changing function signatures.

## Important workflows & patterns ⚙️
- Intent classification: `is_slow_intent(message)` in `ai.py` creates a small classifier-agent to decide whether to reply synchronously or enqueue a background task.
- Background reply path (slow/intensive flows): `main.py` schedules `send_delayed_message` using FastAPI `BackgroundTasks`, which invokes `agent.invoke(...)` then sends a Twilio message via `send_twilio_message`.
- Message history behavior: `get_message_history` returns `message_history` from DynamoDB; if empty it appends the `SYSTEM_PROMPT` (see `db.py`).
- Tool I/O conventions:
  - Tools use `@tool(response_format=...)` to specify return structure.
  - `list_all_products` returns `(serialized_content, docs)` (content_and_artifact); callers expect both.
  - `create_order` expects *product name* (not product ID); product IDs come from vectorstore metadata (`product_id`).

## Integration points & expectations 🔗
- Pinecone vector index: named `index3` (set in `ai.py`). When adding products to the vector index, include `metadata` keys: `product_id`, `name`, `price` so downstream tools can rely on them.
- DynamoDB: code expects tables named exactly `users`, `orders`, `products`. `orders` must have a GSI on `user_id` named `user_id-index`.
- Twilio: webhook payload example is in `main.py` — expect `WaId` (user id), `From` (phone), `Body` (message text), and `ProfileName`. Voice notes arrive as media (set `NumMedia` > 0); the code checks `MediaContentType0` to detect audio and downloads `MediaUrl0` (authenticated with your Twilio creds) and transcribes with OpenAI (Whisper) when `OPENAI_API_KEY` is present.
- SMTP: uses GoDaddy SMTP host in `utils.py` and `EMAIL_PASSWORD` from env.

## Project-specific conventions & gotchas ⚠️
- System prompt formatting rule in `db.py` **must be preserved**: When placing headings in the assistant output, they are explicitly required to use single asterisks (`*HEADER*`) instead of double asterisks. Agents may rely on this.
- Agent calls: Use `agent.invoke({'messages': messages})` and expect the assistant reply at `res['messages'][-1].content`.
- Product matching flow: `get_product_id(...)` uses vectorstore similarity + `relativity_checker(...)` (a separate agent); do NOT assume similarity_search result is 1:1 — `relativity_checker` enforces a strict true/false.
- DynamoDB timestamps and timezone: `create_user()` attempts `datetime.now(datetime.UTC)` (likely a bug — `datetime.UTC` is not standard); be cautious when editing time handling.
- Requirements file and package names have minor inconsistencies (e.g., stray whitespace in `langchain== 1.1.2`) — prefer using pinned versions as-is but check builds if you change package lines.

## Safe, minimal edits an AI assistant can make ✅
- Small refactors to improve clarity in `ai.py` or `main.py` (e.g., extract repeated code into helper functions), provided unit tests or manual runtime checks are added.
- Add logging to `send_delayed_message` and Twilio send code for better observability.
- Fix minor typos and formatting issues (requirements spacing, docstrings).

## Risky changes — ask human first 🛑
- Changing the `SYSTEM_PROMPT` content or its formatting rule — this affects chat behavior and persisted histories.
- Renaming DynamoDB table names or changing table schemas without first verifying infrastructure (cloud formation / manual tables) because the code assumes exact table names and indexes.
- Changing the agent model string (e.g., `gpt-4o-mini`) for behavior-sensitive logic without A/B testing.

---

If any section is unclear or you want more examples (sample messages payloads, typical Twilio webhook sample, or an onboarding checklist), tell me which areas to expand and I will iterate. ✨
