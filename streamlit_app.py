import streamlit as st
from sql_module import get_metadata_from_sql
from aws_module import get_files_from_s3, download_file_from_s3  # 確保匯入 download_file_from_s3
from openai_module import send_to_openai
import os
from dotenv import load_dotenv
import tempfile
import PyPDF2
import docx
import pandas as pd
from PIL import Image
import pytesseract

# 加載環境變數
load_dotenv()

# 設定支持的檔案類型
SUPPORTED_EXTENSIONS = ['.json', '.pdf', '.png', '.jpeg', '.jpg', '.txt', 
                        '.xlsx', '.csv', '.zip', '.tar.gz', '.mp3', 
                        '.pdb', '.pptx', '.jsonld', '.docx', '.py']

# 定義提取不同檔案類型內容的函數
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
            text = pytesseract.image_to_string(image, lang='chi_tra')  # 使用繁體中文語言包
            return text
        else:
            return f"不支援的檔案類型: {ext}"
    except Exception as e:
        return f"處理檔案時出錯: {e}"

# Streamlit App
st.title("Task ID 匹配器")

# 從 .env 獲取 AWS bucket 名稱
bucket_name = os.getenv('AWS_BUCKET')

# 1. 從 SQL Server 獲取 metadata task_ids 和問題
metadata = get_metadata_from_sql()
metadata_task_ids = [record['task_id'] for record in metadata]
questions_dict = {record['task_id']: record['Question'] for record in metadata}
st.write("Metadata Task IDs:", metadata_task_ids)

# 2. 從 AWS S3 獲取檔案
s3_files = get_files_from_s3(bucket_name)
st.write("S3 檔案:", s3_files)

# 3. 匹配 metadata 和 S3 中的 Task ID
def match_task_ids(metadata_task_ids, s3_files):
    task_id_to_files = {}
    for task_id in metadata_task_ids:
        # 假設檔案名稱以 task_id 開頭，例如 "task123_file.pdf"
        matched_files = [file for file in s3_files if file.startswith(task_id)]
        # 過濾支持的檔案類型
        matched_files = [file for file in matched_files 
                        if any(file.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS)]
        if matched_files:
            task_id_to_files[task_id] = matched_files
    return task_id_to_files

matched_task_ids_dict = match_task_ids(metadata_task_ids, s3_files)
matched_task_ids = list(matched_task_ids_dict.keys())
st.write("匹配的 Task IDs:", matched_task_ids)

# 4. 選擇要查詢 OpenAI 的 Task ID
selected_task_id = st.selectbox("選擇一個 Task ID 來處理", matched_task_ids)

# 5. 顯示與選擇的 Task ID 相關的檔案
if selected_task_id:
    associated_files = matched_task_ids_dict[selected_task_id]
    st.write(f"與 Task ID {selected_task_id} 相關的檔案:", associated_files)
else:
    associated_files = []

# 6. 發送問題和檔案內容給 OpenAI
if st.button("將問題發送給 OpenAI"):
    if selected_task_id and associated_files:
        question = questions_dict[selected_task_id]
        extracted_contents = []
        
        # 創建臨時目錄下載檔案
        with tempfile.TemporaryDirectory() as tmpdir:
            for file_key in associated_files:
                # 下載檔案
                local_path = os.path.join(tmpdir, os.path.basename(file_key))
                download_file_from_s3(bucket_name, file_key, local_path)  # 修改此行
                
                # 提取檔案內容
                content = extract_text_from_file(local_path)
                extracted_contents.append(f"檔案: {file_key}\n內容:\n{content}\n")
        
        # 聚合所有檔案內容
        aggregated_content = "\n".join(extracted_contents)
        
        # 組合要發送給 OpenAI 的訊息
        prompt = f"{aggregated_content}\n問題: {question}"
        
        # 發送給 OpenAI 並獲取回應
        result = send_to_openai(prompt)
        st.write("OpenAI 回應:", result)
    else:
        st.write("未選擇 Task ID 或相關檔案。")
