# app_controller.py

from flask import Flask, render_template, request, redirect, url_for  # Importar módulos de Flask
import mysql.connector  # Importar el conector MySQL
import xlrd  # Importar para procesar archivos de Excel
from sklearn.linear_model import LinearRegression  # Importa el modelo de regresión lineal
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import StandardScaler  # Importa el escalador StandardScaler
from models.db_connection import get_db_connection  # Importar la función de conexión a la base de datos
from controllers.regresion_lineal import RegresionLinealModel# Importa la clase
from controllers.analizar_correlacion import analizar_correlacion  # Importar función para analizar correlación
from models.db_connection import get_db_connection
import pickle


# Crear una instancia de la aplicación Flask
app = Flask(__name__, template_folder='views')
app.debug = False  # Desactivar el modo de depuración de la aplicación

# Inicializar la clase RegresionLinealModel
regresion_model = RegresionLinealModel()

# Definir success_message como cadena vacía al principio
success_message = ""

# Inicializar las variables globales
tables = []  # Almacena los nombres de las tablas en la base de datos
records = []  # Almacena los registros de la tabla seleccionada
selected_table = None
columns = []  # Lista de columnas de la tabla seleccionada



# Función para conectar a la base de datos MySQL
def connect_to_db():
    try:
        db = get_db_connection()  # Obtener una conexión a la base de datos utilizando una función externa

        if db is not None:
            return db
        else:
            return None
    except mysql.connector.Error as err:
        return None

# Ruta principal ("/") para mostrar la página index.html
@app.route('/', methods=['GET'])
def index():
    # Renderiza la plantilla index.html
    return render_template('index.html')

# Ruta para procesar la selección de una tabla en la base de datos y mostrar opciones de acción
@app.route('/seleccionar-tabla/<action>', methods=['GET', 'POST'])
def seleccionar_tabla(action):
    error_message = None
    selected_table = None
    records = []  # Almacenará los registros de la tabla seleccionada
    columns = []  # Lista de columnas de la tabla seleccionada

    # Intentar conectarse a la base de datos para obtener la lista de tablas
    db = connect_to_db()  # Llamar a la función para conectar a la base de datos
    if db is not None:  # Si la conexión a la base de datos es exitosa
        cursor = db.cursor()  # Crear un cursor para ejecutar consultas SQL
        cursor.execute("SHOW TABLES")  # Consulta SQL para obtener la lista de tablas
        tables = [table[0] for table in cursor]  # Obtener la lista de tablas desde el cursor
        db.close()  # Cerrar la conexión a la base de datos
    else:
        tables = []  # Si no se puede conectar a la base de datos, establece la lista de tablas como vacía

    if request.method == 'POST':  # Si se envía un formulario mediante el método POST
        selected_table = request.form.get('table')  # Obtener el nombre de la tabla seleccionada desde el formulario
        if selected_table:  # Si se selecciona una tabla
            if action == 'correlacion':
                # Redirige a la vista de correlación con el nombre de la tabla como argumento
                return redirect(url_for('seleccionar_variables_correlacion', table_name=selected_table))
            elif action == 'regresion':
                # Redirige a la vista de regresión con el nombre de la tabla como argumento
                return redirect(url_for('seleccionar_variables_regresion', table_name=selected_table))
        else:
            error_message = "Selecciona una tabla antes de continuar."  # Mensaje de error si no se selecciona una tabla

    # Obtener los registros de la tabla seleccionada
    if selected_table:  # Si se ha seleccionado una tabla
        db = connect_to_db()  # Conectar a la base de datos nuevamente
        if db is not None:
            cursor = db.cursor()  # Crear un cursor para ejecutar consultas SQL
            cursor.execute(f"SHOW COLUMNS FROM {selected_table}")  # Consulta SQL para obtener las columnas de la tabla
            columns = [col[0] for col in cursor.fetchall()]  # Obtener la lista de nombres de columnas desde el cursor
            cursor.execute(f"SELECT * FROM {selected_table}")  # Consulta SQL para obtener los registros de la tabla
            records = cursor.fetchall()  # Obtener los registros desde el cursor
            db.close()  # Cerrar la conexión a la base de datos

    # Renderizar la plantilla 'seleccionar_tabla.html' con los datos obtenidos
    return render_template('seleccionar_tabla.html', action=action, tables=tables, selected_table=selected_table, error_message=error_message, columns=columns, records=records)


