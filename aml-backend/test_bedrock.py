import os
import boto3
from dotenv import load_dotenv
import json

load_dotenv()

client = boto3.client(
    'bedrock',
    region_name=os.getenv('AWS_REGION', 'us-east-1'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

try:
    print("Listing available Anthropic models:")
    response = client.list_foundation_models(byProvider='anthropic')
    models = [m['modelId'] for m in response.get('modelSummaries', []) if m.get('modelLifecycle', {}).get('status') == 'ACTIVE']
    for m in models:
        print(f" - {m}")
        
    print("\nListing inference profiles:")
    try:
        profiles = client.list_inference_profiles()
        for p in profiles.get('inferenceProfileSummaries', []):
            print(f" - {p.get('inferenceProfileId')} ({p.get('inferenceProfileName')})")
    except Exception as e:
        print(f"Could not list inference profiles: {e}")

except Exception as e:
    print(f"Error connecting to Bedrock: {e}")
