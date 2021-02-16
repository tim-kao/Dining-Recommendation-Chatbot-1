"""

This sample demonstrates an implementation of the Lex Code Hook Interface

in order to serve a sample bot which manages orders for flowers.

Bot, Intent, and Slot models which are compatible with this sample can be found in the Lex Console

as part of the 'OrderFlowers' template.



For instructions on how to set up and test this bot, as well as additional samples,

visit the Lex Getting Started documentation http://docs.aws.amazon.com/lex/latest/dg/getting-started.html.

"""

import math

import dateutil.parser

import datetime

import time

import os

import logging

import sys

import boto3

from botocore.exceptions import ClientError

sqs_url = 'https://sqs.us-east-1.amazonaws.com/205407915465/SQS.fifo'

logger = logging.getLogger()

logger.setLevel(logging.DEBUG)

""" --- Helpers to build responses which match the structure of the necessary dialog actions --- """


def get_slots(intent_request):
    return intent_request['currentIntent']['slots']


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {

        'sessionAttributes': session_attributes,

        'dialogAction': {

            'type': 'ElicitSlot',

            'intentName': intent_name,

            'slots': slots,

            'slotToElicit': slot_to_elicit,

            'message': message

        }

    }


def close(session_attributes, fulfillment_state, message):
    response = {

        'sessionAttributes': session_attributes,

        'dialogAction': {

            'type': 'Close',

            'fulfillmentState': fulfillment_state,

            'message': message

        }

    }

    return response


def delegate(session_attributes, slots):
    return {

        'sessionAttributes': session_attributes,

        'dialogAction': {

            'type': 'Delegate',

            'slots': slots

        }

    }


""" --- Helper Functions --- """


def parse_int(n):
    try:

        return int(n)

    except ValueError:

        return float('nan')


def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {

            "isValid": is_valid,

            "violatedSlot": violated_slot,

        }

    return {

        'isValid': is_valid,

        'violatedSlot': violated_slot,

        'message': {'contentType': 'PlainText', 'content': message_content}

    }


def isvalid_location(location):
    try:

        return location.isalpha()

    except ValueError:

        return False


def isvalid_date(date):
    try:

        dateutil.parser.parse(date)

        return True

    except ValueError:

        return False


def validate_suggest_restaurant(slot):
    diningDay = slot["diningDay"]

    location = slot["location"]

    phoneNumber = slot["phoneNumber"]

    email = slot["email"]

    time = slot["time"]

    cuisine = slot["cuisine"]

    ppl = slot["ppl"]

    cities = ['new york', 'manhattan', 'ny']

    if location is not None:

        if not isvalid_location(location) and location.lower() not in cities:
            return build_validation_result(False, 'location',

                                           'I did not understand that, what city would you like to check?')
        else:
            if location.lower() not in cities:
                return build_validation_result(False,

                                               'location',

                                               'We do not have data at {}, would you like a location?'

                                               'Our most popular cuisine are new york and manhattan'.format(location))

    # Check cuisines

    cuisines = ['caribbean', 'japanese', 'italian', 'chinese', 'american', 'mexico', 'korean']

    if cuisine is not None:  # and cuisine.lower() not in cuisines:

        if cuisine.lower() not in cuisines:
            return build_validation_result(False,

                                           'cuisine',

                                           'We do not have {}, would you like a different type of cuisines?'

                                           'Our most popular cuisine are caribbean, japanese, italian, chinese, american, mexico, and korean'.format(
                                               cuisine))

    if diningDay is not None:

        if not isvalid_date(diningDay):

            return build_validation_result(False, 'diningDay',

                                           'I did not understand that, what day would you like to check?')

        elif datetime.datetime.strptime(diningDay, '%Y-%m-%d').date() < datetime.date.today():

            return build_validation_result(False, 'diningDay',

                                           'What time?')

    # if phoneNumber is not None:

    #     if math.isnan(parse_int(phoneNumber)):

    #         return build_validation_result(False,

    #                                        'phoneNumber',

    #                                        'Your number {} is invalid, would you like a different number?'.format(PhoneNumber))

    if phoneNumber is not None:

        if not phoneNumber.isdigit() or len(phoneNumber) < 9 or len(phoneNumber) > 13:
            print(phoneNumber, type(phoneNumber))
            return build_validation_result(False, 'phoneNumber',

                                           'The phone number entered is not a valid phone number '.format(
                                               phoneNumber))

    if email is not None:

        if not isinstance(email, str) or '@' not in email or len(email) < 3:
            return build_validation_result(False,
                                           'email',
                                           'Your email {} is invalid, would you like a different email?'.format(
                                               email))

    if time is not None:

        if len(time) != 5:
            # Not a valid time; use a prompt defined on the build-time model.

            return build_validation_result(False, 'time', None)

        hour, minute = time.split(':')

        hour = parse_int(hour)

        minute = parse_int(minute)

        if math.isnan(hour) or math.isnan(minute):
            # Not a valid time; use a prompt defined on the build-time model.

            return build_validation_result(False, 'time', None)

        if hour < 7 or hour > 22:
            # Outside of business hours

            return build_validation_result(False, 'time',
                                           'Our business hours are from seven a m. to ten p m. Can you specify a time during this range?')

    if ppl is not None:

        if not ppl.isdigit() or parse_int(ppl) > 30 or parse_int(ppl) < 1:
            return build_validation_result(False,

                                           'ppl',

                                           'Your number {} is invalid, would you like a different number of people?'.format(
                                               ppl))

    return build_validation_result(True, None, None)