#REGRESION LINEAL
#ruta que permite al usuario seleccionar las variables para el análisis de regresión en una tabla de la base de datos.
@app.route('/seleccionar-variables-regresion/<table_name>', methods=['GET', 'POST'])
def seleccionar_variables_regresion(table_name):
    error_message = None
    selected_columns = []
    records = []  # Almacenará los registros de la tabla seleccionada

    # Obtén la lista de columnas de la tabla seleccionada
    db = connect_to_db()  # Se llama a la función para conectar a la base de datos
    if db is not None:  # Si la conexión a la base de datos es exitosa
        cursor = db.cursor()  # Crear un cursor para ejecutar consultas SQL
        cursor.execute(f"SHOW COLUMNS FROM {table_name}")  # Consulta SQL para obtener la lista de columnas de la tabla
        columns = [col[0] for col in cursor.fetchall()]  # Obtener la lista de columnas desde el cursor
        cursor.execute(f"SELECT * FROM {table_name}")  # Consulta SQL para obtener los registros de la tabla
        records = cursor.fetchall()  # Obtener los registros desde el cursor
        db.close()  # Cerrar la conexión a la base de datos
    else:
        columns = []  # Si no se puede conectar a la base de datos, establece la lista de columnas como vacía

    if request.method == 'POST':  # Si se envía un formulario mediante el método POST
        selected_columns = request.form.getlist('variables')  # Obtiene la lista de variables seleccionadas desde el formulario

        if len(selected_columns) != 2:  # Comprueba si se han seleccionado exactamente dos variables (una para X y otra para Y) para realizar un análisis de regresión.
            error_message = "Selecciona exactamente dos variables, una para X y otra para Y, para el análisis de regresión."

    return render_template('seleccionar_variables_regresion.html', error_message=error_message or "", columns=columns, table_name=table_name, selected_columns=selected_columns, records=records)

# Función para verificar si la tabla y las variables son válidas
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

# Función para obtener los nombres de las columnas de la tabla
def obtener_nombres_columnas(selected_table):
    try:
        # Conexión a la base de datos
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
            verification_result = verificar_variables(table_name, x_variable, y_variable)
            if verification_result is True:
                (
                    success_message, error_message, prediction, beta_0, beta_1,
                    r_squared, varianza_residual, correlation_coefficient, registros
                ) = regresion_model.realizar_regresion_lineal(table_name, x_variable, y_variable)
        except ValueError:
            error_message = "Ingresa un valor válido para X."

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
        'registros': registros  # Agrega esta línea
    }

    return render_template('resultado_regresion.html', **context)




# Ruta para mostrar los resultados de la regresión
@app.route('/resultado-regresion', methods=['GET'])
def resultado_regresion():
    return render_template('regresion.html', success_message=success_message, error_message=None)



# Ruta para realizar la predicción
@app.route('/realizar-prediccion', methods=['POST'])
def realizar_prediccion():
    result = None  # Inicializa el resultado

    if request.method == 'POST':
        x_variable = request.form.get('x_variable')  # Obtiene el valor de X del formulario

        try:
            x_variable = float(x_variable)  # Intenta convertir el valor de X a un número de punto flotante
            result = regresion_model.realizar_prediccion(x_variable)

        except ValueError:
            result = {
                'x_variable': None,
                'y_variable': None,
                
                'prediction': None,
                'error_message': "Ingresa un valor válido para X."
            }

    return render_template('resultado_regresion.html', result=result)





