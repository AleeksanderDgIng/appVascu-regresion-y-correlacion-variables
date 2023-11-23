# app_controller.py

from flask import Flask, render_template, request, redirect, url_for, flash, get_flashed_messages, render_template_string, send_file
import mysql.connector
import os
from io import BytesIO
import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import NamedStyle
from openpyxl import Workbook, styles
import tempfile

from models.db_connection import get_db_connection
from controllers.regresion_lineal import RegresionLinealModel
from controllers.analizar_correlacion import analizar_correlacion
from flask_session import Session
from controllers.etl import *

# Crear una instancia de la aplicación Flask
app = Flask(__name__, template_folder='views')
app.secret_key = os.urandom(24)

app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

app.debug = False

# Inicializar la clase RegresionLinealModel
regresion_model = RegresionLinealModel()

#----------------------------SELECCION----------------------------

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
def get_table_list():
    db = connect_to_db()
    if db is not None:
        cursor = db.cursor()
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor]
        table_list = []
        for table_name in tables:
            columns = get_table_columns(table_name)
            table_list.append({'name': table_name, 'columns': columns})
        db.close()
        return table_list
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
    tables = get_table_list()
    return render_template('seleccion.html', action='seleccion', tables=tables, selected_tables=[])

# Ruta para procesar la selección de tabla(s) en la base de datos y mostrar opciones de acción
@app.route('/seleccionar-tabla/<action>', methods=['GET', 'POST'])
def seleccionar_tabla(action):
    error_message = None
    selected_tables = []
    records = {}
    columns = {}
    selected_variables = {'x_variable': None, 'y_variable': None}  # Inicialización

    # Obtener la lista de tablas en la base de datos
    tables = get_table_list()

    if request.method == 'POST':
        selected_tables = request.form.getlist('table')
        if selected_tables:
            # Obtener las columnas y registros de todas las tablas seleccionadas
            for table_name in selected_tables:
                table_columns, table_records = get_table_info(table_name)
                columns[table_name] = table_columns
                records[table_name] = table_records

    # Obtener las variables seleccionadas si ya se han seleccionado en la primera acción
    if 'selected_variables' in request.form:
        selected_variables['x_variable'] = request.form.get('x_variable')
        selected_variables['y_variable'] = request.form.get('y_variable')

    # Pasa selected_variables al renderizar la plantilla
    return render_template('seleccion.html', action=action, tables=tables, selected_tables=selected_tables,
                           error_message=error_message, columns=columns, records=records,
                           selected_variables=selected_variables)

#----------------------------CORRELACION----------------------------

# Ruta que permite al usuario seleccionar las variables para el análisis de correlación en una tabla de la base de datos.
@app.route('/seleccionar-variables-correlacion/<table_name>', methods=['GET', 'POST'])
def seleccionar_variables_correlacion(table_name):
    error_message = None
    selected_columns = []

    # Obtener la lista de columnas y registros de la tabla seleccionada
    columns, records = get_table_info(table_name)

    if request.method == 'POST':
        selected_columns = request.form.getlist('variables[]')  

    # Renderizar la plantilla 'seleccion.html' con los datos obtenidos
    return render_template('seleccion.html', error_message=error_message or "", columns=columns,
                           table_name=table_name, selected_columns=selected_columns, records=records)

# Ruta para mostrar el mapa de calor de correlación
@app.route('/mostrar-mapa-de-calor', methods=['POST'])
def mostrar_resultado_correlacion():
    selected_tables = request.form.get('table_names').split(',')
    selected_columns = request.form.getlist('variables[]')

    print("Selected tables:", selected_tables)
    print("Selected columns:", selected_columns)

    # Llamar a la función analizar_correlación del módulo regresión
    result = analizar_correlacion(', '.join(selected_tables), selected_columns)

    if "message" in result:
        # Si el resultado contiene un mensaje, mostrar el mapa de calor
        message = result["message"]
        heatmap_path = result["heatmap_path"]
        return render_template('resultado_correlacion.html', selected_tables=selected_tables,
                               selected_columns=selected_columns, message=message, heatmap_path=heatmap_path)
    else:
        return result  # Devuelve el resultado (puede ser un error o el mapa de calor)

#----------------------------REGRESION----------------------------

# Ruta que permite al usuario seleccionar las variables para el análisis de regresión en una tabla de la base de datos.
@app.route('/seleccionar-variables-regresion/<table_name>', methods=['GET', 'POST'])
def seleccionar_variables_regresion(table_name):
    error_message = None
    selected_columns = []

    # Obtener la lista de columnas y registros de la tabla seleccionada
    columns, records = get_table_info(table_name)

    if request.method == 'POST':
        selected_columns = request.form.getlist('variables')

    # Renderizar la plantilla 'seleccion.html' con los datos obtenidos
    return render_template('seleccion.html', error_message=error_message or "", columns=columns,
                           table_name=table_name, selected_columns=selected_columns, records=records)

