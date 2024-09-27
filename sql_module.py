


import os
import pyodbc
from dotenv import load_dotenv

def connect_db():
    load_dotenv()
    server = os.getenv('SQL_SERVER')
    database = os.getenv('SQL_DATABASE')
    username = os.getenv('SQL_USER')
    password = os.getenv('SQL_PASSWORD')
    driver = '{ODBC Driver 17 for SQL Server}'
    
    # 打印调试信息
    print(f"Attempting connection to server: {server}, database: {database}, user: {username}")
    
    try:
        connection = pyodbc.connect(
            f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password};'
        )
        print("Connection successful!")
        return connection
    except pyodbc.Error as e:
        print(f"Connection failed: {e}")
        return None

def get_metadata_from_sql():
    connection = connect_db()
    if connection is None:
        print("Failed to connect to the database.")
        return []
    
    cursor = connection.cursor()
    
    try:
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
        print(f"Fetched {len(metadata)} records from the database.")
        
    except pyodbc.Error as e:
        print(f"Error executing query: {e}")
        metadata = []
    
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


if __name__ == "__main__":
    # 尝试获取任务元数据
    metadata = get_metadata_from_sql()
    
    if metadata:
        print(f"Successfully fetched {len(metadata)} records from the database:")
        for record in metadata:
            print(record)
    else:
        print("No data fetched from the database.")

    # 测试插入评估记录
    success = insert_evaluation(1, True, "Sample feedback")
    if success:
        print("Successfully inserted evaluation into the database.")
    else:
        print("Failed to insert evaluation.")
    
    # 获取所有评估记录
    evaluations = get_evaluations()
    if evaluations:
        print(f"Successfully fetched {len(evaluations)} evaluation records:")
        for evaluation in evaluations:
            print(evaluation)
    else:
        print("No evaluation records found.")