# Ruta para crear un nuevo registro desde un archivo Excel
@app.route('/crear_registro/<table_name>', methods=['GET', 'POST'])
def crear_registro(table_name):
    error_message = None
    success_message = None

    if request.method == 'POST':
        if 'excel_file' not in request.files:
            error_message = "No se ha proporcionado un archivo de Excel."
        else:
            excel_file = request.files['excel_file']
            if excel_file.filename == '':
                error_message = "No se ha seleccionado un archivo de Excel."
            else:
                try:
                    # Leer el archivo de Excel y obtener los datos
                    workbook = xlrd.open_workbook(file_contents=excel_file.read())
                    sheet = workbook.sheet_by_index(0)
                    header = [sheet.cell(0, col).value for col in range(sheet.ncols)]
                    data = []

                    for row_index in range(1, sheet.nrows):
                        row_data = [sheet.cell(row_index, col).value for col in range(sheet.ncols)]
                        data.append(row_data)

                    # Realizar validación de datos
                    valid_data = []
                    for row in data:
                        # Validar que los valores de salario sean números válidos
                        salario_index = header.index('salario') if 'salario' in header else -1
                        if salario_index >= 0:
                            salario_value = row[salario_index]
                            if not isinstance(salario_value, (float, int)) or salario_value < 0:
                                error_message = f"Error en la fila {data.index(row) + 2}: El valor de salario no es un número válido."
                                break
                        valid_data.append(row)
                    
                    if not error_message:
                        # Conectar a la base de datos y crear registros
                        db = connect_to_db()
                        if db is not None:
                            cursor = db.cursor()
                            placeholders = ', '.join(['%s'] * len(header))
                            insert_query = f"INSERT INTO {table_name} ({', '.join(header)}) VALUES ({placeholders})"
                            
                            try:
                                cursor.executemany(insert_query, valid_data)
                                db.commit()
                                success_message = "Registros creados con éxito desde el archivo de Excel."
                            except mysql.connector.Error as err:
                                db.rollback()
                                error_message = f"No se pudieron crear los registros: {err}"
                            finally:
                                db.close()
                except xlrd.XLRDError as err:
                    error_message = f"No se pudo leer el archivo de Excel: {err}"
                except Exception as e:
                    error_message = f"Error inesperado: {e}"

    return render_template('crear_registro.html', error_message=error_message or "", success_message=success_message or "", table_name=table_name)


#CORRELACION

# Ruta para mostrar el mapa de calor de correlación
@app.route('/mostrar-mapa-de-calor/<table_name>', methods=['POST'])
def mostrar_mapa_de_calor(table_name):
    selected_columns = request.form.getlist('selected_columns')  # Obtiene la lista de columnas seleccionadas desde el formulario

    if len(selected_columns) < 2:  # Comprueba si se han seleccionado menos de dos variables para el análisis de correlación
        return "Selecciona al menos dos variables para el análisis de correlación."

    # Llama a la función analizar_correlación del módulo regresión
    result = analizar_correlacion(table_name, selected_columns)

    if "message" in result:  # Comprueba si el resultado de la función contiene un mensaje
        message = result["message"]  # Obtiene el mensaje del resultado
        heatmap_path = result["heatmap_path"]  # Obtiene la ruta de la imagen del mapa de calor
        return render_template('mapa_de_calor.html', table_name=table_name, selected_columns=selected_columns, message=message, heatmap_path=heatmap_path)
    else:
        return result  # Devuelve el resultado (puede ser un error o el mapa de calor)


#ruta que permite al usuario seleccionar las variables para el análisis de correlación en una tabla de la base de datos.
@app.route('/seleccionar-variables-correlacion/<table_name>', methods=['GET', 'POST'])
def seleccionar_variables_correlacion(table_name):
    error_message = None
    selected_columns = []

    # Obtén la lista de columnas de la tabla seleccionada
    db = connect_to_db()  # Se llama a la función para conectar a la base de datos
    if db is not None:  # Si la conexión a la base de datos es exitosa
        cursor = db.cursor()  # Crear un cursor para ejecutar consultas SQL
        cursor.execute(f"SHOW COLUMNS FROM {table_name}")  # Consulta SQL para obtener la lista de columnas de la tabla
        columns = [col[0] for col in cursor.fetchall()]  # Obtener la lista de columnas desde el cursor
        cursor.execute(f"SELECT * FROM {table_name}")  # Consulta SQL para obtener los registros de la tabla
        records = cursor.fetchall()  # Obtener los registros desde el cursor
        db.close()  # Cerrar la conexión a la base de datos
    else:
        columns = []  # Si no se puede conectar a la base de datos, establece la lista de columnas como vacía
        records = []  # Establece la lista de registros como vacía

    if request.method == 'POST':  # Si se envía un formulario mediante el método POST
        selected_columns = request.form.getlist('variables')  # Obtiene la lista de variables seleccionadas desde el formulario

        if len(selected_columns) < 2:  # Comprueba si se han seleccionado menos de dos variables para realizar un análisis de correlación
            error_message = "Selecciona al menos dos variables para el análisis de correlación."

    return render_template('seleccionar_variables_correlacion.html', error_message=error_message or "", columns=columns, table_name=table_name, selected_columns=selected_columns, records=records)


# Iniciar la aplicación si este archivo se ejecuta directamente
if __name__ == '__main__':
    app.run(debug=True)