# Función para verificar si las variables son válidas para una tabla
def verificar_variables(selected_tables, x_variable, y_variable):
    try:
        # Iterar sobre todas las tablas seleccionadas
        for selected_table in selected_tables:
            # Obtener los nombres de las columnas para la tabla actual
            column_names = obtener_nombres_columnas(selected_table)
            
            # Verificar si las variables son válidas para la tabla actual
            if x_variable not in column_names:
                raise Exception(f"La variable X '{x_variable}' no es válida para la tabla '{selected_table}'.")
            if y_variable not in column_names:
                raise Exception(f"La variable Y '{y_variable}' no es válida para la tabla '{selected_table}'.")
        
        # Si ha pasado la verificación para todas las tablas, devolver True
        return True
    except Exception as e:
        # Si se encuentra alguna excepción, devolver el mensaje de error
        return str(e)

# Ruta para realizar la regresión lineal
@app.route('/regresion_lineal', methods=['POST'])
def regresion_lineal():
    error_message = ""
    success_message = ""
    prediction = None
    beta_0 = None
    beta_1 = None
    r_squared = None
    correlation_coefficient = None
    x_variable = None
    y_variable = None
    registros = None

    if request.method == 'POST':
        selected_tables = request.form.get('table_names').split(',')
        x_variable = request.form.get('x_variable')
        y_variable = request.form.get('y_variable')

        print("Selected tables:", selected_tables)
        print("x_variable:", x_variable)
        print("y_variable:", y_variable)
    
        try:
            # Verificar si las variables son válidas para la tabla seleccionada
            #verification_result = verificar_variables(', '.join(selected_tables), x_variable, y_variable)
            verification_result = all(verificar_variables(selected_table, x_variable, y_variable) for selected_table in selected_tables)

            print(f"registros: {registros}")
            print(f"Valores recibidos antes del if - selected_tables:¨{selected_tables}, x_variable: {x_variable}, y_variable: {y_variable}" )
            
            if verification_result is True:
                
                print(f"Valores recibidos despues del if - selected_tables:¨{selected_tables}, x_variable: {x_variable}, y_variable: {y_variable}" )
               

                # Realizar la regresión lineal
                (
                    success_message, error_message, prediction, beta_0, beta_1,
                    r_squared, correlation_coefficient, registros
                ) = regresion_model.realizar_regresion_lineal(', '.join(selected_tables), x_variable, y_variable)
                print(f"registros: {registros}")
                print(f"verificar los valores obteniendo regresion, beta_0: {beta_0}")
                print(f"verificar los valores obteniendo regresion, beta_1: {beta_1}")
                print(f"verificar los valores obteniendo regresion, r_squared: {r_squared}")
                print(f"verificar los valores obteniendo regresion, correlation_coefficient: {correlation_coefficient}")
                
            else: print(f"la variables NO son válidas para la tabla seleccionada")
            
        except ValueError:
            error_message = "Ingresa un valor válido para X."

    # Crear un contexto con los resultados y renderizar la plantilla 'resultado_regresion.html'
    context = {
        'table_name': ', '.join(selected_tables),
        'x_variable': x_variable,
        'y_variable': y_variable,
        'error_message': error_message,
        'success_message': success_message,
        'prediction': prediction,
        'beta_0': beta_0,
        'beta_1': beta_1,
        'r_squared': r_squared,
        'correlation_coefficient': correlation_coefficient,
        'registros': registros
    }

    print(f"valores antes de pasar al contexto, beta_0: {beta_0}")
    print(f"valores antes de pasar al contexto, beta_1: {beta_1}")
    print(f"valores antes de pasar al contexto, r_squared: {r_squared}")
    print(f"valores antes de pasar al contexto, correlation_coefficient: {correlation_coefficient}")
    
    return render_template('resultado_regresion.html', **context)

#----------------------------PREDICCION----------------------------

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

        except ValueError as ve:
            print(f"Error al convertir a float: {ve}")
            result = {
                'x_variable': None,
                'y_variable': None,
                'prediction': None,
                'error_message': "Ingresa un valor válido para X."
            }

    # Renderizar la plantilla 'resultado_regresion.html' con los resultados de la predicción
    return render_template('resultado_regresion.html', result=result)



#---------------------------- RUTA ETL----------------------------

# Ruta para ver y seleccionar datos de una tabla
@app.route('/ver-datos', methods=['GET', 'POST'])
def ver_datos():
    tables = get_table_list_etl()
    table_name = None
    columns = []
    records = []

    if request.method == 'POST':
        table_name = request.form.get('table_name')
        columns, records = get_table_info_etl(table_name)

    return render_template('datos.html', tables=tables, table_name=table_name, columns=columns, records=records)

#---------------
# Ruta para editar un registro
@app.route('/editar/<table_name>/<int:record_id>', methods=['GET', 'POST'])
def editar_registro(table_name, record_id):
    columns = obtener_nombres_columnas_etl(table_name)
    record = obtener_registro_etl(table_name, record_id)

    if request.method == 'POST':
        # Obtener los nuevos valores desde el formulario
        nuevos_valores = {}
        for columna in columns:
            nuevos_valores[columna] = request.form[columna]

        # Actualizar el registro en la base de datos
        actualizar_registro_etl(table_name, record_id, nuevos_valores)

        # Redirigir a la página de ver datos
        return redirect(url_for('ver_datos'))

    return render_template('editar_registro.html', table_name=table_name, columns=columns, record=record)


