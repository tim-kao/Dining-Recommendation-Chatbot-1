import boto3
from botocore.exceptions import ClientError
import requests
from requests.auth import HTTPBasicAuth
import random

# The AWS Region that you want to use to send the message. For a list of
# AWS Regions where the Amazon Pinpoint API is available, see
# https://docs.aws.amazon.com/pinpoint/latest/apireference/
region = 'us-east-1'

# The Amazon Pinpoint project/application ID to use when you send this message.
# Make sure that the SMS channel is enabled for the project or application
# that you choose.
applicationId = '03cc4948f5e948cd92588ad09a6c624c'

# The type of SMS message that you want to send. If you plan to send
# time-sensitive content, specify TRANSACTIONAL. If you plan to send
# marketing-related content, specify PROMOTIONAL.
messageType = 'TRANSACTIONAL'

# The registered keyword associated with the originating short code.
registeredKeyword = 'myKeyword'

# The sender ID to use when sending the message. Support for sender ID
# varies by country or region. For more information, see
# https://docs.aws.amazon.com/pinpoint/latest/userguide/channels-sms-countries.html
senderId = 'MySenderID'

# elasticsearch path
es_url = 'https://search-restaurants-mzwl7jz5j43kesh6unvvvouizu.us-east-1.es.amazonaws.com/restaurants/_search?q='
username = 'tim'
password = 'Windows2020;'
random_seed = '1688'

# dynamodb info
dynamodb_table_name = 'yelp-restaurants'
dynamodb_region = 'us-east-1'
num_recommendations = 3  # >= 1
sqs_url = 'https://sqs.us-east-1.amazonaws.com/205407915465/SQS.fifo'


def lambda_handler(event, context):
    '''
    Main handler, poll the message from SQS, then tie up message to sns.
    :param event, A evet object trigger by cloud watch event.
    :param context: A context object.
    :return: None.
    '''
    # Poll requests from SQS

    slot = sqs_handlder()
    print(slot)

    """
    slot = {
        'cuisine': {
            'DataType': 'String',
            'StringValue': 'chinese'
        },
        'location': {
            'DataType': 'String',
            'StringValue': 'manhattan'
        },
        'phoneNumber': {
            'DataType': 'String',
            #'StringValue': '+886919525750'
            'StringValue': 'savikx@gmail.com'
        },
        'ppl': {
            'DataType': 'String',
            'StringValue': 4
        },
        'diningDay': {
            'DataType': 'String',
            'StringValue': 'today'
        },
        'time': {
            'DataType': 'String',
            'StringValue': '12:45'
        }}
    """
    # elasticsearch for cuisine.
    if slot is not None:
        query_es = es_url + slot['cuisine']['StringValue']
        response = requests.get(query_es, auth=HTTPBasicAuth(username, password))
        restaurants = response.json()
        text_message = message_helper(restaurants, slot)
        print(text_message)
        # email_handler(text_message, 'sk4920@columbia.edu')
        # print(slot)
        sns_handler(text_message, slot['phoneNumber']['StringValue'])
    else:
        print("No message available in SQS.")


def read_from_dynamodb(key, db=None, table_name=dynamodb_table_name):
    '''
    Fetch data from dynamodb.
    :param key: use key from es to query dynamodb.
    :param db: database resource.
    :param table_name: Assigned table name.
    :return: response from dynamodb.
    '''
    if not db:
        db = boto3.resource('dynamodb', region_name=dynamodb_region)
    table = db.Table(table_name)
    try:
        response = table.get_item(Key=key)
        print('Read data to dynamodb', response)
    except ClientError as e:
        print('Error', e.response['Error']['Message'])
    return response['Item']


def sqs_handlder():
    sqs = boto3.client('sqs')
    response = sqs.receive_message(
        QueueUrl=sqs_url,
        AttributeNames=[
            'SentTimestamp'
        ],
        MaxNumberOfMessages=10,
        MessageAttributeNames=[
            'All'
        ],
        VisibilityTimeout=60,
        WaitTimeSeconds=0
    )
    print(response)
    slot = None
    if 'Messages' in response and response['Messages'][0]['MessageAttributes']:
        slot = response['Messages'][0]['MessageAttributes']
        # print("to be deleted", response['Messages'][0]['ReceiptHandle'] )
        obsolete_message = response['Messages'][0]['ReceiptHandle']
        del_response = sqs.delete_message(
            QueueUrl=sqs_url,
            ReceiptHandle=obsolete_message
        )
    return slot


