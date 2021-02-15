# Dining-Recommendation-Chatbot

### Overview
##### Customer Service is a core service for a lot of businesses around the world and it is getting disrupted at the moment by Natural Language Processing-powered applications. The dining Concierge chatbot is a serverless, microservice-driven web application that sends customers restaurant suggestions given a set of preferences that they provide the chatbot with through conversation. 

### Application
##### 1) Frontend: CSS, HTML, JavaScript
##### 2) Backend: AWS Serverless (S3, Lambda, API Gateway, LEX, SQS, SNS, DynamoDB, ElasticSearch), Swagger API, PyThon

### Architecture

### Description
#### 1) [S3](https://s3.console.aws.amazon.com/s3/)
#####    - Store the frontend files.
#####    - Generate SDK from AWS API Gateway and store it into js folder.
#####    - chat.js file needs modification.
#####    - Create CORS policy.
#### 2) [API Gateway](https://s3.console.aws.amazon.com/apigateway/)
#####    - Create a new API by importing swagger API.
#####    - Set POST method abd integrate Lambda function LF0 with it.
#####    - Set OPTIONS method with HTTP status 200.
#####    - Enable CORS.
#####    - Deploy API.
#####    - Generate SDK for frontend.
#### 3) [Lambda](https://s3.console.aws.amazon.com/lambda/) - LF0
#####    - Receive messages from the frontend user.
#####    - Direct messages to Dining Chatbot in Lex.
#### 4) [Lex](https://s3.console.aws.amazon.com/lex/)
#####    - Create a Dining Chatbot with three intents (GreetingIntent, DiningSuggestionsIntent, ThankYouIntent).
#####    - Set up user utterances and slots for interaction conversation. 
#####    - Integrate with Lambda function LF1.
#####    - Publish the chatbot.
#### 5) [Lambda](https://s3.console.aws.amazon.com/lambda/) - LF1
#####    - Trigger to fulfill the recommendation by sending it to SQS for later processing after the conversation.
