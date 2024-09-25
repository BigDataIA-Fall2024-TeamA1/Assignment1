import os
import pyodbc
from dotenv import load_dotenv

def get_metadata_from_sql():
    # Load environment variables from .env file
    load_dotenv()

    # Read SQL Server connection settings from environment variables
    server = os.getenv('SQL_SERVER')        # Server name
    database = os.getenv('SQL_DATABASE')    # Database name
    username = os.getenv('SQL_USER')        # SQL username
    password = os.getenv('SQL_PASSWORD')    # SQL password
    driver = '{ODBC Driver 17 for SQL Server}'  # SQL Server ODBC driver

    # Establish connection using SQL Server authentication
    connection = pyodbc.connect(
        f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password};'
    )
    
    cursor = connection.cursor()
    
    # Execute query to fetch necessary fields
    cursor.execute('''
        SELECT task_id, Question, Final_answer, Steps, Number_of_steps, 
               How_long_did_this_take, Tools, Number_of_tools 
        FROM Tasks
    ''')
    rows = cursor.fetchall()
    
    # Organize the fetched data into a list of dictionaries
    metadata = []
    for row in rows:
        metadata.append({
            'task_id': row.task_id,
            'Question': row.Question,
            'Final answer': row.Final_answer,
            'Steps': row.Steps,
            'Number of steps': row.Number_of_steps,
            'How long did this take?': row.How_long_did_this_take,
            'Tools': row.Tools,
            'Number of tools': row.Number_of_tools
        })

    # Close the database connection
    cursor.close()
    connection.close()

    return metadata

def update_metadata_steps(task_id, new_steps):
    """
    Updates the 'Steps' field for a given task_id.

    Parameters:
    - task_id (str): The unique identifier for the task.
    - new_steps (str): The updated steps to replace the existing ones.

    Returns:
    - bool: True if the update was successful, False otherwise.
    """
    load_dotenv()

    # Read SQL Server connection settings from environment variables
    server = os.getenv('SQL_SERVER')        # Server name
    database = os.getenv('SQL_DATABASE')    # Database name
    username = os.getenv('SQL_USER')        # SQL username
    password = os.getenv('SQL_PASSWORD')    # SQL password
    driver = '{ODBC Driver 17 for SQL Server}'  # SQL Server ODBC driver

    try:
        # Establish connection
        connection = pyodbc.connect(
            f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password};'
        )
        cursor = connection.cursor()

        # Update the 'Steps' column for the given task_id
        cursor.execute(
            '''
            UPDATE Tasks 
            SET Steps = ? 
            WHERE task_id = ?
            ''',
            new_steps,
            task_id
        )
        connection.commit()
        success = True

    except Exception as e:
        print(f"Error updating Steps: {e}")
        success = False
    finally:
        # Ensure the connection is closed
        cursor.close()
        connection.close()

    return success
