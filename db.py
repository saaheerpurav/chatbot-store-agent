import boto3
from boto3.dynamodb.conditions import Key

import datetime
import uuid
import dotenv

dotenv.load_dotenv()

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("users")
orders_table = dynamodb.Table("orders")
products_table = dynamodb.Table("products")



def create_order_in_db(user_id: str, product_id: str):
    order_id = f"ORD-{uuid.uuid4().hex[:8]}"
    eta = (datetime.datetime.utcnow() + datetime.timedelta(days=5)).date().isoformat()

    res = products_table.get_item(Key={"product_id": product_id})

    if "Item" not in res:
        return "Invalid product_id"

    orders_table.put_item(
        Item={
            "order_id": order_id,
            "user_id": user_id,
            "product_id": product_id,
            "status": "processing",
            "eta": eta,
            "created_at": datetime.datetime.utcnow().isoformat()
        }
    )

    return {
        "order_id": order_id,
        "status": "processing",
        "eta": eta
    }

def get_order(user_id):
    response = orders_table.query(
        IndexName="user_id-index",
        KeyConditionExpression=Key("user_id").eq(user_id)
    )
    out = []
    
    for i in  response.get("Items", []):
        temp = i
        res = products_table.get_item(
            Key={"product_id": i["product_id"]}
        )
        item = res.get("Item")
        temp["name"] = item["name"]
        temp["price"] = item["price"]
        out.append(temp)

    return out





def create_user(user_id, phone, name, language):
    #user_id = str(uuid.uuid4())
    timestamp = datetime.datetime.now(datetime.UTC).isoformat()

    item = {
        "id": user_id,
        "created_at": timestamp,
        "phone": phone,
        "name": name,
        "language": language,
        "message_history": [],  # Start empty
        "media": [],  # store media URLs (e.g., voice notes, images)
    }

    table.put_item(Item=item)
    return item


# Example
"""new_user = create_user(
    phone="+15551234567",
    name="John Doe",
    language="en"
)
print(new_user)"""

SYSTEM_PROMPT = """
You are an AI assistant responsible for managing orders in an online store.

You have access to tools to perform actions such as:
- create_order
- lookup_order_status
- create_support_ticket
- list_all_products

Rules:
- When an action is required, call the appropriate tool.
- Do NOT describe what you will do — call the tool directly.
- Do NOT invent product IDs, order IDs, or user data.
- Only respond in natural language AFTER a tool has been successfully executed.
- If a request cannot be completed, explain the reason clearly.

Behavior:

- Buying intent → create_order
- Status inquiry or Show orders → lookup_order_status
- Problem, complaint or cancel order → create_support_ticket
- General questions → answer normally using available context

You are a transactional assistant focused on correctness and reliability.
Do NOT AT ALL make up any ids, JUST pass null

For ANY HEADER or SUBHEADER, ONLY put it in single asterisk (*) and NO DOUBLE ASTERISK
eg ONLY *ORDER ID** and NOT **ORDER ID*
"""


def get_user(user_id):
    response = table.get_item(Key={"id": user_id})
    return response.get("Item")

def get_message_history(user_id):
    temp: list = get_user(user_id)["message_history"]
    if len(temp) == 0:
        temp.append({"role": "system", "content": SYSTEM_PROMPT})

    return temp


def append_message(user_id, message):
    table.update_item(
        Key={"id": user_id},
        UpdateExpression="SET message_history = list_append(message_history, :msg)",
        ExpressionAttributeValues={":msg": [message]},  # must be a list
    )


def append_media(user_id, media_url: str):
    """Append a media URL to the user's `media` list. Creates the list if it does not exist."""
    table.update_item(
        Key={"id": user_id},
        UpdateExpression="SET media = list_append(if_not_exists(media, :empty), :m)",
        ExpressionAttributeValues={":m": [media_url], ":empty": []},
    )

def update_msg_history(user_id, msgs):
    table.update_item(
        Key={"id": user_id},
        UpdateExpression="SET message_history = :msgs",
        ExpressionAttributeValues={":msgs": msgs}
    )



"""append_message(
    "c0fa2df5-65ef-49d0-bdc4-81cd5bbd6e60",
    {
        "role": "user",
        "content": "Hello!",
    },
)
"""
