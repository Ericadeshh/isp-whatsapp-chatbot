# Save as test_connection.py
import pymysql  # pyright: ignore[reportMissingModuleSource]
try:
    conn = pymysql.connect(host='localhost', user='Ericadesh', password='404-found-#', database='isp_chatbot')
    print("Connected isp chatbot database successfully⚡!")
    conn.close()
except Exception as e:
    print(f"Error: {e}")