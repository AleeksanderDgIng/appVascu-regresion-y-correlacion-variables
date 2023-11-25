# controllers/regresion_lineal.py

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import mysql.connector
from models.db_connection import get_db_connection
import plotly.express as px
import statsmodels.api as sm

class RegresionLinealModel:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.x_variable_name = None
        self.y_variable_name = None

    def realizar_regresion_lineal(self, selected_table, x_variable, y_variable):
        success_message = None
        error_message = None
        beta_0 = None
        beta_1 = None
        r_squared = None

        correlation_coefficient = None
        registros = None
        values_calculated = False
        self.x_variable_name = x_variable
        self.y_variable_name = y_variable

        try:
            plt.figure()

            db = get_db_connection()

            if db.is_connected():
                print("Conexión exitosa a la base de datos MySQL.")

                cursor = db.cursor()
                query = f"SELECT {x_variable}, {y_variable} FROM {selected_table}"
                print("Query SQL:", query)
                cursor.execute(query)
                result = cursor.fetchall()

                db.close()

                if result:
                    data_regression = pd.DataFrame(result, columns=[x_variable, y_variable])

                    X = data_regression[x_variable]
                    X = sm.add_constant(X)  
                    y = data_regression[y_variable]

                    self.model = sm.OLS(y, X).fit()

                    # Utilizamos Plotly para el gráfico interactivo
                    fig = px.scatter(data_regression, x=x_variable, y=y_variable, trendline="ols")
                    fig.update_layout(
                        title=f'Regresión Lineal entre {x_variable} y {y_variable}',
                        xaxis_title=x_variable,
                        yaxis_title=y_variable
                    )
                    fig.write_html('static/image_regresion/regresion_plot.html')

                    registros = len(data_regression)

                    success_message = "Regresión lineal completada."
                    beta_0 = self.model.params['const']
                    print("Intercept (beta_0):", beta_0)
                    beta_1 = self.model.params[x_variable]  # Coeficiente de la variable independiente
                    r_squared = self.model.rsquared
                    correlation_coefficient = data_regression.corr().loc[x_variable, y_variable]
                    values_calculated = True

                    # Después de la asignación
                    print(f"Después de la asignación - beta_0: {beta_0}, beta_1: {beta_1}, r_squared: {r_squared}")

                else:
                    error_message = f"No se encontraron datos en la tabla {selected_table}."
                    registros = 0  # Establecer a cero si no hay datos
            else:
                error_message = "La conexión a la base de datos no está activa"

        except ValueError as ve:
            error_message = f"Error al ajustar el modelo de regresión: {ve}"
        except mysql.connector.Error as err:
            error_message = f"Error al conectar a la base de datos: {err}"
        except Exception as e:
            error_message = f"Error inesperado: {e}"

        return (
            success_message, error_message, values_calculated,
            beta_0 if isinstance(beta_0, (float, int)) else None,
            beta_1 if isinstance(beta_1, (float, int)) else None,
            r_squared if isinstance(r_squared, (float, int)) else None,

            correlation_coefficient,
            registros
        )


    def realizar_prediccion(self, x_variable):
        print("Realizando predicción para x_variable:", x_variable)
        if self.model is None or self.x_variable_name is None or self.y_variable_name is None:
            raise ValueError("Debes realizar la regresión lineal primero para configurar el modelo y los nombres de las variables.")

        try:
            print("Valor de x_variable recibido:", x_variable)

            # Formatea x_variable como una matriz 2D
            x_variable_std = np.array([[1, x_variable]])
            print("Forma de x_variable_std:", x_variable_std.shape)
            print("Valores de x_variable_std:", x_variable_std)

            y_pred = self.model.predict(x_variable_std)
            print("Forma de y_pred:", y_pred.shape)
            print("Valores de y_pred:", y_pred)

            # Convierte el resultado a un valor numérico
            prediction_value = float(y_pred[0])

            return {
                'x_variable': self.x_variable_name,
                'y_variable': self.y_variable_name,
                'prediction': prediction_value,
                'error_message': None
            }
        except Exception as e:
            return {
                'x_variable': self.x_variable_name,
                'y_variable': self.y_variable_name,
                'prediction': None,
                'error_message': f"Error al realizar la predicción: {e}"
            }


    def calcular_r_squared(self, X, y, y_pred):
        ssr = np.sum((y - y_pred) ** 2)
        sst = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ssr / sst)
        return r_squared


    def calcular_coeficiente_correlacion(self, X, y):
        correlation_matrix = np.corrcoef(X[:, 0], y[:, 0])
        correlation_coefficient = correlation_matrix[0, 1]
        return correlation_coefficient