def validate_order_flowers(flower_type, date, pickup_time):
    flower_types = ['lilies', 'roses', 'tulips']

    if flower_type is not None and flower_type.lower() not in flower_types:
        return build_validation_result(False,

                                       'FlowerType',

                                       'We do not have {}, would you like a different type of flower?  '

                                       'Our most popular flowers are roses'.format(flower_type))

    if date is not None:

        if not isvalid_date(date):

            return build_validation_result(False, 'PickupDate',
                                           'I did not understand that, what date would you like to pick the flowers up?')

        elif datetime.datetime.strptime(date, '%Y-%m-%d').date() <= datetime.date.today():

            return build_validation_result(False, 'PickupDate',
                                           'You can pick up the flowers from tomorrow onwards.  What day would you like to pick them up?')

    if pickup_time is not None:

        if len(pickup_time) != 5:
            # Not a valid time; use a prompt defined on the build-time model.

            return build_validation_result(False, 'PickupTime', None)

        hour, minute = pickup_time.split(':')

        hour = parse_int(hour)

        minute = parse_int(minute)

        if math.isnan(hour) or math.isnan(minute):
            # Not a valid time; use a prompt defined on the build-time model.

            return build_validation_result(False, 'PickupTime', None)

        # if hour < 10 or hour > 16:
        # Outside of business hours

        #   return build_validation_result(False, 'PickupTime',
        #                                   'Our business hours are from ten a m. to five p m. Can you specify a time during this range?')

    return build_validation_result(True, None, None)


""" --- Functions that control the bot's behavior --- """


def suggest_restaurant(intent_request):
    """

    Performs dialog management and fulfillment for restaurant recommendation

    """
    source = intent_request['invocationSource']

    slot = get_slots(intent_request)

    if source == 'DialogCodeHook':

        # Perform basic validation on the supplied input slots.

        # Use the elicitSlot dialog action to re-prompt for the first violation detected.

        slots = get_slots(intent_request)

        validation_result = validate_suggest_restaurant(slot)
        print('Validation results', validation_result)
        # validation_result = build_validation_result(True, None, None)

        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None

            return elicit_slot(intent_request['sessionAttributes'],

                               intent_request['currentIntent']['name'],

                               slots,

                               validation_result['violatedSlot'],

                               validation_result['message'])

        output_session_attributes = intent_request['sessionAttributes'] if intent_request[
                                                                               'sessionAttributes'] is not None else {}

        return delegate(output_session_attributes, get_slots(intent_request))

        # Send Message to SQS Here
    print(slot)

    sqs_response = message_sender(slot)

    if sqs_response:
        print("Send slot to SQS successfully.")
    else:
        print("Fail to send slot to SQS.")

    return close(intent_request['sessionAttributes'],

                 'Fulfilled',

                 {'contentType': 'PlainText',

                  'content': 'You`re all set. Expect my suggestions shortly! Have a good day.'})


