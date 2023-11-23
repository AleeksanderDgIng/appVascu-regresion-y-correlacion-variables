from flask import Flask, render_template, request, redirect, url_for, flash, get_flashed_messages
import mysql.connector
from models.db_connection import get_db_connection

# Función para conectar a la base de datos MySQL
def connect_to_db():
    try:
        db = get_db_connection()
        if db is not None:
            return db
        else:
            return None
    except mysql.connector.Error as err:
        return None
    
    # Función para obtener la lista de tablas en la base de datos OK
def get_table_list_etl():
    db = connect_to_db()
    if db is not None:
        cursor = db.cursor()
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor]
        table_list = []
        for table_name in tables:
            columns = get_table_columns_etl(table_name)
            table_list.append({'name': table_name, 'columns': columns})
        db.close()
        return table_list
    else:
        return []
    
# Función para obtener los registros de una tabla
def get_table_records_etl(table_name):
    db = connect_to_db()
    if db is not None:
        cursor = db.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        records = cursor.fetchall()
        db.close()
        return records
    else:
        return []
    
    
    # Función para obtener las columnas de una tabla y sus registros
def get_table_info_etl(table_name):
    columns = get_table_columns_etl(table_name)
    records = get_table_records_etl(table_name)
    return columns, records

# Función para obtener nombres y tipos de datos de las columnas
def get_table_columns_etl(table_name):
    db = connect_to_db()
    if db is not None:
        cursor = db.cursor()
        cursor.execute(f"SHOW COLUMNS FROM {table_name}")
        columns = [{'name': col[0], 'type': col[1]} for col in cursor.fetchall()]
        db.close()
        return columns
    else:
        return []
    

# Función para obtener los nombres de las columnas de una tabla
def obtener_nombres_columnas_etl(selected_table):
    try:
        db = get_db_connection()
        if db.is_connected():
            cursor = db.cursor()
            query = f"SHOW COLUMNS FROM {selected_table}"
            cursor.execute(query)
            result = cursor.fetchall()
            db.close()

            if result:
                column_names = [row[0] for row in result]
                return column_names
            else:
                raise Exception(f"No se encontraron columnas en la tabla '{selected_table}'.")
        else:
            raise Exception("La conexión a la base de datos no está activa.")
    except Exception as e:
        raise Exception(f"Error al conectar a la base de datos: {e}")

