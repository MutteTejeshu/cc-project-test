import json
import boto3

lex_client = boto3.client('lexv2-runtime')

def lambda_handler(event, context):
    print(event)
    body = json.loads(event['body'])
    print(body)
    input_text = body['messages'][0]['unstructured']['text']
    print(input_text)

    response = lex_client.recognize_text(
        botId='HZIAVEEIT3',
        botAliasId='TSTALIASID',
        localeId='en_US',
        sessionId="test_session",
        text=input_text
    )

    print(response)

    output_text = response['messages'][0]['content']

    response_body = {
        "messages": [
            {
                "type": "unstructured",
                "unstructured": {
                    "text": output_text
                }
            }
        ]
    }
    print(response_body)

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(response_body)
    }