def message_sender(slot):
    '''
    Send slot data to SQS.
    :param slot: Get slot from Lex.
    :return: Commit successful or failed.
    '''
    try:

        sqs_client = boto3.client('sqs')
        logger.setLevel(logging.DEBUG)
        logger.debug('Sent message to SQS!')
        response = sqs_client.send_message(
            QueueUrl=sqs_url,
            MessageBody='Test send message',
            # mark for fifo queue, DelaySeconds=0,
            MessageAttributes={
                'cuisine': {
                    'DataType': 'String',
                    'StringValue': slot['cuisine']
                },
                'location': {
                    'DataType': 'String',
                    'StringValue': slot['location']
                },
                'phoneNumber': {
                    'DataType': 'String',
                    'StringValue': slot['phoneNumber']
                },
                'email': {
                    'DataType': 'String',
                    'StringValue': slot['email']
                },
                'ppl': {
                    'DataType': 'String',
                    'StringValue': slot['ppl']
                },
                'diningDay': {
                    'DataType': 'String',
                    'StringValue': slot['diningDay']
                },
                'time': {
                    'DataType': 'String',
                    'StringValue': slot['time']
                }},
            MessageDeduplicationId='TYchatbotspring2021_165489',
            MessageGroupId='1233214566547899817')
        return True
    except ClientError as e:
        return False


def order_flowers(intent_request):
    """

    Performs dialog management and fulfillment for ordering flowers.

    Beyond fulfillment, the implementation of this intent demonstrates the use of the elicitSlot dialog action

    in slot validation and re-prompting.

    """

    flower_type = get_slots(intent_request)["FlowerType"]

    date = get_slots(intent_request)["PickupDate"]

    pickup_time = get_slots(intent_request)["PickupTime"]

    source = intent_request['invocationSource']

    if source == 'DialogCodeHook':

        # Perform basic validation on the supplied input slots.

        # Use the elicitSlot dialog action to re-prompt for the first violation detected.

        slots = get_slots(intent_request)

        validation_result = validate_order_flowers(flower_type, date, pickup_time)

        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None

            return elicit_slot(intent_request['sessionAttributes'],

                               intent_request['currentIntent']['name'],

                               slots,

                               validation_result['violatedSlot'],

                               validation_result['message'])

        # Pass the price of the flowers back through session attributes to be used in various prompts defined

        # on the bot model.

        output_session_attributes = intent_request['sessionAttributes'] if intent_request[
                                                                               'sessionAttributes'] is not None else {}

        if flower_type is not None:
            output_session_attributes['Price'] = len(flower_type) * 5  # Elegant pricing model

        return delegate(output_session_attributes, get_slots(intent_request))

    # Order the flowers, and rely on the goodbye message of the bot to define the message to the end user.

    # In a real bot, this would likely involve a call to a backend service.

    return close(intent_request['sessionAttributes'],

                 'Fulfilled',

                 {'contentType': 'PlainText',

                  'content': 'Thanks, your order for {} has been placed and will be ready for pickup by {} on {}'.format(
                      flower_type, pickup_time, date)})


""" --- Intents --- """


def dispatch(intent_request):
    """

    Called when the user specifies an intent for this bot.

    """

    logger.debug(
        'dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers

    # if intent_name == 'GreetingIntent':

    #    return

    if intent_name == 'GreetingIntent':

        return close(intent_request['sessionAttributes'], 'Fulfilled',

                     {'contentType': 'PlainText', 'content': 'Hi there, how can I help?'})

    elif intent_name == 'DiningSuggestionsIntent':

        return suggest_restaurant(intent_request)

    elif intent_name == 'ThankYouIntent':

        return close(intent_request['sessionAttributes'], 'Fulfilled',

                     {'contentType': 'PlainText', 'content': 'You`re welcome.'})

    elif intent_name == 'OrderFlowers':

        return order_flowers(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')


""" --- Main handler --- """


def lambda_handler(event, context):
    """

    Route the incoming request based on intent.

    The JSON body of the request is provided in the event slot.

    """

    # By default, treat the user request as coming from the America/New_York time zone.

    os.environ['TZ'] = 'America/New_York'

    time.tzset()

    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)

