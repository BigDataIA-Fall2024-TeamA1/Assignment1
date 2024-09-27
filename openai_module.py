
from openai import OpenAI
import os
from dotenv import load_dotenv

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load environment variables
load_dotenv()

def send_to_openai(question, user_feedback=None):
    # 准备问题提示
    prompt = f"Question: {question}\n\n"
    
    if user_feedback:
        prompt += f"User Feedback:\n{user_feedback}\n\n"
    else:
        prompt += "No user feedback provided."
    
    # 调用 OpenAI API
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # 使用 gpt-3.5-turbo 或 gpt-4
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=300  # 调整 max_tokens 以适应更长的回答
    )

    # 提取 OpenAI 模型生成的答案
    advice = response.choices[0].message.content
    return advice