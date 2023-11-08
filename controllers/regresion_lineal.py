# Importación de bibliotecas necesarias
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
import mysql.connector
from models.db_connection import get_db_connection

# Variables globales para el modelo y el escalador
model = None
scaler = None


# Función que realiza la regresión lineal y genera un gráfico
def realizar_regresion_lineal(selected_table, x_variable, y_variable):
    success_message = None
    error_message = None
    beta_0 = None
    beta_1 = None
    r_squared = None
    values_calculated = False

    try:
        # Configura el modelo
        model = LinearRegression()

        # Conexión a la base de datos
        db = get_db_connection()

        if db.is_connected():
            print("Conexión exitosa a la base de datos MySQL.")

            # Realizar una consulta SQL para obtener los datos de la tabla seleccionada
            cursor = db.cursor()
            query = f"SELECT {x_variable}, {y_variable} FROM {selected_table}"
            print("Query SQL:", query)
            cursor.execute(query)
            result = cursor.fetchall()

            db.close()

            if result:
                print("Datos obtenidos de la base de datos:", result)
                data_regression = pd.DataFrame(result, columns=[x_variable, y_variable])

                X = data_regression[x_variable].values.reshape(-1, 1)
                y = data_regression[y_variable].values.reshape(-1, 1)

                # Configura el escalador y ajusta a los datos
                scaler = StandardScaler()
                X_std = scaler.fit_transform(X)
                y_std = scaler.fit_transform(y)

                model.fit(X_std, y_std)

                y_pred = model.predict(X_std)
                y_pred = scaler.inverse_transform(y_pred)

                plt.scatter(X, y, label='Datos reales', color='blue')
                plt.plot(X, y_pred, label='Línea de regresión', color='red')
                plt.xlabel(x_variable)
                plt.ylabel(y_variable)
                plt.legend()
                plt.savefig('static/image_regresion/regresion_plot.png')
                print("Gráfico de regresión guardado correctamente en 'static/image_regresion/regresion_plot.png'")
                success_message = "Regresión lineal completada."
                beta_0 = model.intercept_[0]
                beta_1 = model.coef_[0][0]
                r_squared = calcular_r_squared(X, y, y_pred)
                values_calculated = True
            else:
                error_message = f"No se encontraron datos en la tabla {selected_table}."
        else:
            error_message = "La conexión a la base de datos no está activa"
            
    except ValueError:
        error_message = "Ingresa un valor válido para X."
    except mysql.connector.Error as err:
        error_message = f"Error al conectar a la base de datos: {err}"
    except Exception as e:
        error_message = f"Error inesperado: {e}"

    return success_message, error_message, values_calculated, beta_0, beta_1, r_squared


# Función para calcular r_squared
def calcular_r_squared(X, y, y_pred):
    ssr = np.sum((y - y_pred) ** 2)
    sst = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - (ssr / sst)
    return r_squared


# Función para realizar predicciones
def realizar_prediccion(x_variable):
    if scaler is None or model is None:
        raise ValueError("Debes realizar la regresión lineal primero para configurar el escalador y el modelo.")
    
    x_variable_std = scaler.transform([[x_variable]])
    y_pred = model.predict(x_variable_std)
    y_pred = scaler.inverse_transform(y_pred)
    
    return y_pred
