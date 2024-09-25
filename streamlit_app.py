import streamlit as st
from sql_module import (
    get_metadata_from_sql, 
    update_metadata_steps, 
    insert_evaluation, 
    get_evaluations
)
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
import plotly.express as px

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
if 'associated_files' not in st.session_state:
    st.session_state.associated_files = []
if 'evaluation_submitted' not in st.session_state:
    st.session_state.evaluation_submitted = False

# Streamlit App
st.title("Task ID Matcher with OpenAI Evaluation and Feedback")

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
    st.session_state.associated_files = associated_files
    st.write(f"### Files Associated with Task ID {selected_task_id}:", associated_files)
else:
    st.session_state.associated_files = []

# 6. Send question and file content to OpenAI
if st.button("Send Question to OpenAI"):
    if selected_task_id and st.session_state.associated_files:
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
            for file_key in st.session_state.associated_files:
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

# 7. If the answer is incorrect, provide option to modify Steps and capture feedback
if st.session_state.comparison_result == "incorrect":
    st.write("### Modify Steps and Provide Feedback")
    
    # Text area to modify Steps
    new_steps = st.text_area("Edit the Steps below:", value=st.session_state.steps, height=200)
    
    # Text area to provide feedback
    user_feedback = st.text_area("Provide your feedback on the OpenAI response:", height=150)
    
    # Button to save modified Steps and feedback
    if st.button("Save Modified Steps and Submit Feedback"):
        if new_steps.strip() == "":
            st.error("Steps cannot be empty.")
        else:
            # Update the Steps in the metadata (SQL)
            update_success = update_metadata_steps(selected_task_id, new_steps)
            if update_success:
                st.success("Steps updated successfully.")
                st.session_state.steps = new_steps
                # Insert evaluation into Evaluations table
                feedback_success = insert_evaluation(
                    task_id=selected_task_id,
                    is_correct=False,
                    user_feedback=user_feedback.strip() if user_feedback else None
                )
                if feedback_success:
                    st.success("Your feedback has been recorded.")
                else:
                    st.error("Failed to record your feedback. Please try again.")
                # Reset comparison result to allow re-evaluation
                st.session_state.comparison_result = None
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
                for file_key in st.session_state.associated_files:
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
            
            # Display OpenAI's response
            st.write("### OpenAI's Response:")
            st.write(result)
            
            # Display Final Answer
            st.write("### Final Answer from Metadata:")
            st.write(final_answer)

# 8. Generate Reports and Visualizations
st.header("### Evaluation Reports and Visualizations")

# Fetch evaluations data
evaluations = get_evaluations()
if evaluations:
    eval_df = pd.DataFrame(evaluations)
    
    # Display basic metrics
    total_evaluations = len(eval_df)
    correct_answers = eval_df['is_correct'].sum()
    incorrect_answers = total_evaluations - correct_answers
    
    st.subheader("Summary Metrics")
    st.write(f"**Total Evaluations:** {total_evaluations}")
    st.write(f"**Correct Answers:** {correct_answers}")
    st.write(f"**Incorrect Answers:** {incorrect_answers}")
    
    # Pie Chart for Correct vs Incorrect
    fig_pie = px.pie(
        names=['Correct', 'Incorrect'],
        values=[correct_answers, incorrect_answers],
        title='Distribution of OpenAI Responses',
        color=['Correct', 'Incorrect'],
        color_discrete_map={'Correct':'green', 'Incorrect':'red'}
    )
    st.plotly_chart(fig_pie)
    
    # Bar Chart of Evaluations Over Time
    eval_df['evaluation_date'] = pd.to_datetime(eval_df['evaluation_timestamp']).dt.date
    eval_by_date = eval_df.groupby('evaluation_date').size().reset_index(name='count')
    fig_bar = px.bar(
        eval_by_date, 
        x='evaluation_date', 
        y='count',
        title='Number of Evaluations Over Time',
        labels={'evaluation_date': 'Date', 'count': 'Number of Evaluations'},
        template='plotly_white'
    )
    st.plotly_chart(fig_bar)
    
    # Feedback Word Cloud (Optional)
    # Requires installation of wordcloud and additional setup
    try:
        from wordcloud import WordCloud
        import matplotlib.pyplot as plt
        
        feedback_text = ' '.join(eval_df['user_feedback'].dropna().tolist())
        if feedback_text:
            wordcloud = WordCloud(width=800, height=400, background_color='white').generate(feedback_text)
            fig_wc, ax_wc = plt.subplots(figsize=(10, 5))
            ax_wc.imshow(wordcloud, interpolation='bilinear')
            ax_wc.axis('off')
            st.pyplot(fig_wc)
        else:
            st.write("No user feedback available for word cloud.")
    except ImportError:
        st.write("WordCloud module not installed. Install it using `pip install wordcloud` to see feedback word clouds.")
    
    # Table of Evaluations
    st.subheader("Detailed Evaluations")
    st.dataframe(eval_df[['evaluation_id', 'task_id', 'is_correct', 'user_feedback', 'evaluation_timestamp']])
    
else:
    st.write("No evaluations recorded yet.")

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
