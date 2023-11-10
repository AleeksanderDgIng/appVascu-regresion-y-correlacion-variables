# controllers/regresion_lineal.py

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler #libreria  permite hacer el escalamiento de dtos para que los valores se ajusten mejor cuandohay valores atipicos
from sklearn.linear_model import LinearRegression #libreria modelo de regresion
import mysql.connector
from models.db_connection import get_db_connection

class RegresionLinealModel:
    def __init__(self):
        self.model = None
        self.scaler = None

    def realizar_regresion_lineal(self, selected_table, x_variable, y_variable):
        success_message = None
        error_message = None
        beta_0 = None
        beta_1 = None
        r_squared = None
        values_calculated = False

        try:
            plt.figure()  # Crea una nueva figura

            # Configura el modelo
            self.model = LinearRegression()

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
                    y = data_regression[y_variable].values.reshape(-1, 1) #variable predictoria

                    # Configura el escalador y ajusta a los datos
                    self.scaler = StandardScaler()
                    X_std = self.scaler.fit_transform(X)
                    y_std = self.scaler.fit_transform(y)

                    self.model.fit(X_std, y_std)

                    y_pred = self.model.predict(X_std)
                    y_pred = self.scaler.inverse_transform(y_pred)

                    plt.scatter(X, y, label='Datos reales', color='blue')
                    plt.plot(X, y_pred, label='Línea de regresión', color='red')
                    plt.xlabel(x_variable)
                    plt.ylabel(y_variable)
                    plt.legend()
                    plt.savefig('static/image_regresion/regresion_plot.png')
                    plt.clf()  # Limpia la figura actual
                    print("Gráfico de regresión guardado correctamente en 'static/image_regresion/regresion_plot.png'")
                    success_message = "Regresión lineal completada."
                    beta_0 = self.model.intercept_[0]
                    beta_1 = self.model.coef_[0][0]
                    r_squared = self.calcular_r_squared(X, y, y_pred)
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

    def calcular_r_squared(self, X, y, y_pred):
        ssr = np.sum((y - y_pred) ** 2)
        sst = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ssr / sst)
        return r_squared

    def realizar_prediccion(self, x_variable):
        if self.scaler is None or self.model is None:
            raise ValueError("Debes realizar la regresión lineal primero para configurar el escalador y el modelo.")

        try:
            x_variable_std = self.scaler.transform([[x_variable]])  # Estandariza el valor de X

            # Realiza la predicción con el modelo
            y_pred = self.model.predict(x_variable_std)
            y_pred = self.scaler.inverse_transform(y_pred)  # Desescala la predicción

            return y_pred, None  # Devuelve el valor de predicción y sin mensaje de error
        except Exception as e:
            return None, f"Error al realizar la predicción: {e}"
