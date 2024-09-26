# import os
# import pyodbc
# import json
# from dotenv import load_dotenv

# def get_metadata_from_sql():
#     # 載入 .env 文件中的環境變數
#     load_dotenv()

#     # 從環境變數中讀取 SQL Server 連接設定
#     server = os.getenv('SQL_SERVER')
#     database = os.getenv('SQL_DATABASE')
#     username = os.getenv('SQL_USER')
#     password = os.getenv('SQL_PASSWORD')
#     driver = '{ODBC Driver 17 for SQL Server}'

#     print(f"Connecting to server: {server}, database: {database}, user: {username}")

#     # 使用 SQL Server 身份驗證建立連接
#     try:
#         connection = pyodbc.connect(
#             f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password};'
#         )
#         print("Connection successful!")
#     except pyodbc.Error as e:
#         print(f"Error connecting to the database: {e}")
#         return None
    
#     try:
#         cursor = connection.cursor()
#         print("Connected to database, executing query...")

#         # 修改查询，选择 id 和 jsonData 列
#         cursor.execute('SELECT id, jsonData FROM JsonData')
#         rows = cursor.fetchall()

#         if not rows:
#             print("Query executed, but no data found.")
#             return None

#         print(f"Number of rows fetched: {len(rows)}")

#         # 解析 jsonData 列，提取 task_id 和 Question
#         metadata = []
#         for row in rows:
#             try:
#                 json_data = json.loads(row[1])  # 解析 jsonData 列

#                 # 如果 json_data 是列表，则遍历它
#                 if isinstance(json_data, list):
#                     for item in json_data:
#                         task_id = item.get('task_id')  # 提取 task_id
#                         question = item.get('Question')  # 提取 Question
#                         metadata.append({'task_id': task_id, 'Question': question})
#                 else:
#                     # 如果 json_data 不是列表，则处理为字典
#                     task_id = json_data.get('task_id')
#                     question = json_data.get('Question')
#                     metadata.append({'task_id': task_id, 'Question': question})

#             except json.JSONDecodeError as e:
#                 print(f"Error decoding JSON for row {row[0]}: {e}")

#         print("Metadata fetched successfully!")
    
#     except pyodbc.Error as e:
#         print(f"Error executing query: {e}")
#         return None

#     finally:
#         cursor.close()
#         connection.close()
#         print("Database connection closed.")

#     return metadata




import os
import pyodbc
from dotenv import load_dotenv

# Connect to SQL Server
def connect_db():
    load_dotenv()
    server = os.getenv('SQL_SERVER')
    database = os.getenv('SQL_DATABASE')
    username = os.getenv('SQL_USER')
    password = os.getenv('SQL_PASSWORD')
    driver = '{ODBC Driver 17 for SQL Server}'

    connection = pyodbc.connect(
        f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password};'
    )
    return connection

def get_metadata_from_sql():
    connection = connect_db()
    cursor = connection.cursor()
    
    cursor.execute('SELECT task_id, Question, Final_answer, Steps FROM Tasks')
    rows = cursor.fetchall()
    
    metadata = []
    for row in rows:
        metadata.append({
            'task_id': row.task_id,
            'Question': row.Question,
            'Final answer': row.Final_answer,
            'Steps': row.Steps
        })
    
    cursor.close()
    connection.close()
    return metadata

def update_metadata_steps(task_id, new_steps):
    connection = connect_db()
    cursor = connection.cursor()
    
    try:
        cursor.execute('UPDATE Tasks SET Steps = ? WHERE task_id = ?', (new_steps, task_id))
        connection.commit()
        success = True
    except Exception as e:
        print(f"Error updating steps: {e}")
        success = False
    
    cursor.close()
    connection.close()
    return success

def insert_evaluation(task_id, is_correct, user_feedback=None):
    """
    将评估记录插入到 Evaluations 表中。

    Parameters:
    - task_id (str): 任务的唯一标识。
    - is_correct (bool): OpenAI 结果是否正确。
    - user_feedback (str, optional): 用户的反馈意见。

    Returns:
    - bool: 如果插入成功，返回 True；否则返回 False。
    """
    connection = connect_db()  # 连接数据库的函数
    cursor = connection.cursor()
    
    try:
        cursor.execute(
            '''
            INSERT INTO Evaluations (task_id, is_correct, user_feedback)
            VALUES (?, ?, ?)
            ''', 
            (task_id, int(is_correct), user_feedback)
        )
        connection.commit()
        success = True
    except Exception as e:
        print(f"Error inserting evaluation: {e}")
        success = False
    
    cursor.close()
    connection.close()
    return success

def get_evaluations():
    """
    Retrieves all evaluation records from the Evaluations table.

    Returns:
    - list of dict: Each dictionary represents an evaluation record.
    """
    connection = connect_db()
    
    if connection is None:
        return []

    cursor = connection.cursor()

    try:
        # Fetch all evaluations from the Evaluations table
        cursor.execute('SELECT evaluation_id, task_id, is_correct, user_feedback, evaluation_timestamp FROM Evaluations')
        rows = cursor.fetchall()

        # Organize the fetched data into a list of dictionaries
        evaluations = []
        for row in rows:
            evaluations.append({
                'evaluation_id': row.evaluation_id,
                'task_id': row.task_id,
                'is_correct': bool(row.is_correct),
                'user_feedback': row.user_feedback,
                'evaluation_timestamp': row.evaluation_timestamp
            })
        
    except Exception as e:
        print(f"Error retrieving evaluations: {e}")
        evaluations = []
    
    finally:
        cursor.close()
        connection.close()

    return evaluations