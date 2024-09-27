# # Import necessary libraries
# import streamlit as st
# from sql_module import get_metadata_from_sql, insert_evaluation, get_evaluations
# from aws_module import get_files_from_s3
# from openai_module import send_to_openai
# import os
# from dotenv import load_dotenv

# # Load environment variables
# load_dotenv()

# # Streamlit App
# st.title("Comparison of OpenAI Answer and Final Answer from Metadata")

# # Initialize session_state variables
# if 'openai_response' not in st.session_state:
#     st.session_state.openai_response = None  # OpenAI Answer
# if 'user_feedback' not in st.session_state:
#     st.session_state.user_feedback = ""  # User Feedback
# if 'is_satisfied' not in st.session_state:
#     st.session_state.is_satisfied = None  # Satisfaction status
# if 'selected_task_id' not in st.session_state:
#     st.session_state.selected_task_id = None  # Current task ID
# if 'feedback_history' not in st.session_state:
#     st.session_state.feedback_history = []  # Feedback history for current question

# # Get the metadata from SQL Server
# metadata = get_metadata_from_sql()
# questions_dict = {record['task_id']: record['Question'] for record in metadata}
# final_answer_dict = {record['task_id']: record['Final answer'] for record in metadata}

# # Display questions in a dropdown
# selected_question = st.selectbox("Select a Question to process", list(questions_dict.values()))

# # Update the selected task_id based on the selected question
# if selected_question:
#     selected_task_id = [task_id for task_id, question in questions_dict.items() if question == selected_question][0]
    
#     # Reset related state variables if a new question is selected
#     if selected_task_id != st.session_state.selected_task_id:
#         st.session_state.selected_task_id = selected_task_id
#         st.session_state.openai_response = None
#         st.session_state.is_satisfied = None
#         st.session_state.user_feedback = ""
#         st.session_state.feedback_history = []  # Reset feedback history

# # Process OpenAI answer logic
# if st.session_state.selected_task_id:
#     question = questions_dict[st.session_state.selected_task_id]

#     # Send the question to OpenAI or display existing OpenAI answer
#     if st.button("Send Question to OpenAI") or st.session_state.openai_response:
#         if st.session_state.openai_response is None:
#             st.session_state.openai_response = send_to_openai(question)
        
#         # Retrieve final answer from metadata
#         final_answer = final_answer_dict.get(st.session_state.selected_task_id, "No final answer available in metadata.")

#         # Display comparison in table format
#         st.subheader("Comparison of OpenAI Answer and Final Answer from Metadata")
#         comparison_data = {
#             "OpenAI Answer": [st.session_state.openai_response],
#             "Metadata Answer": [final_answer]
#         }
#         st.table(comparison_data)

#         # Ask user if they are satisfied with the OpenAI response
#         satisfaction = st.text_input("Is the OpenAI response satisfactory? (Enter 'Yes' or 'No')", key="satisfaction_input")

#         # If the user is not satisfied
#         if satisfaction.lower() == "no":
#             # Show a text area for feedback
#             user_feedback = st.text_area("Provide Feedback or Modify OpenAI Answer", st.session_state.user_feedback, key="feedback_area")
#             if st.button("Submit Feedback"):
#                 # Append user feedback to history
#                 st.session_state.feedback_history.append({
#                     'question': question,
#                     'openai_response': st.session_state.openai_response,
#                     'feedback': user_feedback
#                 })
                
#                 # Generate a new OpenAI answer based on the feedback
#                 st.session_state.openai_response = send_to_openai(user_feedback)

#                 # Display the updated comparison
#                 st.subheader("Updated Comparison of OpenAI Answer and Metadata Answer")
#                 updated_comparison_data = {
#                     "OpenAI Answer": [st.session_state.openai_response],
#                     "Metadata Answer": [final_answer]
#                 }
#                 st.table(updated_comparison_data)
#                 st.info("You can modify the feedback and re-evaluate.")

#         # If the user is satisfied
#         if satisfaction.lower() == "yes":
#             st.session_state.is_satisfied = True
#             insert_evaluation(st.session_state.selected_task_id, True, st.session_state.user_feedback)
#             st.success("You are satisfied. Below is the complete interaction for this question:")

