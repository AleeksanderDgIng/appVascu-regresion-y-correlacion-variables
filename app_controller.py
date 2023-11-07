# Importar bibliotecas 
from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import xlrd
#from controllers.regresion import realizar_regresion_lineal 
from models.db_connection import get_db_connection  # Importa la función de conexión
#from controllers.regresion import analizar_correlacion 

from controllers.analizar_correlacion import analizar_correlacion
from controllers.regresion_lineal import realizar_regresion_lineal

# Crear instancia de la aplicación Flask
app = Flask(__name__, template_folder='views')
app.debug = False

# Definir success_message como cadena vacía al principio
success_message = ""

# Inicializar las variables globales
tables = []  # Almacenará los nombres de las tablas en la base de datos
records = []  # Almacenará los registros de la tabla seleccionada
selected_table = None
columns = []  # Lista de columnas de la tabla seleccionada

 
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
    

# Función para cargar los valores antes de cualquier solicitud
@app.before_request
def load_values():
    global tables, selected_table, columns, records  # Declarar las variables globales

    # Intentar conectarse a la base de datos
    db = connect_to_db()
    if db is not None:
        cursor = db.cursor()
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor]  # Actualizar la variable global 'tables'
        if selected_table:
            cursor.execute(f"SHOW COLUMNS FROM {selected_table}")
            columns = [col[0] for col in cursor.fetchall()]  # Actualizar la variable global 'columns'
            cursor.execute(f"SELECT * FROM {selected_table}")
            records = cursor.fetchall()  # Actualizar la variable global 'records'

        db.close()  # Cerrar la conexión a la base de datos


# Ruta principal ("/") para mostrar la página de inicio
@app.route('/', methods=['GET', 'POST'])
def index():
    global tables, records, selected_table  # Declarar las variables globales

    error_message = None
    success_message = None
    selected_table = None
    columns = []  # Lista de columnas de la tabla seleccionada
    record_to_edit = []

    if request.method == 'POST':
        # Intentar conectarse a la base de datos
        db = connect_to_db()
        if db is not None:
            cursor = db.cursor()
            cursor.execute("SHOW TABLES")
            tables = [table[0] for table in cursor]  # Actualizar la variable global 'tables'
            selected_table = request.form.get('table')
            if selected_table:
                cursor.execute(f"SHOW COLUMNS FROM {selected_table}")
                columns = [col[0] for col in cursor.fetchall()]  # Actualizar la variable global 'columns'
                cursor.execute(f"SELECT * FROM {selected_table}")
                records = cursor.fetchall()  # Actualizar la variable global 'records'

            db.close()  # Cerrar la conexión a la base de datos
            success_message = "Conexión exitosa a la base de datos MySQL."
        else:
            error_message = "No se pudo conectar a la base de datos MySQL. Verifica tus credenciales."

    # Verificar si selected_table tiene un valor válido antes de construir la URL
    if selected_table:
        return render_template('index.html', error_message=error_message or "", success_message=success_message or "", tables=tables, selected_table=selected_table, columns=columns, records=records, record_to_edit=record_to_edit, table_name=selected_table)
    else:
        return render_template('index.html', error_message=error_message or "", success_message=success_message or "", tables=tables, columns=columns, records=records, record_to_edit=record_to_edit)


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
    error_message = None
    success_message = None

    if request.method == 'POST':
        db = connect_to_db()
        if db is not None:
            cursor = db.cursor()

            # Construye la consulta SQL para eliminar el registro
            delete_query = f"DELETE FROM {table_name} WHERE id = %s"  # Asume que hay una columna 'id' para identificar el registro

            try:
                cursor.execute(delete_query, (record_id,))
                db.commit()
                success_message = "Registro eliminado con éxito."
            except mysql.connector.Error as err:
                db.rollback()
                error_message = f"No se pudo eliminar el registro: {err}"
            
            db.close()

    # Obtener los datos del registro que se está eliminando
    db = connect_to_db()
    if db is not None:
        cursor = db.cursor()
        cursor.execute(f"SELECT * FROM {table_name} WHERE id = %s", (record_id,))
        record = cursor.fetchone()
        db.close()

    return render_template('eliminar.html', error_message=error_message or "", success_message=success_message or "", record=record, table_name=table_name)


