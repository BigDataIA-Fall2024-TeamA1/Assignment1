import openai
import os
from dotenv import load_dotenv

openai.api_key = os.getenv("OPENAI_API_KEY")

def send_to_openai(task_data):
    prompt=f"Process the following task data: {task_data}"

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful AI travel assistant. You will give advices about places to visit"},
            {"role": "user", "content": prompt}
        ],
        max_tokens=150
    )
    advice = response.choices[0].message.content
    return advice
