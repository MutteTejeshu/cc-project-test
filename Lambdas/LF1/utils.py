# --- Helper Functions for Lex Responses ---
import datetime
import re
import json
import boto3

def elicit_confirmation(session_attributes, intent_name, message):
    """Ask the user for confirmation before proceeding."""
    return {
        "sessionState": {
            "sessionAttributes": session_attributes,
            "dialogAction": {
                "type": "ConfirmIntent"
            },
            "intent": {
                "name": intent_name
            }
        },
        "messages": [
            {
                "contentType": "PlainText",
                "content": message
            }
        ]
    }

def greet(intent_request):
    session_attributes = intent_request['sessionState']['sessionAttributes'] if intent_request['sessionState'].get('sessionAttributes') else {}
    intent_name = intent_request['sessionState']['intent']['name']

    return {
            "sessionState": {
                "sessionAttributes": session_attributes,
                "dialogAction": {
                    "type": "ElicitIntent"
                },
                "intent": {
                    "name": intent_name
                }
            },
            "messages": [
                {
                    "contentType": "PlainText",
                    "content": "Hi there, how can I help?"
                }
            ]
        }

def thank_you(intent_request):
    session_attributes = intent_request['sessionState']['sessionAttributes'] if intent_request['sessionState'].get('sessionAttributes') else {}
    intent_name = intent_request['sessionState']['intent']['name']

    return {
            "sessionState": {
                "sessionAttributes": session_attributes,
                "dialogAction": {
                    "type": "Close"
                },
                "intent": {
                    "name": intent_name,
                    "state": "Fulfilled"
                }
            },
            "messages": [
                {
                    "contentType": "PlainText",
                    "content": "Thank you, we will be sending your restaurant recommendations over to your email in some time."
                }
            ]
        }

def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionState': {
            'sessionAttributes': session_attributes,
            'dialogAction': {
                'type': 'ElicitSlot',
                'slotToElicit': slot_to_elicit
            },
            'intent': {
                'name': intent_name,
                'slots': slots
            }
        },
        'messages': [
            {
                'contentType': 'PlainText',
                'content': message
            }
        ]
    }

def delegate(session_attributes, slots, intent_name):
    """Delegate control back to Lex for slot collection."""
    return {
        'sessionState': {
            'sessionAttributes': session_attributes,
            'intent': {
                'name': intent_name,
                'slots': slots
            },
            'dialogAction': {
                'type': 'Delegate'
            }
        }
    }

def close(session_attributes, fulfillment_state, message, intent_name):
    """Close the conversation with a completion message."""
    return {
        "sessionState" : {
            "sessionAttributes": session_attributes,
            "dialogAction": {
                "type": "Close"
            },
            "intent": {
                "name": intent_name,
                "state": fulfillment_state
            }
        },
        "messages": [
            {
                "contentType": "PlainText",
                "content": message
            }
        ]
    }

def build_validation_result(is_valid, violated_slot, message_content):
    """Build the result structure for validation."""
    if not is_valid:
        return {
            'isValid': False,
            'violatedSlot': violated_slot,
            'message': {'contentType': 'PlainText', 'content': message_content}
        }
    return {'isValid': True}

# --- Slot Validation Functions ---
def is_valid_location(location):
    """Check if the location is valid for this bot."""
    valid_locations = ['manhattan']
    return location.lower() in valid_locations

def is_valid_cuisine(cuisine):
    """Check if the cuisine is valid for this bot."""
    valid_cuisines = ['chinese', 'italian', 'japanese']
    return cuisine.lower() in valid_cuisines

def is_valid_dining_time(dining_time):
    """Check if the dining time is a valid time."""
    try:
        dining_time = datetime.datetime.strptime(dining_time, '%H:%M').time()

        opening_time = datetime.time(10, 0)
        closing_time = datetime.time(22, 0)

        if not (opening_time <= dining_time <= closing_time):
            return False, f"Please choose a valid time, the operating hours of the restaurants are from {opening_time.strftime('%H:%M')} to {closing_time.strftime('%H:%M')}"
        return True, None
    except ValueError:
        return False, "The time format is invalid. Please use HH:MM format."

def is_valid_number_of_people(number_of_people):
    """Check if the number of people is a positive integer and not too large."""
    try:
        number_of_people = int(number_of_people)
        if number_of_people <= 0:
            return False, "The number of people should be a positive integer. Please provide a valid number."
        if number_of_people > 16:
            return False, "We do not allow bookings for more than 16 people. Please enter a smaller number."
        return True, None
    except ValueError:
        return False, "The number of people should be a valid integer."

def is_valid_email(email):
    """Check if the email is valid."""
    email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    ses_client = boto3.client('ses')
    response = ses_client.list_identities(
        IdentityType='EmailAddress',
        NextToken='',
        MaxItems=100
    )
    if not re.match(email_pattern, email):
        return False, "The email format is invalid. Please enter a valid email address (e.g., user@example.com)."
    if email not in response['Identities']:
        return False, "The email address is not verified. Please use a verified email address or verify your email address and try again."
    return True, None

def is_valid_date(dining_date):
    """Check if the date is a valid future date and not too far in the future."""
    try:
        dining_in_date = datetime.datetime.strptime(dining_date, '%Y-%m-%d').date()
        print(datetime.date.today())
        if dining_in_date < datetime.date.today():
            return False, "The check-in date cannot be in the past. Can you provide a future date?"
        if dining_in_date > datetime.date.today() + datetime.timedelta(days=365):
            return False, "You cannot book more than a year in advance. Please choose a closer date."
        return True, None
    except ValueError:
        return False, "The date format is invalid. Please use YYYY-MM-DD format."

# --- Main Validation Function ---
def validate_restaurant_suggestion(location, cuisine, dining_time, number_of_people, email, dining_date):
    """Perform validation for all slots with advanced checks."""
    if location and not is_valid_location(location):
        return build_validation_result(False, 'Location', f"We do not support {location} yet. Please choose from: Manhattan")
    
    if cuisine and not is_valid_cuisine(cuisine):
        return build_validation_result(False, 'Cuisine', f"We do not support {cuisine} cuisine yet. Please choose from: Chinese, Italian, Japanese.")
    
    if dining_time:
        dining_time_valid, dining_time_message = is_valid_dining_time(dining_time)
        if not dining_time_valid:
            return build_validation_result(False, 'DiningTime', dining_time_message)

    if number_of_people:
        number_of_people_valid, number_of_people_message = is_valid_number_of_people(number_of_people)
        if not number_of_people_valid:
            return build_validation_result(False, 'NumberOfPeople', number_of_people_message)

    if email:
        email_valid, email_message = is_valid_email(email)
        if not email_valid:
            return build_validation_result(False, 'Email', email_message)
    
    if dining_date:
        date_valid, date_message = is_valid_date(dining_date)
        if not date_valid:
            return build_validation_result(False, 'DiningDate', date_message)

    return {'isValid': True, 'violatedSlot': None, 'message': None}