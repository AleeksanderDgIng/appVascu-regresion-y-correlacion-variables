import mysql.connector

def get_db_connection():
    try:
        db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="vascubd"
        )
        return db
    except mysql.connector.Error as err:
        return None
