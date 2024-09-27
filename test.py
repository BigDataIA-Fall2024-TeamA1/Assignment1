from dotenv import load_dotenv
import os
import pyodbc





print(os.environ)
# 加载环境变量
load_dotenv()

# 调试输出，确保环境变量被正确加载
print(f"SQL_SERVER: {os.getenv('SQL_SERVER')}")
print(f"SQL_DATABASE: {os.getenv('SQL_DATABASE')}")
print(f"SQL_USER: {os.getenv('SQL_USER')}")
print(f"SQL_PASSWORD: {os.getenv('SQL_PASSWORD')}")

# 打印调试信息
server = os.getenv('SQL_SERVER')
database = os.getenv('SQL_DATABASE')
username = os.getenv('SQL_USER')
password = os.getenv('SQL_PASSWORD')

print(f"Server: {server}, Database: {database}, User: {username}, Password: {password}")

# 测试连接
driver = '{ODBC Driver 17 for SQL Server}'

try:
    connection = pyodbc.connect(
        f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password};'
    )
    print("Connection successful!")
except pyodbc.Error as e:
    print(f"Connection failed: {e}")