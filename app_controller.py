# Importar bibliotecas
from flask import Flask, render_template, request, redirect, url_for  # Importar módulos de Flask
import mysql.connector  # Importar el conector MySQL
import xlrd  # Importar para procesar archivos de Excel

from models.db_connection import get_db_connection  # Importar la función de conexión a la base de datos
from controllers.regresion_lineal import realizar_regresion_lineal  # Importar función de regresión lineal
from controllers.regresion_lineal import model, scaler  # Importar el modelo de regresión lineal y el escalador
from controllers.analizar_correlacion import analizar_correlacion  # Importar función para analizar correlación

# Crear una instancia de la aplicación Flask
app = Flask(__name__, template_folder='views')
app.debug = False  # Desactivar el modo de depuración de la aplicación

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
 
  
# Función que se encarga de cargar y actualizar las variables globales antes de procesar cualquier solicitud
@app.before_request
def load_values():
    global tables, selected_table, columns, records  # Declarar las variables globales que se actualizarán

    # Intentar conectarse a la base de datos
    db = connect_to_db()  # Llamar a la función para conectar a la base de datos
    if db is not None:  # Si la conexión a la base de datos es exitosa
        cursor = db.cursor()  # Crear un cursor para ejecutar consultas SQL
        cursor.execute("SHOW TABLES")  # Consulta SQL para obtener la lista de tablas en la base de datos
        tables = [table[0] for table in cursor]  # Obtener la lista de nombres de tablas desde el cursor y actualizar la variable global 'tables'
        if selected_table:  # Si se ha seleccionado una tabla
            cursor.execute(f"SHOW COLUMNS FROM {selected_table}")  # Consulta SQL para obtener las columnas de la tabla seleccionada
            columns = [col[0] for col in cursor.fetchall()]  # Obtener la lista de nombres de columnas desde el cursor y actualizar la variable global 'columns'
            cursor.execute(f"SELECT * FROM {selected_table}")  # Consulta SQL para obtener todos los registros de la tabla seleccionada
            records = cursor.fetchall()  # Obtener los registros desde el cursor y actualizar la variable global 'records'
        db.close()  # Cerrar la conexión a la base de datos para liberar recursos


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

# Ruta para editar un registro específico
@app.route('/editar/<table_name>/<int:record_id>', methods=['GET', 'POST'])
def editar_registro(table_name, record_id):
    error_message = None
    success_message = None
    columns = []  # Lista de columnas para mostrar en el formulario

    if not columns:
        db = connect_to_db()
        if db is not None:
            cursor = db.cursor()
            cursor.execute(f"SHOW COLUMNS FROM {table_name}")
            columns = [col[0] for col in cursor.fetchall()]
            db.close()

    if request.method == 'POST':
        # Recupera los datos actualizados del formulario
        updated_data = {column: request.form[column] for column in columns}
        db = connect_to_db()
        if db is not None:
            cursor = db.cursor()

            # Verifica si hay columnas para actualizar
            if not columns:
                error_message = "No se pueden actualizar registros sin columnas."
            else:
                # Construye la consulta SQL para actualizar el registro
                update_query = f"UPDATE {table_name} SET " + ", ".join([f"{column} = %s" for column in updated_data.keys()])
                update_query += " WHERE id = %s"  # Asume que hay una columna 'id' para identificar el registro

                # Ejecuta la consulta SQL para actualizar el registro
                try:
                    cursor.execute(update_query, list(updated_data.values()) + [int(record_id)])
                    db.commit()
                    success_message = "Registro actualizado con éxito."
                except mysql.connector.Error as err:
                    db.rollback()
                    error_message = f"No se pudo actualizar el registro: {err}"

            db.close()

    # Obtener los datos del registro que se está editando
    db = connect_to_db()
    if db is not None:
        cursor = db.cursor()
        cursor.execute(f"SELECT * FROM {table_name} WHERE id = %s", (record_id,))
        record = cursor.fetchone()
        db.close()

    return render_template('editar.html', error_message=error_message or "", success_message=success_message or "", columns=columns, record=record, record_id=record_id, table_name=table_name)


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


