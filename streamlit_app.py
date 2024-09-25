# streamlit_app.py

# Import necessary libraries
import streamlit as st
from sql_module import get_metadata_from_sql, insert_evaluation
from aws_module import get_files_from_s3
from openai_module import send_to_openai
import os
from dotenv import load_dotenv
import boto3
import pandas as pd
from PIL import Image
import pytesseract
import whisper
from io import BytesIO
import filetype
import tempfile
import json

# Function to process audio using Whisper
def process_audio(file_path):
    try:
        model = whisper.load_model("base")
        result = model.transcribe(file_path)
        return result['text']
    except Exception as e:
        return f"Error processing audio: {e}"

# Load environment variables
load_dotenv()

# Streamlit App
st.title("Task ID Matcher with File Prompt")

# Get AWS bucket name from .env
bucket_name = os.getenv('AWS_BUCKET')

# 1. Fetch metadata task_ids and questions from SQL Server
metadata = get_metadata_from_sql()
questions_dict = {record['task_id']: record['Question'] for record in metadata}
file_name_dict = {record['task_id']: record.get('file_name', '') for record in metadata}
final_answer_dict = {record['task_id']: record['Final answer'] for record in metadata}

# Display all questions in a dropdown
selected_question = st.selectbox("Select a Question to process", list(questions_dict.values()))

# Get the selected task_id from the question
selected_task_id = None
for task_id, question in questions_dict.items():
    if question == selected_question:
        selected_task_id = task_id
        break

# 2. Check if the selected question has an associated file
file_content = ""
if selected_task_id:
    associated_file = file_name_dict.get(selected_task_id, '')

    if associated_file:
        # Fetch the file content from S3
        st.write(f"Fetching associated file: {associated_file}")
        s3_files = get_files_from_s3(bucket_name)

        if associated_file in s3_files:
            # Download file from S3
            s3 = boto3.client('s3')
            file_obj = s3.get_object(Bucket=bucket_name, Key=associated_file)
            file_type = associated_file.split('.')[-1].lower()
            
            # Read the file content
            file_bytes = file_obj['Body'].read()

            # Use filetype library to detect file type
            kind = filetype.guess(file_bytes)
            
            if kind:
                file_type = kind.extension
            else:
                st.write("Unsupported or unknown file type.")
            
            if file_type in ['xlsx', 'csv']:
                # Process Excel/CSV file
                data = BytesIO(file_bytes)
                if file_type == 'xlsx':
                    df = pd.read_excel(data)
                else:
                    df = pd.read_csv(data)
                
                # Extract relevant information from the dataframe
                st.dataframe(df.head())
                map_representation = df.to_string(index=False)
                #st.write(f"Extracted Map Representation:\n{map_representation}")
                file_content = map_representation

            elif file_type in ['mp3', 'wav']:
                # Process audio file
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_type}") as temp_audio:
                    temp_audio.write(file_bytes)
                    temp_audio.flush()
                # Transcribe audio
                file_content = process_audio(temp_audio.name)
                st.write(f"Audio Transcript:\n{file_content}")

            else:
                st.write("Unsupported file type for processing.")
        
        else:
            st.write(f"File {associated_file} not found in the bucket.")
    else:
        file_content = "No file associated with this question."

# 3. Send question and file content to OpenAI
if st.button("Send Question to OpenAI"):
    question = questions_dict[selected_task_id]
    
    # Creating a structured prompt with extracted information
    prompt_text = f"Question: {question}"
    
    if file_content:
        prompt_text += f"\n\nAdditional Context:\n{file_content}"
    
    result = send_to_openai(prompt_text)
    st.write("OpenAI Result:", result)

    # Display final answer from metadata for feedback comparison
    final_answer = final_answer_dict.get(selected_task_id, "No final answer available in metadata.")
    st.write("Final Answer from Metadata:", final_answer)

    # 4. Provide feedback option
    feedback = st.radio("Is the OpenAI response satisfactory?", ("Yes", "No"))
    if st.button("Submit Feedback"):
        is_correct = True if feedback == "Yes" else False
        # Insert the evaluation into the database
        success = insert_evaluation(selected_task_id, is_correct)
        if success:
            st.write("Thank you for your feedback!")
        else:
            st.write("There was an error submitting your feedback. Please try again.")
else:
    st.write("Please select a valid question.")
