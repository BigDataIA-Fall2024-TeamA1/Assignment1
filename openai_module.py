from openai import OpenAI
import os
from dotenv import load_dotenv

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# Load environment variables
load_dotenv()

# Set the OpenAI API key

def send_to_openai(question, file_content=None):
    # Prepare the prompt
    prompt = f"Question: {question}\n\n"
    
    if file_content:
        # If the file content is too long, summarize or trim it
        if len(file_content) > 1000:
            file_content = file_content[:1000] + "\n\n... (content truncated)"
        # Format the file content clearly
        prompt += f"Attached File Content:\n{file_content}"
    else:
        prompt += "No file content provided."
    
    # Call OpenAI API with the prompt using the updated API format
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # Use gpt-3.5-turbo or gpt-4 if you have access
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=300  # Increase the max_tokens to allow a longer response
    )

    # Extract the assistant's message content from the response
    advice = response.choices[0].message.content
    return advice
