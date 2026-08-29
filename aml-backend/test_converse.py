import os
import boto3
from dotenv import load_dotenv

load_dotenv()

from langchain_aws import ChatBedrockConverse

models_to_test = [
    "us.amazon.nova-lite-v1:0",
    "us.amazon.nova-micro-v1:0",
    "us.meta.llama3-2-11b-instruct-v1:0",
    "us.mistral.pixtral-large-2502-v1:0"
]

for model_id in models_to_test:
    print(f"\nTesting model: {model_id}")
    try:
        llm = ChatBedrockConverse(
            model=model_id,
            region_name=os.getenv("AWS_REGION", "us-east-1"),
        )
        response = llm.invoke("Say hi.")
        print("Success! Response:")
        print(response.content)
    except Exception as e:
        print(f"Failed: {e}")