# Ruta para mostrar el mapa de calor de correlación
@app.route('/mostrar-mapa-de-calor/<table_name>', methods=['POST'])
def mostrar_mapa_de_calor(table_name):
    selected_columns = request.form.getlist('selected_columns')

    if len(selected_columns) < 2:
        return "Selecciona al menos dos variables para el análisis de correlación."

    # Llama a la función analizar_correlación del módulo regresión
    result = analizar_correlacion(table_name, selected_columns)

    if "message" in result:
        message = result["message"]
        heatmap_path = result["heatmap_path"]
        return render_template('mapa_de_calor.html', table_name=table_name, selected_columns=selected_columns, message=message, heatmap_path=heatmap_path)
    else:
        return result


# Ruta para seleccionar las variables a analizar de correlacion
@app.route('/seleccionar-variables/<table_name>', methods=['GET', 'POST'])
def seleccionar_variables(table_name):
    error_message = None
    selected_columns = []

    # Obtén la lista de columnas de la tabla seleccionada
    db = connect_to_db()
    if db is not None:
        cursor = db.cursor()
        cursor.execute(f"SHOW COLUMNS FROM {table_name}")
        columns = [col[0] for col in cursor.fetchall()]
        db.close()

    if request.method == 'POST':
        selected_columns = request.form.getlist('variables')

        if len(selected_columns) < 2:
            error_message = "Selecciona al menos dos variables para el análisis de correlación."
        else:
            # Redirige a la página de mapa de calor con las variables seleccionadas
            return redirect(url_for('seleccionar_variables', table_name=table_name))

    return render_template('seleccionar_variables_correlacion.html', error_message=error_message or "", columns=columns, table_name=table_name, selected_columns=selected_columns)


# Ruta para seleccionar variables para la regresión lineal
@app.route('/seleccionar-variables-regresion/<table_name>', methods=['GET', 'POST'])
def seleccionar_variables_regresion(table_name):
    error_message = None
    selected_columns = []

    # Obtén la lista de columnas de la tabla seleccionada
    db = connect_to_db()
    if db is not None:
        cursor = db.cursor()
        cursor.execute(f"SHOW COLUMNS FROM {table_name}")
        columns = [col[0] for col in cursor.fetchall()]
        db.close()

    if request.method == 'POST':
        selected_columns = request.form.getlist('variables')

        if len(selected_columns) != 2:
            error_message = "Selecciona exactamente dos variables, una para X y otra para Y, para el análisis de regresión."
        else:
            # Redirige a la página de realizar la regresión lineal con las variables seleccionadas
            return redirect(url_for('realizar_regresion', table=table_name, x_variable=selected_columns[0], y_variable=selected_columns[1]))

    return render_template('seleccionar_variables_regresion.html', error_message=error_message or "", columns=columns, table_name=table_name, selected_columns=selected_columns)





@app.route('/realizar-regresion-lineal', methods=['POST'])
def realizar_regresion_lineal_route():
    error_message = None
    success_message = ""  # Define success_message como una cadena vacía al principio
    selected_table = request.form.get('table')
    x_variable = request.form.get('x_variable')
    y_variable = request.form.get('y_variable')

    try:
        print(f"Realizando regresión lineal para {selected_table} con variables X: {x_variable}, Y: {y_variable}")
        success_message, error_message = realizar_regresion_lineal(selected_table, x_variable, y_variable)
        print(f"Mensaje de éxito: {success_message}")
        print(f"Mensaje de error: {error_message}")
    except Exception as e:
        error_message = f"Error en la regresión lineal: {str(e)}"

    return redirect(url_for('resultado_regresion'))


# Ruta para la página de regresión lineal
@app.route('/regresion-lineal', methods=['GET'])
def regresion_lineal():
    selected_table = request.args.get('table')
    x_variable = request.args.get('x_variable')
    y_variable = request.args.get('y_variable')
    success_message = None
    error_message = None

    if selected_table:
        try:
            success_message, error_message = realizar_regresion_lineal(selected_table, x_variable, y_variable)
        except Exception as e:
            error_message = f"Error en la regresión lineal: {str(e)}"
    else:
        error_message = "Falta información necesaria para realizar la regresión lineal."

    return render_template('regresion.html', success_message=success_message, error_message=error_message)


# Ruta para la página de regresión lineal
@app.route('/resultado-regresion', methods=['GET'])
def resultado_regresion():
    return render_template('regresion.html', success_message=success_message, error_message=None)


# Iniciar la aplicación si este archivo se ejecuta directamente
if __name__ == '__main__':
    app.run(debug=True)