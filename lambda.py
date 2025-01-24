import os
import boto3
import json

# Grab environment variables
ENDPOINT_NAME = os.environ['ENDPOINT_NAME']
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']
runtime = boto3.client('runtime.sagemaker')
sns = boto3.client('sns')

def lambda_handler(event, context):
    try:
        # Extract payload from event
        payload = json.loads(event['body'])  # Assuming 'body' contains the input data
        payload_data = payload.get('features')  # Adjust according to the structure of the input

        if not payload_data:
            raise ValueError("Missing 'features' in the payload")

        # Convert the payload to CSV format (or ensure it's the correct format for your model)
        payload_csv = ','.join(map(str, payload_data))  # Convert features to CSV

        # Invoke the SageMaker endpoint
        response = runtime.invoke_endpoint(
            EndpointName=ENDPOINT_NAME,
            ContentType='text/csv',  # Ensure model expects this format
            Body=payload_csv
        )

        # Decode and process the SageMaker response
        result = json.loads(response['Body'].read().decode('utf-8'))  # Decode response body
        prediction = {"Prediction of loan status": result}  # Prepare the prediction result

        # Prepare response for API Gateway
        response_dict = {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps(prediction)
        }

        # Publish result to SNS
        sns_message = json.dumps(prediction)
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject='Lambda Function Notification',
            Message=sns_message
        )

        return response_dict

    except Exception as e:
        # Handle errors
        error_message = str(e)
        error_response = {
            "error": error_message
        }

        response_dict = {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps(error_response)
        }

        # Publish error to SNS
        sns_message = json.dumps(error_response)
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject='Lambda Function Error',
            Message=sns_message
        )

        return response_dict
