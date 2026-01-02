# WhatsApp Based Online Store Agent

A **WhatsApp-based conversational commerce system** that enables users to discover products, place orders, and create support tickets entirely through chat, powered by an LLM-driven agent and semantic search.

This project treats **chat as the primary interface**, replacing traditional storefront flows with conversational interactions.


The system integrates with **WhatsApp via Twilio**, processes text and voice messages, and routes user requests through an AI agent that combines intent classification, semantic retrieval, and deterministic backend tools.



## High-Level Architecture

![Architecture](https://raw.githubusercontent.com/saaheerpurav/portfolio/refs/heads/master/public/architecture.png)


## Request Flow

1. **User Interaction**

    * Users send text or voice messages via WhatsApp.
    * Messages are delivered through Twilio WhatsApp webhooks.

2. **Webhook Handling**

    * FastAPI receives and validates webhook payloads.
    * User identity is derived from `WaId`.
    * Responses are returned in TwiML format.

3. **Voice Message Handling**

    * Twilio provides media URLs for voice messages.
    * Media URLs are persisted in the users table.
    * Audio is transcribed with OpenAI Whisper
    * Transcribed text follows the same pipeline as text messages.

4. **Intent Classification**

    * A lightweight LLM classifies intent:
      * product search
      * order placement
      * order status
      * support
      * general queries

5. **Execution Routing**

   * **Synchronous path**:

     * Read-only requests (e.g. product listing)
   * **Asynchronous path**:

     * State-changing operations (orders, support tickets)
     * Immediate acknowledgment sent to WhatsApp
     * Processing continues in the background

6. **Tool Execution**

   * Tools are stateless and single-purpose.
   * User identity is injected at runtime by the backend.
   * Tools interact with DynamoDB, Pinecone, and notification systems.

7. **Response Delivery**

   * Final responses are sent back to the user via WhatsApp after processing completes.



## Agent Design

* **LLM-based intent classifier** determines execution flow.
* **Tool-calling agent** performs deterministic actions.
* The LLM does not manage identity or state.
* Follow-up queries rely on persisted message history and semantic re-retrieval.


## Concurrency & Performance

* FastAPI handles concurrent webhook requests.
* Long-running operations are executed asynchronously.
* Webhook responses are never blocked by slow tasks.
* Designed to meet WhatsApp webhook timing constraints.


## Security & Identity

* User identity is derived externally from WhatsApp metadata.
* The LLM never generates or modifies user identifiers.
* All sensitive operations are handled by backend-controlled tools.


## Technology Stack

* **Backend**: FastAPI (Python)
* **Messaging**: Twilio WhatsApp API
* **LLM**: GPT-4o mini
* **Database**: DynamoDB, Pinecone
* **Speech-to-Text**: Whisper
* **Deployment**: Google Cloud Run with Docker


## Status

This project is under active development and focuses on **production-grade agent architecture**, not demo-only behavior.

