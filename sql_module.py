import streamlit as st
import pyodbc

def get_metadata_from_sql():
    # SQL Server connection settings
    server = st.secrets["sql_server"]["address"]       # Server name
    database = st.secrets["sql_server"]["database"]    # Database name
    username = st.secrets["sql_server"]["user"]        # SQL username
    password = st.secrets["sql_server"]["password"]    # SQL password
    driver = '{ODBC Driver 17 for SQL Server}'         # SQL Server ODBC driver

    # Establish connection using SQL Server authentication
    connection = pyodbc.connect(
        f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password};'
    )

    cursor = connection.cursor()
    
    cursor.execute('''
        SELECT task_id, Question, file_name, Final_answer, Steps, Number_of_steps, 
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
            'file_name': row.file_name,
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
    """
    # Read SQL Server connection settings from Streamlit secrets
    server = st.secrets["sql_server"]["address"]
    database = st.secrets["sql_server"]["database"]
    username = st.secrets["sql_server"]["user"]
    password = st.secrets["sql_server"]["password"]
    driver = '{ODBC Driver 17 for SQL Server}'

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

def insert_evaluation(task_id, is_correct, user_feedback=None):
    """
    Inserts a new evaluation record into the Evaluations table.
    """
    # Read SQL Server connection settings from Streamlit secrets
    server = st.secrets["sql_server"]["address"]
    database = st.secrets["sql_server"]["database"]
    username = st.secrets["sql_server"]["user"]
    password = st.secrets["sql_server"]["password"]
    driver = '{ODBC Driver 17 for SQL Server}'

    try:
        # Establish connection
        connection = pyodbc.connect(
            f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password};'
        )
        cursor = connection.cursor()

        # Insert into Evaluations
        cursor.execute(
            '''
            INSERT INTO Evaluations (task_id, is_correct, user_feedback)
            VALUES (?, ?, ?)
            ''',
            task_id,
            int(is_correct),  # Convert boolean to integer (1 or 0)
            user_feedback
        )
        connection.commit()
        success = True

    except Exception as e:
        print(f"Error inserting evaluation: {e}")
        success = False
    finally:
        # Ensure the connection is closed
        cursor.close()
        connection.close()

    return success

def get_evaluations():
    """
    Retrieves all evaluation records from the Evaluations table.
    """
    # Read SQL Server connection settings from Streamlit secrets
    server = st.secrets["sql_server"]["address"]
    database = st.secrets["sql_server"]["database"]
    username = st.secrets["sql_server"]["user"]
    password = st.secrets["sql_server"]["password"]
    driver = '{ODBC Driver 17 for SQL Server}'

    try:
        # Establish connection
        connection = pyodbc.connect(
            f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password};'
        )
        cursor = connection.cursor()

        # Fetch all evaluations
        cursor.execute('SELECT evaluation_id, task_id, is_correct, user_feedback, evaluation_timestamp FROM Evaluations')
        rows = cursor.fetchall()

        # Organize into list of dictionaries
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
        # Ensure the connection is closed
        cursor.close()
        connection.close()

    return evaluations