def sns_handler(message, phone):
    '''
    Send SMS.
    :param message, input message for sns delivery.
    :param phone: destination phone number.
    :return: None.
    '''
    try:
        # Create a new client and specify a region.
        client = boto3.client('pinpoint', region_name=region)
        print('Send message via sns.')
        response = client.send_messages(
            ApplicationId=applicationId,
            MessageRequest={
                'Addresses': {
                    phone: {
                        'ChannelType': 'SMS'
                    }
                },
                'MessageConfiguration': {
                    'SMSMessage': {
                        'Body': message,
                        'Keyword': registeredKeyword,
                        'MessageType': messageType,
                        # 'OriginationNumber': originationNumber,
                        'SenderId': senderId
                    }
                }
            }
        )

    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print('Message sent! Message ID: '
              + response['MessageResponse']['Result'][phone]['MessageId'])


def message_helper(data, slot):
    '''
    wrap up data to sns message.
    :param data: response from elasticsearch, including restaurantid and cuisine.
    :return: A re-organized message ready for sns delivery.
    '''
    items = []
    db = boto3.resource('dynamodb', region_name=dynamodb_region)
    restaurants = []
    # randomization.
    while len(restaurants) < num_recommendations:
        index = random.randint(0, len(data['hits']['hits']) - 1)
        if data['hits']['hits'][index] not in restaurants:
            restaurants.append(data['hits']['hits'][index])

    for restaurant in restaurants:
        key = {}
        key['restaurantID'] = restaurant['_source']['Restaurant']['restaurantID']
        # key = {'restaurantID': 'X8ZS-dgiMIJvhwf9SaDnjw'}
        item = read_from_dynamodb(key, db=db)
        items.append(item)

    message = 'Hello! Here are my ' + \
              slot['cuisine']['StringValue'].capitalize() + ' restaurant suggestions for ' + \
              str(slot['ppl']['StringValue']) + ' people, for ' + slot['diningDay']['StringValue'] + ' ' + slot['time'][
                  'StringValue'] + ': \n'
    for i, item in enumerate(items):
        message += str(i + 1) + '. ' + item['name'] + ', located at '
        if item['location']['display_address']:
            for address_line in item['location']['display_address']:
                message += address_line
        else:
            if item['location']['address1']:
                message += item['location']['address1']
            if item['location']['address2']:
                message += item['location']['address2']
            if item['location']['address3']:
                message += item['location']['address3']
            if item['location']['city']:
                message += item['location']['city']
        if item['rating']:
            message += ', rating: ' + item['rating'] + ' out of 5'
        if item['phone']:
            message += ', phone number: ' + item['phone']
        message += '\n'

    message += 'Enjoy your meal!'

    return message


def email_handler(message, email_addr):
    # Replace sender@example.com with your "From" address.
    # This address must be verified with Amazon SES.
    SENDER = 'sk4920@columbia.edu'

    # If necessary, replace us-west-2 with the AWS Region you're using for Amazon SES.
    AWS_REGION = "us-east-1"

    # The subject line for the email.
    SUBJECT = "TY's Dining Recommendations"

    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = message

    # The HTML body of the email.
    BODY_HTML = message

    # The character encoding for the email.
    CHARSET = "UTF-8"

    # Create a new SES resource and specify a region.
    client = boto3.client('ses', region_name=AWS_REGION)

    # Try to send the email.
    try:
        # Provide the contents of the email.
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    email_addr,
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': BODY_HTML,
                    },
                    'Text': {
                        'Charset': CHARSET,
                        'Data': message,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=SENDER,
            # If you are not using a configuration set, comment or delete the
            # following line
            # ConfigurationSetName=CONFIGURATION_SET,
        )
    # Display an error if something goes wrong.
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])