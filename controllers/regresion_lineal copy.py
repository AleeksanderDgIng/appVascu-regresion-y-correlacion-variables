import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import mysql.connector
from models.db_connection import get_db_connection

def realizar_regresion_lineal(selected_table, x_variable, y_variable):
    success_message = None
    error_message = None
    
    try:
        # Conectar a la base de datos
        db = get_db_connection()

        if db.is_connected():
            print("Conexión exitosa a la base de datos MySQL.")
            
            # Realizar una consulta SQL para obtener los datos de la tabla seleccionada
            cursor = db.cursor()
            query = f"SELECT {x_variable}, {y_variable} FROM {selected_table}"
            print("Query SQL:", query)  # Agrega esta línea para verificar la consulta
            cursor.execute(query)
            result = cursor.fetchall()
            
            # Cerrar la conexión a la base de datos
            db.close()

            if result:
                print("Datos obtenidos de la base de datos:", result)  # Agrega esta línea para verificar los datos
                # Crear un DataFrame de pandas con los datos
                data_regression = pd.DataFrame(result, columns=[x_variable, y_variable])

                # Crear un modelo de regresión lineal
                model = LinearRegression()

                # Ajustar el modelo a los datos
                X = data_regression[[x_variable]]
                y = data_regression[y_variable]
                model.fit(X, y)

                # Predecir valores
                y_pred = model.predict(X)

                # Graficar los datos y la línea de regresión
                plt.scatter(X, y, label='Datos reales', color='blue')
                plt.plot(X, y_pred, label='Línea de regresión', color='red')
                plt.xlabel(x_variable)
                plt.ylabel(y_variable)
                plt.legend()
                plt.savefig('static/regresion_plot.png')  # Guardar el gráfico en la carpeta "static"
                print("Gráfico de regresión guardado correctamente en 'static/regresion_plot.png'")
                success_message = "Regresión lineal completada."
                
               
            
            else:
                error_message = f"No se encontraron datos en la tabla {selected_table}."
        else:
            error_message = "La conexión a la base de datos no está activa."
    except mysql.connector.Error as err:
        error_message = f"Error al conectar a la base de datos: {err}"
    except Exception as e:
        error_message = f"Error inesperado: {e}"
    
    return success_message, error_message