#             # Display the full feedback history in a table
#             feedback_history_data = [{
#                 'Round': idx + 1,
#                 'Question': record['question'],
#                 'OpenAI Response': record['openai_response'],
#                 'User Feedback': record['feedback']
#             } for idx, record in enumerate(st.session_state.feedback_history)]

#             # Show the feedback history table
#             st.table(feedback_history_data)

#             # Fetch evaluations from the database and filter for the current task
#             evaluation_data = get_evaluations()  # Retrieve all evaluations
#             filtered_data = [e for e in evaluation_data if e['task_id'] == st.session_state.selected_task_id]  # Filter by current task ID
#             st.table(filtered_data)















import streamlit as st
from sql_module import get_metadata_from_sql, insert_evaluation, get_evaluations
from openai_module import send_to_openai
from file_processor import process_file_from_s3  # 假设 file_processor.py 中定义了文件处理功能
from upload_data_to_s3 import upload_feedback_to_s3  # 新增：负责上传反馈到S3
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# Streamlit App 标题
st.title("Comparison of OpenAI Answer and Final Answer from Metadata")

# 初始化 session_state 变量
if 'openai_response' not in st.session_state:
    st.session_state.openai_response = None  # OpenAI 答案
if 'user_feedback' not in st.session_state:
    st.session_state.user_feedback = ""  # 用户反馈
if 'is_satisfied' not in st.session_state:
    st.session_state.is_satisfied = None  # 满意状态
if 'selected_task_id' not in st.session_state:
    st.session_state.selected_task_id = None  # 当前选择的任务ID
if 'feedback_history' not in st.session_state:
    st.session_state.feedback_history = []  # 当前问题的反馈历史
if 'file_content' not in st.session_state:
    st.session_state.file_content = ""  # 存储文件内容

# 从数据库获取问题和元数据
metadata = get_metadata_from_sql()
questions_dict = {record['task_id']: record['Question'] for record in metadata}
final_answer_dict = {record['task_id']: record['Final answer'] for record in metadata}
file_name_dict = {record['task_id']: record.get('file_name', '') for record in metadata}  # 获取文件名

# 显示问题下拉框
selected_question = st.selectbox("Select a Question to process", list(questions_dict.values()))

# 当用户选择了问题后，更新 task_id
if selected_question:
    selected_task_id = [task_id for task_id, question in questions_dict.items() if question == selected_question][0]
    
    # 如果选择了新问题，重置相关状态
    if selected_task_id != st.session_state.selected_task_id:
        st.session_state.selected_task_id = selected_task_id
        st.session_state.openai_response = None
        st.session_state.is_satisfied = None
        st.session_state.user_feedback = ""
        st.session_state.file_content = ""
        st.session_state.feedback_history = []  # 重置当前问题的反馈历史

# 如果有附加的文件与问题相关联，从 S3 下载并处理文件
if selected_task_id and file_name_dict[selected_task_id]:
    associated_file = file_name_dict[selected_task_id]
    st.write(f"Processing associated file: {associated_file}")
    
    # 使用文件处理函数处理文件
    file_content = process_file_from_s3(associated_file)
    st.session_state.file_content = file_content  # 将处理后的文件内容存储在 session_state 中
    st.write(f"File Content: {file_content}")

