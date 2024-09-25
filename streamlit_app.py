import streamlit as st
from sql_module import get_metadata_from_sql, update_metadata_steps  # Ensure update_metadata_steps is implemented
from aws_module import get_files_from_s3, download_file_from_s3
from openai_module import send_to_openai
import os
from dotenv import load_dotenv
import tempfile
import PyPDF2
import docx
import pandas as pd
from PIL import Image
import pytesseract

# Load environment variables
load_dotenv()

# Supported file types
SUPPORTED_EXTENSIONS = ['.json', '.pdf', '.png', '.jpeg', '.jpg', '.txt', 
                        '.xlsx', '.csv', '.zip', '.tar.gz', '.mp3', 
                        '.pdb', '.pptx', '.jsonld', '.docx', '.py']

# Function to extract text from different file types
def extract_text_from_file(file_path):
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    try:
        if ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif ext == '.pdf':
            text = ""
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        elif ext == '.docx':
            doc = docx.Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        elif ext in ['.xlsx', '.csv']:
            if ext == '.xlsx':
                df = pd.read_excel(file_path)
            else:
                df = pd.read_csv(file_path)
            return df.to_string()
        elif ext in ['.png', '.jpg', '.jpeg']:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image, lang='chi_tra')  # Using Traditional Chinese language pack
            return text
        else:
            return f"Unsupported file type: {ext}"
    except Exception as e:
        return f"Error processing file: {e}"

# Initialize Streamlit session state
if 'comparison_result' not in st.session_state:
    st.session_state.comparison_result = None
if 'openai_response' not in st.session_state:
    st.session_state.openai_response = ""
if 'final_answer' not in st.session_state:
    st.session_state.final_answer = ""
if 'steps' not in st.session_state:
    st.session_state.steps = ""
if 'selected_task_id' not in st.session_state:
    st.session_state.selected_task_id = ""

# Streamlit App
st.title("Task ID Matcher with OpenAI Evaluation")

# Get AWS bucket name from .env
bucket_name = os.getenv('AWS_BUCKET')

# 1. Get metadata task_ids and questions from SQL Server
metadata = get_metadata_from_sql()
metadata_task_ids = [record['task_id'] for record in metadata]
questions_dict = {record['task_id']: record['Question'] for record in metadata}
final_answers_dict = {record['task_id']: record['Final answer'] for record in metadata}
steps_dict = {record['task_id']: record['Steps'] for record in metadata}
number_of_steps_dict = {record['task_id']: record['Number of steps'] for record in metadata}
how_long_did_this_take_dict = {record['task_id']: record['How long did this take?'] for record in metadata}
tools_dict = {record['task_id']: record['Tools'] for record in metadata}
number_of_tools_dict = {record['task_id']: record['Number of tools'] for record in metadata}

st.write("### Metadata Task IDs:", metadata_task_ids)

# 2. Get files from AWS S3
s3_files = get_files_from_s3(bucket_name)
st.write("### S3 Files:", s3_files)

# 3. Match metadata and S3 Task IDs
def match_task_ids(metadata_task_ids, s3_files):
    task_id_to_files = {}
    for task_id in metadata_task_ids:
        # Assuming file names start with task_id, e.g., "task123_file.pdf"
        matched_files = [file for file in s3_files if file.startswith(task_id)]
        # Filter supported file types
        matched_files = [file for file in matched_files 
                        if any(file.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS)]
        if matched_files:
            task_id_to_files[task_id] = matched_files
    return task_id_to_files

matched_task_ids_dict = match_task_ids(metadata_task_ids, s3_files)
matched_task_ids = list(matched_task_ids_dict.keys())
st.write("### Matched Task IDs:", matched_task_ids)

# 4. Select Task ID to query OpenAI
selected_task_id = st.selectbox("Select a Task ID to Process", matched_task_ids)
st.session_state.selected_task_id = selected_task_id  # Store in session state

# 5. Display associated files
if selected_task_id:
    associated_files = matched_task_ids_dict[selected_task_id]
    st.write(f"### Files Associated with Task ID {selected_task_id}:", associated_files)
else:
    associated_files = []

