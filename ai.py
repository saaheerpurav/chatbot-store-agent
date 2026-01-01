# chatbot.py

from langchain_pinecone import PineconeVectorStore
from langchain.tools import tool
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

import os
import dotenv
from pinecone import Pinecone
from langchain_openai import OpenAIEmbeddings

from db import create_order_in_db, get_order
from utils import send_support_email
from context import current_user_id

dotenv.load_dotenv()

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
INDEX_NAME = "index3"
index = pc.Index(INDEX_NAME)

# --- Create VectorStore + Retriever ---
vectorstore = PineconeVectorStore.from_existing_index(
    index_name=INDEX_NAME, embedding=embeddings
)

retriever = vectorstore.as_retriever()

# USER_ID = "c0fa2df5-65ef-49d0-bdc4-81cd5bbd6e60"


# --- RAG Tool for agent ---
@tool(response_format="content_and_artifact")
def list_all_products(query: str):
    """
    Gives the list of products, ONLY list product name and price
    """

    docs = retriever.invoke(query)

    serialized = "\n\n".join(
        f"Content: {doc.page_content}\nMetadata: {doc.metadata}" for doc in docs
    )

    return serialized, docs


def get_product_id(query: str):
    docs = vectorstore.similarity_search(query, k=1)

    res = [
        {
            "product_id": doc.metadata["product_id"],
            "name": doc.metadata["name"],
            "price": doc.metadata["price"],
        }
        for doc in docs
    ]

    rel = relativity_checker(res[0]["name"], query)

    if rel:
        return res[0]["product_id"]

    else:
        return None


@tool(response_format="content")
def create_order(query: str):
    """
    Creates an order
    Input ONLY product name
    Outputs the order_id, status and ETA. Give user this information
    """
    prodcut_id = get_product_id(query)

    if prodcut_id is None:
        return "product_not_found"
    else:
        user_id = current_user_id.get()
        res = create_order_in_db(user_id, prodcut_id)

        return res


@tool(response_format="content")
def create_support_ticket(query: str):
    """
    Create a support ticket
    """

    user_id = current_user_id.get()
    send_support_email(user_id, query)

    return ("Your support ticket has been created.",)


@tool(response_format="content")
def lookup_order_status():
    """
    Returns the order status.
    Give user the order id, product name, eta, created at, status
    """

    user_id = current_user_id.get()
    res = get_order(user_id)

    return res


agent = create_agent(
    model="gpt-4o-mini",
    tools=[
        list_all_products,
        create_order,
        lookup_order_status,
        create_support_ticket,
    ],
)


INTENTS = [
    "SEARCH",  # list / find products
    "ORDER",  # place / buy order
    "STATUS",  # order status
    "SUPPORT",  # issues / complaints
    "GENERAL",  # FAQs / chit-chat
]


def is_slow_intent(message):
    classifier_agent = create_agent(
        model="gpt-4o-mini",
        system_prompt=f"""
You are an intent classifier for an ecommerce assistant.

Classify the user message into ONE of:
{", ".join(INTENTS)}

Message: "{message}"

Respond with ONLY the intent.
""",
    )
    res = classifier_agent.invoke({"messages": [{"role": "user", "content": message}]})
    answer = res["messages"][-1].content
    return answer in {"ORDER", "SUPPORT"}


def relativity_checker(relavant_product, user_input):
    relavance_agent = create_agent(
        model="gpt-4o-mini",
        system_prompt=f"""
You are a product relavance classifier for an ecommerce assistant.
You will have to check is user inputted product is the same as a product retrieved from the vector store
Product from vector store: {relavant_product}
ONLY OUTPUT true or false NOTHING ELSE
""",
    )
    res = relavance_agent.invoke(
        {"messages": [{"role": "user", "content": user_input}]}
    )
    answer = res["messages"][-1].content

    return answer.lower() == "true"