# 处理 OpenAI 回答逻辑
if st.session_state.selected_task_id:
    question = questions_dict[st.session_state.selected_task_id]
    
    # 生成带文件内容的完整问题
    full_prompt = question
    if st.session_state.file_content:
        full_prompt += "\n\nAttached File Content:\n" + st.session_state.file_content  # 合并问题和文件内容

    # 发送问题至 OpenAI 或展示已有的 OpenAI 答案
    if st.button("Send Question to OpenAI") or st.session_state.openai_response:
        if st.session_state.openai_response is None:
            st.session_state.openai_response = send_to_openai(full_prompt)  # 发送完整问题和文件内容
        
        # 获取数据库中的最终答案
        final_answer = final_answer_dict.get(st.session_state.selected_task_id, "No final answer available in metadata.")

        # 以表格形式呈现数据库答案和 OpenAI 答案
        st.subheader("Comparison of OpenAI Answer and Final Answer from Metadata")
        answer_data = {
            "OpenAI Answer": [st.session_state.openai_response],
            "Metadata Answer": [final_answer]
        }
        st.table(answer_data)

        # 用户输入是否满意 (Yes or No)
        satisfaction = st.text_input("Is the OpenAI response satisfactory? (Enter 'Yes' or 'No')", key="satisfaction_input")

        # 处理用户选择 "No" 的情况
        if satisfaction.lower() == "no":
            # 显示用户输入反馈框
            user_feedback = st.text_area("Provide Feedback or Modify OpenAI Answer", st.session_state.user_feedback, key="feedback_area")
            if st.button("Submit Feedback"):
                # 记录用户反馈
                st.session_state.feedback_history.append({
                    'question': question,
                    'openai_response': st.session_state.openai_response,
                    'feedback': user_feedback
                })
                
                # 生成新的 OpenAI 回答
                st.session_state.openai_response = send_to_openai(user_feedback)

                # 重新以表格形式显示新的 OpenAI 答案和数据库答案
                st.subheader("Updated Comparison of OpenAI Answer and Metadata Answer")
                updated_answer_data = {
                    "OpenAI Answer": [st.session_state.openai_response],
                    "Metadata Answer": [final_answer]
                }
                st.table(updated_answer_data)
                st.info("You can modify the feedback and re-evaluate.")

        # 处理用户选择 "Yes" 的情况
        if satisfaction.lower() == "yes":
            st.session_state.is_satisfied = True
            st.session_state.user_feedback = "satisfied"  # 设置用户反馈为 "satisfied"

            # 将当前反馈和满意状态插入数据库
            insert_evaluation(st.session_state.selected_task_id, True, st.session_state.user_feedback)

            # 将反馈上传至S3
            feedback_file_name = f"feedback_task_{st.session_state.selected_task_id}.txt"
            feedback_content = f"Feedback for task {st.session_state.selected_task_id}:\n{st.session_state.user_feedback}"
            upload_feedback_to_s3(feedback_file_name, feedback_content)  # 调用S3上传函数
            
            # 记录反馈历史
            st.session_state.feedback_history.append({
                'question': question,
                'openai_response': st.session_state.openai_response,
                'feedback': "satisfied"
            })

            st.success("You are satisfied. Below is the complete interaction for this question:")

            # 输出完整的交互历史，并以表格形式呈现
            feedback_history_data = [{
                'Round': idx + 1,
                'Question': record['question'],
                'OpenAI Response': record['openai_response'],
                'User Feedback': record['feedback']
            } for idx, record in enumerate(st.session_state.feedback_history)]

            # 仅在 feedback_history_data 非空时渲染表格
            if feedback_history_data:
                st.table(feedback_history_data)
            else:
                st.write("TeamA1 assignment1.")

            # 从数据库中获取评估数据，并只展示当前问题的评估记录
            evaluation_data = get_evaluations()  # 获取所有评估记录
            filtered_data = [e for e in evaluation_data if e['task_id'] == st.session_state.selected_task_id]  # 只显示当前选中任务的记录
            
            # 仅在 filtered_data 非空时渲染表格
            if filtered_data:
                st.table(filtered_data)
            else:
                st.write("TeamA1 assignment1.")






















# import streamlit as st
# from sql_module import get_metadata_from_sql, insert_evaluation, get_evaluations
# from openai_module import send_to_openai

# # 初始化 session_state 变量
# if 'openai_response' not in st.session_state:
#     st.session_state.openai_response = None  # OpenAI 答案
# if 'user_feedback' not in st.session_state:
#     st.session_state.user_feedback = ""  # 用户反馈
# if 'is_satisfied' not in st.session_state:
#     st.session_state.is_satisfied = None  # 满意状态
# if 'selected_task_id' not in st.session_state:
#     st.session_state.selected_task_id = None  # 当前选择的任务ID
# if 'feedback_history' not in st.session_state:
#     st.session_state.feedback_history = []  # 当前问题的反馈历史

# # 从数据库获取问题和元数据
# metadata = get_metadata_from_sql()
# questions_dict = {record['task_id']: record['Question'] for record in metadata}
# final_answer_dict = {record['task_id']: record['Final answer'] for record in metadata}

