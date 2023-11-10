# models/db_connection.py


import mysql.connector

# Conexion a la base de datos
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

