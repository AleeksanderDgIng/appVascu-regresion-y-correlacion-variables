# app_controller.py

from flask import Flask, render_template, request, redirect, url_for, flash, get_flashed_messages
import mysql.connector
import os

from models.db_connection import get_db_connection
from controllers.regresion_lineal import RegresionLinealModel
from controllers.analizar_correlacion import analizar_correlacion

# Crear una instancia de la aplicación Flask
app = Flask(__name__, template_folder='views')
app.secret_key = os.urandom(24)
app.debug = False

# Inicializar la clase RegresionLinealModel
regresion_model = RegresionLinealModel()


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


# Función para obtener la lista de tablas en la base de datos
def get_table_list():
    db = connect_to_db()
    if db is not None:
        cursor = db.cursor()
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor]
        db.close()
        return tables
    else:
        return []


# Función para obtener las columnas de una tabla y sus registros
def get_table_info(table_name):
    columns = get_table_columns(table_name)
    records = get_table_records(table_name)
    return columns, records


# Función para obtener las columnas de una tabla
def get_table_columns(table_name):
    db = connect_to_db()
    if db is not None:
        cursor = db.cursor()
        cursor.execute(f"SHOW COLUMNS FROM {table_name}")
        columns = [col[0] for col in cursor.fetchall()]
        db.close()
        return columns
    else:
        return []


# Función para obtener los registros de una tabla
def get_table_records(table_name):
    db = connect_to_db()
    if db is not None:
        cursor = db.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        records = cursor.fetchall()
        db.close()
        return records
    else:
        return []


# Función para verificar si las variables son válidas para una tabla
def verificar_variables(selected_table, x_variable, y_variable):
    try:
        column_names = obtener_nombres_columnas(selected_table)
        if x_variable not in column_names:
            raise Exception(f"La variable X '{x_variable}' no es válida para la tabla '{selected_table}'.")
        if y_variable not in column_names:
            raise Exception(f"La variable Y '{y_variable}' no es válida para la tabla '{selected_table}'.")
        return True
    except Exception as e:
        return str(e)


# Función para obtener los nombres de las columnas de una tabla
def obtener_nombres_columnas(selected_table):
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


# Ruta principal ("/") para mostrar la página index.html
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


# Ruta para procesar la selección de una tabla en la base de datos y mostrar opciones de acción
@app.route('/seleccionar-tabla/<action>', methods=['GET', 'POST'])
def seleccionar_tabla(action):
    error_message = None
    selected_table = None
    records = []
    columns = []

    # Obtener la lista de tablas en la base de datos
    tables = get_table_list()

    if request.method == 'POST':
        selected_table = request.form.get('table')
        if selected_table:
            # Obtener las columnas y registros de la tabla seleccionada
            columns, records = get_table_info(selected_table)

    # Renderizar la plantilla 'seleccion.html' con los datos obtenidos
    return render_template('seleccion.html', action=action, tables=tables, selected_table=selected_table,
                           error_message=error_message, columns=columns, records=records)


# Ruta que permite al usuario seleccionar las variables para el análisis de regresión en una tabla de la base de datos.
@app.route('/seleccionar-variables-regresion/<table_name>', methods=['GET', 'POST'])
def seleccionar_variables_regresion(table_name):
    error_message = None
    selected_columns = []

    # Obtener la lista de columnas y registros de la tabla seleccionada
    columns, records = get_table_info(table_name)

    if request.method == 'POST':
        selected_columns = request.form.getlist('variables')

        if len(selected_columns) != 2:
            error_message = "Selecciona exactamente dos variables, una para X y otra para Y, para el análisis de regresión."

    # Renderizar la plantilla 'seleccion.html' con los datos obtenidos
    return render_template('seleccion.html', error_message=error_message or "", columns=columns,
                           table_name=table_name, selected_columns=selected_columns, records=records)


