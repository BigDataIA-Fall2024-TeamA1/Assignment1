import os
import pyodbc
from dotenv import load_dotenv

def get_metadata_from_sql():
    # 載入 .env 文件中的環境變數
    load_dotenv()

    # 從環境變數中讀取 SQL Server 連接設定
    server = os.getenv('SQL_SERVER')  # 伺服器名稱
    database = os.getenv('SQL_DATABASE')  # 資料庫名稱
    username = os.getenv('SQL_USER')  # SQL 使用者名稱
    password = os.getenv('SQL_PASSWORD')  # SQL 使用者密碼
    driver = '{ODBC Driver 17 for SQL Server}'  # SQL Server ODBC 驅動

    # 使用 SQL Server 身份驗證建立連接
    connection = pyodbc.connect(
        f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password};'
    )
    
    cursor = connection.cursor()
    
    # 執行查詢
    cursor.execute('SELECT task_id, Question FROM Tasks')
    rows = cursor.fetchall()
    
    # 整理查詢結果
    metadata = [{'task_id': row[0], 'Question': row[1]} for row in rows]

    # 關閉連接
    cursor.close()
    connection.close()

    return metadata