# Función para obtener un registro por ID
def obtener_registro_etl(table_name, record_id):
    db = connect_to_db()
    if db is not None:
        cursor = db.cursor()
        cursor.execute(f"SELECT * FROM {table_name} WHERE id = %s", (record_id,))
        record = cursor.fetchone()
        db.close()
        return record
    else:
        return None

# Función para actualizar un registro por ID
def actualizar_registro_etl(table_name, record_id, nuevos_valores):
    db = connect_to_db()
    if db is not None:
        cursor = db.cursor()

        # Construir la consulta SQL para la actualización
        update_query = f"UPDATE {table_name} SET "
        update_query += ', '.join([f"{column} = %s" for column in nuevos_valores.keys()])
        update_query += f" WHERE id = %s"

        # Crear una tupla con los nuevos valores y el ID del registro
        valores_actualizados = tuple(nuevos_valores.values()) + (record_id,)

        # Ejecutar la consulta
        cursor.execute(update_query, valores_actualizados)

        # Confirmar la transacción y cerrar la conexión
        db.commit()
        db.close()

#----------------

# Ruta para eliminar un registro
@app.route('/eliminar/<table_name>/<int:record_id>', methods=['GET', 'POST'])
def eliminar_registro(table_name, record_id):
    if request.method == 'POST':
        # Lógica para eliminar el registro de la base de datos
        eliminar_registro_etl(table_name, record_id)

        # Redirigir a la página de ver datos después de eliminar
        return redirect(url_for('ver_datos'))

    return render_template('eliminar_registro.html', table_name=table_name, record_id=record_id)


# Función para obtener y luego eliminar un registro por ID
def eliminar_registro_etl(table_name, record_id):
    db = connect_to_db()
    if db is not None:
        cursor = db.cursor()

        # Obtener los datos del registro antes de eliminarlo
        cursor.execute(f"SELECT * FROM {table_name} WHERE id = %s", (record_id,))
        record = cursor.fetchone()

        if record:
            print(f"Datos del registro antes de eliminar: {record}")

            # Eliminar el registro de la base de datos solo si se encontraron datos
            cursor.execute(f"DELETE FROM {table_name} WHERE id = %s", (record_id,))
            db.commit()

            print("Registro eliminado correctamente.")
        else:
            print("No se encontraron datos para el registro.")

        db.close()

        return record  # Devolvemos los datos del registro eliminado o None si no se encontraron datos

#-------------------

# Función para obtener nombres y tipos de datos de las columnas
def get_table_columns_etl(table_name):
    db = connect_to_db()
    if db is not None:
        cursor = db.cursor()
        cursor.execute(f"SHOW COLUMNS FROM {table_name}")
        columns = cursor.fetchall()
        db.close()
        return columns
    else:
        return []

# Ruta para descargar la plantilla
@app.route('/descargar-plantilla/<table_name>', methods=['GET'])
def descargar_plantilla(table_name):
    # Obtener información sobre las columnas y tipos de datos de la tabla desde la base de datos
    columnas_tipos = get_table_columns_etl(table_name)
    columnas = [col[0] for col in columnas_tipos]
    tipos_de_datos = [col[1] for col in columnas_tipos]

    # Crear una plantilla de Pandas DataFrame con columnas y tipos de datos
    df_template = pd.DataFrame(columns=columnas)

    # Crear un libro de trabajo de Excel y una hoja
    wb = Workbook()
    ws = wb.active

    # Crear estilos para cada tipo de dato
    styles_dict = {
        'int': styles.NamedStyle(name='int_style', number_format=styles.numbers.FORMAT_NUMBER),
        'float': styles.NamedStyle(name='float_style', number_format=styles.numbers.FORMAT_NUMBER_00),
        'str': styles.NamedStyle(name='str_style')
    }

    # Agregar encabezados a la hoja de cálculo con el estilo correspondiente
    for col_num, (columna, tipo_de_dato) in enumerate(zip(columnas, tipos_de_datos), 1):
        cell = ws.cell(row=1, column=col_num, value=columna)
        estilo_name = f'{tipo_de_dato}_style'

        # Verificar si el estilo ya existe antes de agregarlo
        if estilo_name not in wb.named_styles:
            estilo = styles_dict.get(tipo_de_dato, styles.NamedStyle(name=estilo_name))
            wb.add_named_style(estilo)

        # Aplicar el estilo a la celda
        cell.style = estilo_name

    # Crear un archivo temporal para almacenar el libro de trabajo
    temp_file, temp_filename = tempfile.mkstemp(suffix='.xlsx')
    os.close(temp_file)
    
    # Guardar el libro de trabajo en el archivo temporal
    wb.save(temp_filename)

    # Devolver el archivo para su descarga
    return send_file(
        temp_filename,
        download_name=f'{table_name}_template.xlsx',
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )








# Iniciar la aplicación si este archivo se ejecuta directamente
if __name__ == '__main__':
    app.run(debug=True)