# Ruta para eliminar un registro específico
@app.route('/eliminar/<table_name>/<int:record_id>', methods=['GET', 'POST'])
def eliminar_registro(table_name, record_id):
    error_message = None  # Inicializa una variable para mensajes de error
    success_message = None  # Inicializa una variable para mensajes de éxito

    if request.method == 'POST':
        db = connect_to_db()  # Conecta a la base de datos
        if db is not None:
            cursor = db.cursor()  # Crea un cursor para ejecutar consultas SQL

            # Construye la consulta SQL para eliminar el registro
            delete_query = f"DELETE FROM {table_name} WHERE id = %s"  # Asume que hay una columna 'id' para identificar el registro

            try:
                cursor.execute(delete_query, (record_id,))  # Ejecuta la consulta SQL para eliminar el registro
                db.commit()  # Confirma los cambios en la base de datos
                success_message = "Registro eliminado con éxito."
            except mysql.connector.Error as err:
                db.rollback()  # En caso de error, deshace la transacción
                error_message = f"No se pudo eliminar el registro: {err}"
            
            db.close()  # Cierra la conexión a la base de datos

    # Obtener los datos del registro que se está eliminando
    db = connect_to_db()  # Conecta a la base de datos nuevamente
    if db is not None:
        cursor = db.cursor()  # Crea un cursor para ejecutar consultas SQL

        # Construye una consulta SQL para obtener los datos del registro específico
        cursor.execute(f"SELECT * FROM {table_name} WHERE id = %s", (record_id,))
        record = cursor.fetchone()  # Obtiene el registro
        db.close()  # Cierra la conexión a la base de datos

    return render_template('eliminar.html', error_message=error_message or "", success_message=success_message or "", record=record, table_name=table_name)


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


# Ruta para la página de regresión lineal
@app.route('/regresion-lineal', methods=['GET', 'POST'])
def regresion_lineal():
    selected_table = request.args.get('table')  # Obtiene el nombre de la tabla desde la URL
    x_variable = request.args.get('x_variable')  # Obtiene la variable X desde la URL
    y_variable = request.args.get('y_variable')  # Obtiene la variable Y desde la URL
    success_message = None
    error_message = None
    prediction = None  # Inicializa la variable de predicción

    if request.method == 'POST':  # Si se envía un formulario mediante el método POST
        try:
            # Obtener el valor de entrada de X desde el formulario
            input_x = float(request.form['x_variable'])  # Obtiene el valor de X ingresado en el formulario como un número de punto flotante
            
            # Inicializa la variable de predicción
            prediction = None
            
            # Llamar a la función de regresión lineal con el valor de entrada
            success_message, error_message, prediction = realizar_regresion_lineal(selected_table, x_variable, y_variable, input_x)
        except ValueError:
            error_message = "Ingresa un valor válido para X."  # Maneja errores si el valor ingresado para X no es válido (por ejemplo, no es un número)

    return render_template('regresion.html', success_message=success_message, error_message=error_message, prediction=prediction)

#ruta para realizar la regresión lineal, que se activa cuando se envía un formulario mediante el método POST.
@app.route('/realizar-regresion-lineal', methods=['POST'])
def realizar_regresion_lineal_route():
    error_message = None
    success_message = ""  # Define success_message como una cadena vacía al principio
    selected_table = request.form.get('table')  # Obtiene el nombre de la tabla desde el formulario
    x_variable = request.form.get('x_variable')  # Obtiene la variable X desde el formulario
    y_variable = request.form.get('y_variable')  # Obtiene la variable Y desde el formulario

    try:
        print(f"Realizando regresión lineal para {selected_table} con variables X: {x_variable}, Y: {y_variable}")
        
        # Llama a la función para realizar la regresión lineal con los parámetros especificados
        success_message, error_message = realizar_regresion_lineal(selected_table, x_variable, y_variable)
        
        print(f"Mensaje de éxito: {success_message}")
        print(f"Mensaje de error: {error_message}")
    except Exception as e:
        error_message = f"Error en la regresión lineal: {str(e)}"

    return redirect(url_for('resultado_regresion'))


# Ruta para ingresar nuevos datos y realizar predicciones
@app.route('/realizar-prediccion', methods=['POST'])
def realizar_prediccion():
    prediction = None  # Inicializa la variable de predicción

    if request.method == 'POST':
        x_variable = float(request.form.get('x_variable'))  # Obtiene el valor de X del formulario
        
        # Verifica si la función realizar_regresion_lineal ha sido llamada previamente para configurar el scaler
        if scaler is None:
            return "Debes realizar la regresión lineal primero para configurar el scaler."
        
        x_variable_std = scaler.transform([[x_variable]])  # Estandariza el valor de X

        # Realiza la predicción con el modelo
        y_pred = model.predict(x_variable_std)
        y_pred = scaler.inverse_transform(y_pred)  # Desescala la predicción

        # Asigna la predicción a la variable de resultado
        prediction = f"Predicción para X={x_variable}: Y={y_pred[0, 0]:.2f}"

    return render_template('regresion.html', prediction=prediction)


# Ruta para mostrar los resultados de la regresión
@app.route('/resultado-regresion', methods=['GET'])
def resultado_regresion():
    return render_template('regresion.html', success_message=success_message, error_message=None)


# Iniciar la aplicación si este archivo se ejecuta directamente
if __name__ == '__main__':
    app.run(debug=True)