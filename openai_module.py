import openai
import streamlit as st

# Access the OpenAI API key from Streamlit secrets
openai_api_key = st.secrets["openai"]["api_key"]

# Initialize the OpenAI client with the API key from secrets
client = openai.OpenAI(api_key=openai_api_key)

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
        model="gpt-4o",  
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=300  # Increase the max_tokens to allow a longer response
    )

    # Extract the assistant's message content from the response
    advice = response.choices[0].message.content
    return advice
