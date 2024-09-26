# # import openai
# # import os
# # from dotenv import load_dotenv

# # openai.api_key = os.getenv("OPENAI_API_KEY")

# # def send_to_openai(task_data):
# #     prompt=f"Process the following task data: {task_data}"

# #     response = openai.chat.completions.create(
# #         model="gpt-3.5-turbo",
# #         messages=[
# #             {"role": "system", "content": "You are a helpful AI travel assistant. You will give advices about places to visit"},
# #             {"role": "user", "content": prompt}
# #         ],
# #         max_tokens=150
# #     )
# #     advice = response.choices[0].message.content
# #     return advice



# # openai_module.py
# import openai
# import os
# from dotenv import load_dotenv

# # 加載 .env 文件中的環境變數
# load_dotenv()

# def send_to_openai(prompt):
#     openai.api_key = os.getenv("OPENAI_API_KEY")
    
#     try:
#         response = openai.chat.completions.create(
#             model="gpt-4o",  # 修正模型名稱
#             messages=[
#                 {
#                     "role": "system",
#                     "content": "你是一個有幫助的 AI 助手。請根據提供的檔案內容回答問題，並以繁體中文作答。"
#                 },
#                 {
#                     "role": "user",
#                     "content": prompt
#                 }
#             ],
#             max_tokens=1500,  # 根據需要調整
#             temperature=0.7,
#         )
#         advice = response.choices[0].message.content  # 正確訪問訊息內容
#         return advice
#     except Exception as e:
#         return f"與 OpenAI 通信時發生錯誤: {e}"


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