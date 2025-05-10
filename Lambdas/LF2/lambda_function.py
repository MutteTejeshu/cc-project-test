import sys
sys.path.append("/opt")
import json
import boto3
from botocore.exceptions import ClientError
import logging
import requests
import random
from boto3.dynamodb.conditions import Key, Attr

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def receive_messages(queue, max_number, wait_time):
    try:
        messages = queue.receive_messages(
            MessageAttributeNames=["All"],
            MaxNumberOfMessages=max_number,
            WaitTimeSeconds=wait_time,
        )
        for msg in messages:
            logger.info("Received message: %s: %s", msg.message_id, msg.body)
    except ClientError as error:
        logger.exception("Couldn't receive messages from queue: %s", queue)
        raise error
    else:
        return messages

def delete_message(message):
    try:
        message.delete()
        logger.info("Deleted message: %s", message.message_id)
    except ClientError as error:
        logger.exception("Couldn't delete message: %s", message.message_id)
        raise error

def get_restaurant_ids(cuisine_request):
    query = "####://##########################################################/restaurants/_search?q={cuisine}".format(cuisine = cuisine_request)
    response = requests.get(query, auth=("#########", "##########"))
    data = json.loads(response.content.decode("utf-8"))
    try:
        esData = data["hits"]["hits"]
    except KeyError:
        logger.debug("Error extracting hits from ES response")
    restaurant_ids = []
    nums = random.sample(range(0, len(esData)), 5)
    for i in range(5):
        restaurant_ids.append(esData[nums[i]]["_source"]["Business_ID"])
    print(restaurant_ids)
    return restaurant_ids

def get_all_attrs_dynamodb(restaurant_ids):
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    table = dynamodb.Table("yelp-restaurants")
    restaurant_attrs = []
    for restaurant_id in restaurant_ids:
        response = table.query(KeyConditionExpression=Key("business_id").eq(restaurant_id))
        restaurant_attrs.append(response["Items"][0])
    return restaurant_attrs

def send_email(message_body, restaurant_attrs):
    ses = boto3.client("ses")
    response = ses.send_email(
        Source="tm4258@nyu.edu",
        Destination={
            "ToAddresses": [message_body["Email"]]
        },
        Message={
            "Subject": {
                "Data": "Restaurant Recommendations"
            },
            "Body": {
                "Text": {
                    "Data": """Here are your {} restaurant recommendations for {} people in {} for {} at {}: \n 
                    1. {}, located at {} \n 
                    2. {}, located at {} \n 
                    3. {}, located at {} \n 
                    4. {}, located at {} \n 
                    5. {}, located at {} 
                    \n Enjoy your meal!""".format(
                        message_body["Cuisine"].lower().capitalize(),
                        message_body["NumberOfPeople"],
                        message_body["Location"],
                        message_body["DiningDate"],
                        message_body["DiningTime"],
                        restaurant_attrs[0]["name"],
                        restaurant_attrs[0]["address"],
                        restaurant_attrs[1]["name"],
                        restaurant_attrs[1]["address"],
                        restaurant_attrs[2]["name"],
                        restaurant_attrs[2]["address"],
                        restaurant_attrs[3]["name"],
                        restaurant_attrs[3]["address"],
                        restaurant_attrs[4]["name"],
                        restaurant_attrs[4]["address"],
                    )
                }
            }
        }
    )

def send_email2(message_body, restaurant_attrs):
    ses = boto3.client("ses")
    response = ses.send_email(
        Source="tm4258@nyu.edu",
        Destination={
            "ToAddresses": [message_body["Email"]]
        },
        Message={
            "Subject": {
                "Data": "Restaurant Recommendations"
            },
            "Body": {
                "Text": {
                    "Data": """Here are your {} restaurant recommendations in {}: \n 
                    1. {}, located at {} \n 
                    2. {}, located at {} \n 
                    3. {}, located at {} \n 
                    4. {}, located at {} \n 
                    5. {}, located at {} 
                    \n Enjoy your meal!""".format(
                        message_body["Cuisine"].lower().capitalize(),
                        message_body["Location"],
                        restaurant_attrs[0]["name"],
                        restaurant_attrs[0]["address"],
                        restaurant_attrs[1]["name"],
                        restaurant_attrs[1]["address"],
                        restaurant_attrs[2]["name"],
                        restaurant_attrs[2]["address"],
                        restaurant_attrs[3]["name"],
                        restaurant_attrs[3]["address"],
                        restaurant_attrs[4]["name"],
                        restaurant_attrs[4]["address"],
                    )
                }
            }
        }
    )

def lambda_handler(event, context):
    sqs = boto3.resource("sqs")
    queue = sqs.get_queue_by_name(QueueName="RequirementsQueue")
    
    messages = receive_messages(queue, 1, 5)
    if not messages:
        logger.warning("No messages found in SQS queue.")
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "No messages found in queue"})
        }
    message = messages[0]
    print(message)
    message_body = json.loads(message.body)
    cuisine_request = message_body["Cuisine"]
    cuisine_request = message_body["Cuisine"].lower().capitalize()
    email = message_body["Email"]
    print(cuisine_request)
    print(email)

    delete_message(message)

    restaurant_ids = get_restaurant_ids(cuisine_request)
    
    all_restaurant_attrs = get_all_attrs_dynamodb(restaurant_ids)
    print(all_restaurant_attrs)

    if len(message_body) < 5:
        send_email2(message_body, all_restaurant_attrs)
    else:
        send_email(message_body, all_restaurant_attrs)

    return {
        'statusCode': 200
    }




