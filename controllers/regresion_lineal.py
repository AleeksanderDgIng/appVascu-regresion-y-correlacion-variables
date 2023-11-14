import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
import mysql.connector
from models.db_connection import get_db_connection
import plotly.express as px

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
        varianza_residual = None
        correlation_coefficient = None
        registros = None
        values_calculated = False
        self.x_variable_name = x_variable
        self.y_variable_name = y_variable

        try:
            plt.figure()

            self.model = LinearRegression()

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
                    print("Datos obtenidos de la base de datos:", result)
                    data_regression = pd.DataFrame(result, columns=[x_variable, y_variable])

                    X = data_regression[x_variable].values.reshape(-1, 1)
                    y = data_regression[y_variable].values.reshape(-1, 1)

                    self.scaler = StandardScaler()
                    X_std = self.scaler.fit_transform(X)
                    y_std = self.scaler.fit_transform(y)

                    self.model.fit(X_std, y_std)

                    y_pred = self.model.predict(X_std)
                    y_pred = self.scaler.inverse_transform(y_pred)

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
                    beta_0 = self.model.intercept_[0]
                    beta_1 = self.model.coef_[0][0]
                    r_squared = self.calcular_r_squared(X, y, y_pred)
                    varianza_residual = self.calcular_varianza_residual(y, y_pred)
                    correlation_coefficient = self.calcular_coeficiente_correlacion(X, y)
                    values_calculated = True
                else:
                    error_message = f"No se encontraron datos en la tabla {selected_table}."
                    registros = 0  # Establecer a cero si no hay datos
            else:
                error_message = "La conexión a la base de datos no está activa"

        except ValueError:
            error_message = "Ingresa un valor válido para X."
        except mysql.connector.Error as err:
            error_message = f"Error al conectar a la base de datos: {err}"
        except Exception as e:
            error_message = f"Error inesperado: {e}"

        return (
            success_message, error_message, values_calculated,
    beta_0, beta_1 if isinstance(beta_1, (float, int)) else None,
    r_squared if isinstance(r_squared, (float, int)) else None,
    varianza_residual, correlation_coefficient, registros
        )

    def calcular_r_squared(self, X, y, y_pred):
        ssr = np.sum((y - y_pred) ** 2)
        sst = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ssr / sst)
        return r_squared

    def calcular_varianza_residual(self, y, y_pred):
        residuals = y - y_pred
        varianza_residual = np.var(residuals)
        return varianza_residual

    def calcular_coeficiente_correlacion(self, X, y):
        correlation_matrix = np.corrcoef(X[:, 0], y[:, 0])
        correlation_coefficient = correlation_matrix[0, 1]
        return correlation_coefficient

    def realizar_prediccion(self, x_variable):
        if self.scaler is None or self.model is None or self.x_variable_name is None or self.y_variable_name is None:
            raise ValueError("Debes realizar la regresión lineal primero para configurar el escalador, el modelo y los nombres de las variables.")

        try:
            x_variable_std = self.scaler.transform([[x_variable]])

            y_pred = self.model.predict(x_variable_std)
            y_pred = self.scaler.inverse_transform(y_pred)

            return {
                'x_variable': self.x_variable_name,
                'y_variable': self.y_variable_name,
                'prediction': y_pred[0, 0],
                'error_message': None
            }
        except Exception as e:
            return {
                'x_variable': self.x_variable_name,
                'y_variable': self.y_variable_name,
                'prediction': None,
                'error_message': f"Error al realizar la predicción: {e}"
            }
