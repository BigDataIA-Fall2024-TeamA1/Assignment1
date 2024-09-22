import streamlit as st
from sql_module import get_metadata_from_sql
from aws_module import get_files_from_s3
from openai_module import send_to_openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Streamlit App
st.title("Task ID Matcher")

# Get AWS bucket name from .env
bucket_name = os.getenv('AWS_BUCKET')

# 1. Fetch metadata task_ids and questions from SQL Server
metadata = get_metadata_from_sql()
metadata_task_ids = [record['task_id'] for record in metadata]
questions_dict = {record['task_id']: record['Question'] for record in metadata}
st.write("Metadata Task IDs:", metadata_task_ids)

# 2. Fetch files from AWS S3
s3_files = get_files_from_s3(bucket_name)
st.write("S3 Files:", s3_files)

# 3. Match Task ID between metadata and S3
def match_task_ids(metadata_task_ids, s3_files):
    matched_ids = [task_id for task_id in metadata_task_ids if task_id in s3_files]
    return matched_ids

matched_task_ids = match_task_ids(metadata_task_ids, s3_files)
st.write("Matched Task IDs:", matched_task_ids)

# 4. Select Task ID to query OpenAI
selected_task_id = st.selectbox("Select a Task ID to process", matched_task_ids)

# 5. Send question to OpenAI
if st.button("Send Question to OpenAI"):
    if selected_task_id:
        question = questions_dict[selected_task_id]
        result = send_to_openai(question)
        st.write("OpenAI Result:", result)
    else:
        st.write("No Task ID selected or matched.")
