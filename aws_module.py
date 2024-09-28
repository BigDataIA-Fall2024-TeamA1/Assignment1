import boto3
import streamlit as st

def get_files_from_s3(bucket_name):
    # 從 secrets.toml 中獲取 AWS 憑證
    aws_access_key_id = st.secrets["aws"]["access_key_id"]
    aws_secret_access_key = st.secrets["aws"]["secret_access_key"]

    # 初始化 S3 客戶端，使用從 secrets 中讀取的憑證
    s3 = boto3.client(
        's3',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key
    )

    # 列出 S3 bucket 中的文件
    response = s3.list_objects_v2(Bucket=bucket_name)
    files = [item['Key'] for item in response.get('Contents', [])]
    return files