# 6. Send question and file content to OpenAI
if st.button("Send Question to OpenAI"):
    if selected_task_id and associated_files:
        question = questions_dict[selected_task_id]
        final_answer = final_answers_dict[selected_task_id]
        steps = steps_dict[selected_task_id]
        number_of_steps = number_of_steps_dict[selected_task_id]
        how_long_did_this_take = how_long_did_this_take_dict[selected_task_id]
        tools = tools_dict[selected_task_id]
        number_of_tools = number_of_tools_dict[selected_task_id]
        
        st.session_state.final_answer = final_answer
        st.session_state.steps = steps
        extracted_contents = []
        
        # Create a temporary directory to download files
        with tempfile.TemporaryDirectory() as tmpdir:
            for file_key in associated_files:
                # Download file
                local_path = os.path.join(tmpdir, os.path.basename(file_key))
                download_file_from_s3(bucket_name, file_key, local_path)
                
                # Extract file content
                content = extract_text_from_file(local_path)
                extracted_contents.append(f"File: {file_key}\nContent:\n{content}\n")
        
        # Aggregate all file contents
        aggregated_content = "\n".join(extracted_contents)
        
        # Combine prompt with steps
        prompt = f"{aggregated_content}\nSteps:\n{steps}\nQuestion: {question}"
        
        # Send to OpenAI and get response
        result = send_to_openai(prompt)
        st.session_state.openai_response = result
        
        # Compare OpenAI's answer with the final answer
        if result.strip().lower() == final_answer.strip().lower():
            st.session_state.comparison_result = "correct"
            st.success("OpenAI's answer matches the Final answer.")
        else:
            st.session_state.comparison_result = "incorrect"
            st.error("OpenAI's answer does NOT match the Final answer.")
        
        # Display OpenAI's response
        st.write("### OpenAI's Response:")
        st.write(result)
        
        # Display Final Answer
        st.write("### Final Answer from Metadata:")
        st.write(final_answer)
    else:
        st.write("No Task ID or associated files selected.")

# 7. If the answer is incorrect, provide option to modify Steps
if st.session_state.comparison_result == "incorrect":
    st.write("### Modify Steps")
    new_steps = st.text_area("Edit the Steps below:", value=st.session_state.steps, height=300)
    
    if st.button("Save Modified Steps"):
        if new_steps.strip() == "":
            st.error("Steps cannot be empty.")
        else:
            # Update the steps in the metadata (SQL)
            update_success = update_metadata_steps(selected_task_id, new_steps)
            if update_success:
                st.success("Steps updated successfully.")
                st.session_state.steps = new_steps
                st.session_state.comparison_result = None  # Reset comparison
            else:
                st.error("Failed to update Steps. Please try again.")
    
    # Option to re-evaluate after modifying steps
    if st.session_state.comparison_result != "incorrect":
        if st.button("Re-send Question to OpenAI with Modified Steps"):
            # Re-run the evaluation with updated steps
            question = questions_dict[selected_task_id]
            final_answer = final_answers_dict[selected_task_id]
            steps = st.session_state.steps
            number_of_steps = number_of_steps_dict[selected_task_id]
            how_long_did_this_take = how_long_did_this_take_dict[selected_task_id]
            tools = tools_dict[selected_task_id]
            number_of_tools = number_of_tools_dict[selected_task_id]
            extracted_contents = []
            
            with tempfile.TemporaryDirectory() as tmpdir:
                for file_key in associated_files:
                    local_path = os.path.join(tmpdir, os.path.basename(file_key))
                    download_file_from_s3(bucket_name, file_key, local_path)
                    content = extract_text_from_file(local_path)
                    extracted_contents.append(f"File: {file_key}\nContent:\n{content}\n")
            
            aggregated_content = "\n".join(extracted_contents)
            prompt = f"{aggregated_content}\nSteps:\n{steps}\nQuestion: {question}"
            result = send_to_openai(prompt)
            st.session_state.openai_response = result
            
            if result.strip().lower() == final_answer.strip().lower():
                st.session_state.comparison_result = "correct"
                st.success("OpenAI's answer matches the Final answer.")
            else:
                st.session_state.comparison_result = "incorrect"
                st.error("OpenAI's answer does NOT match the Final answer.")
            
            st.write("### OpenAI's Response:")
            st.write(result)
            
            st.write("### Final Answer from Metadata:")
            st.write(final_answer)

# Optional: Display Annotator Metadata
if selected_task_id:
    st.write("### Annotator Metadata:")
    annotator_metadata = {
        'Steps': steps_dict[selected_task_id],
        'Number of steps': number_of_steps_dict[selected_task_id],
        'How long did this take?': how_long_did_this_take_dict[selected_task_id],
        'Tools': tools_dict[selected_task_id],
        'Number of tools': number_of_tools_dict[selected_task_id]
    }
    st.json(annotator_metadata)
