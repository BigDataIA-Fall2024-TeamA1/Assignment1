import pyodbc
import json

# SQL Server 連接設定
server = 'LAPTOP-GD5THE3N'  # SQL Server 主機
database = 'big_data_assignment1'  # 資料庫名稱
driver = '{ODBC Driver 17 for SQL Server}'  # SQL Server ODBC 驅動

# 建立連接
connection = pyodbc.connect(f'DRIVER={driver};SERVER={server};DATABASE={database};Trusted_Connection=yes;')
cursor = connection.cursor()

with open('metadata.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

# Insert data into SQL Server
for record in data:
    task_id = record.get('task_id', '')
    question = record.get('Question', '')
    level = record.get('Level', 0)
    file_name = record.get('file_name', '')
    final_answer = record.get('Final answer', '')
    metadata = record.get('Annotator Metadata', {})
    
    steps = metadata.get('Steps', '')
    number_of_steps = metadata.get('Number of steps', '')
    how_long = metadata.get('How long did this take?', '')
    tools = metadata.get('Tools', '')
    number_of_tools = metadata.get('Number of tools', '')

    # Execute SQL command to insert the data
    cursor.execute('''
        INSERT INTO Tasks (task_id, Question, Level, file_name, Final_answer, Steps, Number_of_steps, How_long_did_this_take, Tools, Number_of_tools)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (task_id, question, level, file_name, final_answer, steps, number_of_steps, how_long, tools, number_of_tools))

# Commit the transaction
connection.commit()

# Close the connection
cursor.close()
connection.close()