# # 显示问题下拉框
# selected_question = st.selectbox("Select a Question to process", list(questions_dict.values()))

# # 当用户选择了问题后，更新 task_id
# if selected_question:
#     selected_task_id = [task_id for task_id, question in questions_dict.items() if question == selected_question][0]
    
#     # 如果选择了新问题，重置相关状态
#     if selected_task_id != st.session_state.selected_task_id:
#         st.session_state.selected_task_id = selected_task_id
#         st.session_state.openai_response = None
#         st.session_state.is_satisfied = None
#         st.session_state.user_feedback = ""
#         st.session_state.feedback_history = []  # 重置当前问题的反馈历史

# # 处理 OpenAI 回答逻辑
# if st.session_state.selected_task_id:
#     question = questions_dict[st.session_state.selected_task_id]
    
#     # 发送问题至 OpenAI 或展示已有的 OpenAI 答案
#     if st.button("Send Question to OpenAI") or st.session_state.openai_response:
#         if st.session_state.openai_response is None:
#             st.session_state.openai_response = send_to_openai(question)
        
#         # 获取数据库中的最终答案
#         final_answer = final_answer_dict.get(st.session_state.selected_task_id, "No final answer available in metadata.")

#         # 以表格形式呈现数据库答案和 OpenAI 答案
#         st.subheader("Comparison of OpenAI Answer and Final Answer from Metadata")
#         answer_data = {
#             "OpenAI Answer": [st.session_state.openai_response],
#             "Metadata Answer": [final_answer]
#         }
#         st.table(answer_data)

#         # 用户输入是否满意 (Yes or No)
#         satisfaction = st.text_input("Is the OpenAI response satisfactory? (Enter 'Yes' or 'No')", key="satisfaction_input")

#         # 处理用户选择 "No" 的情况
#         if satisfaction.lower() == "no":
#             # 显示用户输入反馈框
#             user_feedback = st.text_area("Provide Feedback or Modify OpenAI Answer", st.session_state.user_feedback, key="feedback_area")
#             if st.button("Submit Feedback"):
#                 # 记录用户反馈
#                 st.session_state.feedback_history.append({
#                     'question': question,
#                     'openai_response': st.session_state.openai_response,
#                     'feedback': user_feedback
#                 })
                
#                 # 生成新的 OpenAI 回答
#                 st.session_state.openai_response = send_to_openai(user_feedback)

#                 # 重新以表格形式显示新的 OpenAI 答案和数据库答案
#                 st.subheader("Updated Comparison of OpenAI Answer and Metadata Answer")
#                 updated_answer_data = {
#                     "OpenAI Answer": [st.session_state.openai_response],
#                     "Metadata Answer": [final_answer]
#                 }
#                 st.table(updated_answer_data)
#                 st.info("You can modify the feedback and re-evaluate.")

#         # 处理用户选择 "Yes" 的情况
#         if satisfaction.lower() == "yes":
#             st.session_state.is_satisfied = True
#             insert_evaluation(st.session_state.selected_task_id, True, st.session_state.user_feedback)
#             st.success("You are satisfied. Below is the complete interaction for this question:")

#             # 输出完整的交互历史，并以表格形式呈现
#             feedback_history_data = [{
#                 'Round': idx + 1,
#                 'Question': record['question'],
#                 'OpenAI Response': record['openai_response'],
#                 'User Feedback': record['feedback']
#             } for idx, record in enumerate(st.session_state.feedback_history)]

#             # 展示历史反馈表格
#             st.table(feedback_history_data)

#             # 从数据库中获取评估数据，并只展示当前问题的评估记录
#             evaluation_data = get_evaluations()  # 获取所有评估记录
#             filtered_data = [e for e in evaluation_data if e['task_id'] == st.session_state.selected_task_id]  # 只显示当前选中任务的记录
#             st.table(filtered_data)



























# # streamlit_app.py

# # Import necessary libraries
# import streamlit as st
# from sql_module import get_metadata_from_sql, insert_evaluation
# from aws_module import get_files_from_s3
# from openai_module import send_to_openai
# import os
# from dotenv import load_dotenv
# import boto3
# import pandas as pd
# from PIL import Image
# import pytesseract
# import whisper
# from io import BytesIO
# import filetype
# import tempfile
# import json

