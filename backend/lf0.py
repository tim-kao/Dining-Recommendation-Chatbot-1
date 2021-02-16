


import json
import boto3


client = boto3.client('lex-runtime')

def lambda_handler(event, context):
    #event={"message":"hello"}
    print("event:",event)
    print("context",context)
    lastUserMessage = event['message'];
    botMessage = "There is something wrong, Please start process once again.";
    
    if lastUserMessage is None or len(lastUserMessage) < 1:
        return {
            'statusCode': 200,
            'body': json.dumps(botMessage)
        }
    
    # Update the user id, so it is different for different user
    response = client.post_text(
        botName='Dining',
        botAlias='diningchatbot',
        userId='USER1',
        inputText=lastUserMessage)
    
    if response['message'] is not None or len(response['message']) > 0:
        lastUserMessage = response['message']
    
    a = "yo"
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': 'https://s3.us-east-2.amazonaws.com/a1-chatbot.com/',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'messages': str(lastUserMessage)
    }

#'Access-Control-Allow-Origin': 'https://www.example.com',