# Ruta para realizar la regresión lineal
@app.route('/regresion_lineal/<table_name>', methods=['POST'])
def regresion_lineal(table_name):
    error_message = ""
    success_message = ""
    prediction = None
    beta_0 = None
    beta_1 = None
    r_squared = None
    varianza_residual = None
    correlation_coefficient = None
    x_variable = None
    y_variable = None
    registros = None

    if request.method == 'POST':
        x_variable = request.form.get('x_variable')
        y_variable = request.form.get('y_variable')

        try:
            # Verificar si las variables son válidas para la tabla seleccionada
            verification_result = verificar_variables(table_name, x_variable, y_variable)
            if verification_result is True:
                # Realizar la regresión lineal
                (
                    success_message, error_message, prediction, beta_0, beta_1,
                    r_squared, varianza_residual, correlation_coefficient, registros
                ) = regresion_model.realizar_regresion_lineal(table_name, x_variable, y_variable)
        except ValueError:
            error_message = "Ingresa un valor válido para X."

    # Crear un contexto con los resultados y renderizar la plantilla 'resultado_regresion.html'
    context = {
        'table_name': table_name,
        'x_variable': x_variable,
        'y_variable': y_variable,
        'error_message': error_message,
        'success_message': success_message,
        'prediction': prediction,
        'beta_0': beta_0,
        'beta_1': beta_1,
        'r_squared': r_squared,
        'varianza_residual': varianza_residual,
        'correlation_coefficient': correlation_coefficient,
        'registros': registros
    }

    return render_template('resultado_regresion.html', **context)


# Ruta para realizar la predicción
@app.route('/realizar-prediccion', methods=['POST'])
def realizar_prediccion():
    result = None

    if request.method == 'POST':
        x_variable = request.form.get('x_variable')

        try:
            x_variable = float(x_variable)
            # Realizar la predicción utilizando el modelo de regresión lineal
            result = regresion_model.realizar_prediccion(x_variable)

        except ValueError:
            result = {
                'x_variable': None,
                'y_variable': None,
                'prediction': None,
                'error_message': "Ingresa un valor válido para X."
            }

    # Renderizar la plantilla 'resultado_regresion.html' con los resultados de la predicción
    return render_template('resultado_regresion.html', result=result)


# Ruta que permite al usuario seleccionar las variables para el análisis de correlación en una tabla de la base de datos.
@app.route('/seleccionar-variables-correlacion/<table_name>', methods=['GET', 'POST'])
def seleccionar_variables_correlacion(table_name):
    error_message = None
    selected_columns = []

    # Obtener la lista de columnas y registros de la tabla seleccionada
    columns, records = get_table_info(table_name)

    if request.method == 'POST':
        selected_columns = request.form.getlist('variables')

        if len(selected_columns) < 2:
            error_message = "Selecciona al menos dos variables para el análisis de correlación."

    # Renderizar la plantilla 'seleccion.html' con los datos obtenidos
    return render_template('seleccion.html', error_message=error_message or "", columns=columns,
                           table_name=table_name, selected_columns=selected_columns, records=records)


# Ruta para mostrar el mapa de calor de correlación
@app.route('/mostrar-mapa-de-calor/<table_name>', methods=['POST'])
def mostrar_resultado_correlacion(table_name):
    selected_columns = request.form.getlist('selected_columns')

    if len(selected_columns) < 2:
        return "Selecciona al menos dos variables para el análisis de correlación."

    # Llamar a la función analizar_correlación del módulo regresión
    result = analizar_correlacion(table_name, selected_columns)

    if "message" in result:
        # Si el resultado contiene un mensaje, mostrar el mapa de calor
        message = result["message"]
        heatmap_path = result["heatmap_path"]
        return render_template('resultado_correlacion.html', table_name=table_name, selected_columns=selected_columns,
                               message=message, heatmap_path=heatmap_path)
    else:
        return result  # Devuelve el resultado (puede ser un error o el mapa de calor)


# Iniciar la aplicación si este archivo se ejecuta directamente
if __name__ == '__main__':
    app.run(debug=True)