# # Function to process audio using Whisper
# def process_audio(file_path):
#     try:
#         model = whisper.load_model("base")
#         result = model.transcribe(file_path)
#         return result['text']
#     except Exception as e:
#         return f"Error processing audio: {e}"

# # Load environment variables
# load_dotenv()

# # Streamlit App
# st.title("Task ID Matcher with File Prompt")

# # Get AWS bucket name from .env
# bucket_name = os.getenv('AWS_BUCKET')

# # 1. Fetch metadata task_ids and questions from SQL Server
# metadata = get_metadata_from_sql()
# questions_dict = {record['task_id']: record['Question'] for record in metadata}
# file_name_dict = {record['task_id']: record.get('file_name', '') for record in metadata}
# final_answer_dict = {record['task_id']: record['Final answer'] for record in metadata}

# # Display all questions in a dropdown
# selected_question = st.selectbox("Select a Question to process", list(questions_dict.values()))

# # Get the selected task_id from the question
# selected_task_id = None
# for task_id, question in questions_dict.items():
#     if question == selected_question:
#         selected_task_id = task_id
#         break

# # 2. Check if the selected question has an associated file
# file_content = ""
# if selected_task_id:
#     associated_file = file_name_dict.get(selected_task_id, '')

#     if associated_file:
#         # Fetch the file content from S3
#         st.write(f"Fetching associated file: {associated_file}")
#         s3_files = get_files_from_s3(bucket_name)

#         if associated_file in s3_files:
#             # Download file from S3
#             s3 = boto3.client('s3')
#             file_obj = s3.get_object(Bucket=bucket_name, Key=associated_file)
#             file_type = associated_file.split('.')[-1].lower()
            
#             # Read the file content
#             file_bytes = file_obj['Body'].read()

#             # Use filetype library to detect file type
#             kind = filetype.guess(file_bytes)
            
#             if kind:
#                 file_type = kind.extension
#             else:
#                 st.write("Unsupported or unknown file type.")
            
#             if file_type in ['xlsx', 'csv']:
#                 # Process Excel/CSV file
#                 data = BytesIO(file_bytes)
#                 if file_type == 'xlsx':
#                     df = pd.read_excel(data)
#                 else:
#                     df = pd.read_csv(data)
                
#                 # Extract relevant information from the dataframe
#                 st.dataframe(df.head())
#                 map_representation = df.to_string(index=False)
#                 #st.write(f"Extracted Map Representation:\n{map_representation}")
#                 file_content = map_representation

#             elif file_type in ['mp3', 'wav']:
#                 # Process audio file
#                 with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_type}") as temp_audio:
#                     temp_audio.write(file_bytes)
#                     temp_audio.flush()
#                 # Transcribe audio
#                 file_content = process_audio(temp_audio.name)
#                 st.write(f"Audio Transcript:\n{file_content}")

#             else:
#                 st.write("Unsupported file type for processing.")
        
#         else:
#             st.write(f"File {associated_file} not found in the bucket.")
#     else:
#         file_content = "No file associated with this question."

# # 3. Send question and file content to OpenAI
# if st.button("Send Question to OpenAI"):
#     question = questions_dict[selected_task_id]
    
#     # Creating a structured prompt with extracted information
#     prompt_text = f"Question: {question}"
    
#     if file_content:
#         prompt_text += f"\n\nAdditional Context:\n{file_content}"
    
#     result = send_to_openai(prompt_text)
#     st.write("OpenAI Result:", result)

#     # Display final answer from metadata for feedback comparison
#     final_answer = final_answer_dict.get(selected_task_id, "No final answer available in metadata.")
#     st.write("Final Answer from Metadata:", final_answer)

#     # 4. Provide feedback option
#     feedback = st.radio("Is the OpenAI response satisfactory?", ("Yes", "No"))
#     if st.button("Submit Feedback"):
#         is_correct = True if feedback == "Yes" else False
#         # Insert the evaluation into the database
#         success = insert_evaluation(selected_task_id, is_correct)
#         if success:
#             st.write("Thank you for your feedback!")
#         else:
#             st.write("There was an error submitting your feedback. Please try again.")
# else:
#     st.write("Please select a valid question.")