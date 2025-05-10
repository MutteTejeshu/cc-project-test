import json
from utils import elicit_slot, close, delegate, validate_restaurant_suggestion, greet, thank_you, elicit_confirmation
import boto3
from boto3.dynamodb.conditions import Key, Attr

def check_previous_suggestions(email):
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    table = dynamodb.Table("state-information")

    response = table.query(KeyConditionExpression=Key("Email").eq(email))

    if len(response["Items"]) > 0:
        return response["Items"][0]
    return None

def suggest_restaurant(intent_request):

    intent_name = intent_request['sessionState']['intent']['name']
    slots = intent_request['sessionState']['intent']['slots']
    session_attributes = intent_request['sessionState']['sessionAttributes'] if intent_request['sessionState'].get('sessionAttributes') else {}
    
    print(slots)
    print(intent_name)
    print(session_attributes)
    print(intent_request['sessionState']['intent'])
    
    confirmation_state = intent_request['sessionState']['intent'].get('confirmationState')

    location = slots['Location']['value']['interpretedValue'] if slots.get('Location') and slots['Location'].get('value') and slots['Location']['value'].get('interpretedValue') else None
    dining_time = slots['DiningTime']['value']['interpretedValue'] if slots.get('DiningTime') and slots['DiningTime'].get('value') and slots['DiningTime']['value'].get('interpretedValue') else None
    cuisine = slots['Cuisine']['value']['interpretedValue'] if slots.get('Cuisine') and slots['Cuisine'].get('value') and slots['Cuisine']['value'].get('interpretedValue') else None
    number_of_people = slots['NumberOfPeople']['value']['interpretedValue'] if slots.get('NumberOfPeople') and slots['NumberOfPeople'].get('value') and slots['NumberOfPeople']['value'].get('interpretedValue') else None
    email = slots['Email']['value']['interpretedValue'] if slots.get('Email') and slots['Email'].get('value') and slots['Email']['value'].get('interpretedValue') else slots['Email']['value']['originalValue'] if slots.get('Email') and slots['Email'].get('value') and slots['Email']['value'].get('originalValue') else None
    dining_date = slots['DiningDate']['value']['interpretedValue'] if slots.get('DiningDate') and slots['DiningDate'].get('value') and slots['DiningDate']['value'].get('interpretedValue') else None

    print(f"Type of email: {type(email)}, Value: {email}")

    if confirmation_state == "Confirmed":
        if not email and "email" in session_attributes:
            email = session_attributes["email"]
        previous_suggestions = check_previous_suggestions(email)
        if previous_suggestions and not dining_time:
            message_body = json.dumps({
                "Location": previous_suggestions["Location"],
                "Cuisine": previous_suggestions["Cuisine"],
                "Email": previous_suggestions["Email"],
            })
            client = boto3.client('sqs')
            response = client.send_message(
                QueueUrl="https://sqs.us-east-1.amazonaws.com/221082197203/RequirementsQueue",
                MessageBody=message_body)

            return close(
                session_attributes, 
                "Fulfilled", 
                f"Great! We will send the same restaurant recommendations for {previous_suggestions['Cuisine'].lower().capitalize()} "
                f"restaurant(s) in {previous_suggestions['Location']} to {email}.", 
                intent_name
            )
        else:
            location = location.lower().capitalize()

            message_body = json.dumps({
                "Location": location,
                "Cuisine": cuisine,
                "DiningTime": dining_time,
                "NumberOfPeople": number_of_people,
                "Email": email,
                "DiningDate": dining_date
            })
            client = boto3.client('sqs')
            response = client.send_message(
                QueueUrl="https://sqs.us-east-1.amazonaws.com/221082197203/RequirementsQueue",
                MessageBody=message_body)

            dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
            table = dynamodb.Table("state-information")
            try:
                response = table.put_item(Item=json.loads(message_body))
                print(response)
            except Exception as e:
                print(e)

            message = (f"Thank you! We will send you recommendations of {cuisine} restaurant(s) in {location} "
                        f"for {dining_date} at {dining_time}, for {number_of_people} people to {email}")
            
            return close(session_attributes, 'Fulfilled', message, intent_name)

    elif confirmation_state == "Denied":
        if not email and "email" in session_attributes:
            email = session_attributes["email"]
        if "Email" not in slots or slots["Email"] is None:
            slots["Email"] = {"value": {"interpretedValue": email}}
        elif "value" not in slots["Email"]:
            slots["Email"]["value"] = {"interpretedValue": email}
        else:
            slots["Email"]["value"]["interpretedValue"] = email
        return elicit_slot(session_attributes, intent_name, slots, "Location", "What city or city area are you looking to dine in?")

    # Validate the slots using the helper function from utils.py
    validation_result = validate_restaurant_suggestion(location, cuisine, dining_time, number_of_people, email, dining_date)
    if not validation_result['isValid']:
        return elicit_slot(session_attributes, 
                           intent_name, 
                           slots, 
                           validation_result['violatedSlot'], 
                           validation_result['message']['content'])

    if email and not location:
        previous_suggestions = check_previous_suggestions(email)
        if previous_suggestions:
            message = (f"We found your previous restaurant recommendations for {previous_suggestions['Cuisine'].lower().capitalize()} restaurant(s) in {previous_suggestions['Location']}, do you want me to go ahead with these recommendations?")
            session_attributes["email"] = email
            return elicit_confirmation(session_attributes, intent_name, message)

    # If the function is called in DialogCodeHook, delegate control back to Lex
    if intent_request['invocationSource'] == 'DialogCodeHook':
        return delegate(session_attributes, slots, intent_name)

# --- Intent Dispatcher ---
def dispatch(intent_request):
    """Route to the appropriate intent handler."""
    intent_name = intent_request['sessionState']['intent']['name']

    if intent_name == 'GreetingIntent':
        return greet(intent_request)

    if intent_name == 'DiningSuggestionsIntent':
        return suggest_restaurant(intent_request)

    if intent_name == 'ThankYouIntent':
        return thank_you(intent_request)

    raise Exception(f"Intent with name {intent_name} not supported")

# --- Main Lambda Handler ---
def lambda_handler(event, context):
    """Main handler for incoming requests."""
    print(event['invocationSource'])

    return dispatch(event)
