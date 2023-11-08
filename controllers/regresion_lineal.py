# Importación de bibliotecas necesarias
import pandas as pd  # Biblioteca para el análisis de datos
import numpy as np  # Biblioteca para cálculos numéricos
import matplotlib  # Biblioteca para generar gráficos
matplotlib.use('Agg')  # Configuración de Matplotlib para trabajar sin una interfaz gráfica
import matplotlib.pyplot as plt  # Módulo de Matplotlib para crear gráficos
from sklearn.preprocessing import StandardScaler  # Para estandarizar los datos
from sklearn.linear_model import LinearRegression  # Modelo de regresión lineal de Scikit-Learn
import mysql.connector  # Conector para la base de datos MySQL
from models.db_connection import get_db_connection  # Importación de la función para obtener una conexión a la base de datos MySQL

# Variables globales para el modelo y el escalador
model = None  # Inicializa la variable global del modelo de regresión lineal
scaler = None  # Inicializa la variable global del escalador (StandardScaler)

# Función que realiza la regresión lineal
def realizar_regresion_lineal(selected_table, x_variable, y_variable):
    success_message = None  # Inicializa el mensaje de éxito como None
    error_message = None  # Inicializa el mensaje de error como None

    try:
        # Conexión a la base de datos
        db = get_db_connection()  # Obtiene una conexión a la base de datos utilizando una función externa

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
                # Crear un DataFrame de Pandas con los datos
                data_regression = pd.DataFrame(result, columns=[x_variable, y_variable])

                # Separar las variables X e Y
                X = data_regression[x_variable].values.reshape(-1, 1)
                y = data_regression[y_variable].values.reshape(-1, 1)

                # Estandarizar los valores de X e Y
                global scaler
                scaler = StandardScaler()  # Inicializa el escalador
                X_std = scaler.fit_transform(X)  # Estandariza los valores de X
                y_std = scaler.fit_transform(y)  # Estandariza los valores de Y

                # Crear un modelo de regresión lineal
                global model
                model = LinearRegression()  # Inicializa el modelo de regresión lineal

                # Ajustar el modelo a los datos
                model.fit(X_std, y_std)  # Realiza el ajuste de regresión con los datos estandarizados

                # Predecir valores
                y_pred = model.predict(X_std)  # Realiza predicciones con el modelo

                # Desescalar los valores de las predicciones
                y_pred = scaler.inverse_transform(y_pred)  # Desescala las predicciones

                # Graficar los datos y la línea de regresión
                plt.scatter(X, y, label='Datos reales', color='blue')
                plt.plot(X, y_pred, label='Línea de regresión', color='red')
                plt.xlabel(x_variable)
                plt.ylabel(y_variable)
                plt.legend()
                plt.savefig('static/image_regresion/regresion_plot.png')  # Guardar el gráfico en la carpeta "static"
                print("Gráfico de regresión guardado correctamente en 'static/image_regresion/regresion_plot.png'")
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
