import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib
import plotly.express as px
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import pearsonr
from models.db_connection import get_db_connection

# Función para analizar la correlación entre las variables de una tabla
def analizar_correlacion(selected_table, selected_columns):
    error_message = None  # Inicializa error_message como None

    try:
        # Conectar a la base de datos
        print("Conexión exitosa a la base de datos MySQL.")
        
        db = get_db_connection()  # conexión a la base de datos desde la función

        if db.is_connected():
            cursor = db.cursor()

            # Obtener los datos de las columnas seleccionadas
            query = f"SELECT {', '.join(selected_columns)} FROM {selected_table}"
            print("Query SQL:", query)  
            cursor.execute(query)  # Ejecutar la consulta SQL
            result = cursor.fetchall()  # Obtener los resultados de la consulta
            
             # Cerrar la conexión a la base de datos
            db.close()

            if result:
                # Crear un DataFrame de pandas con los datos
                data_correlation = pd.DataFrame(result, columns=selected_columns)

                # Calcular la matriz de correlación
                correlation_matrix = data_correlation.corr()
                
                # Obtener la correlación más alta
                highest_corr = 0
                variable1, variable2 = "", ""
                for col1 in selected_columns:
                    for col2 in selected_columns:
                        if col1 != col2:
                            corr, _ = pearsonr(data_correlation[col1], data_correlation[col2])
                            if corr > highest_corr:
                                highest_corr = corr
                                variable1 = col1
                                variable2 = col2

                # Crear el mapa de calor con Plotly Express
                fig = px.imshow(correlation_matrix, labels=dict(x="Variables", y="Variables"),
                                x=selected_columns, y=selected_columns, color_continuous_scale='Viridis',
                                title=f"Mapa de Calor de Correlación ({selected_table})",
                                zmin=-1, zmax=1, width=600, height=600)  # Ajusta zmin y zmax según tus necesidades

                # Añadir etiquetas de texto a cada celda
                for i in range(len(selected_columns)):
                    for j in range(len(selected_columns)):
                        fig.add_annotation(
                            x=selected_columns[j],
                            y=selected_columns[i],
                            text=f"{correlation_matrix.iloc[i, j]:.2f}",
                            showarrow=False,
                            font=dict(color='white' if -0.5 < correlation_matrix.iloc[i, j] < 0.5 else 'black')
                        )

                # Actualizar el diseño del mapa de calor
                fig.update_layout(
                    xaxis=dict(tickvals=list(range(len(selected_columns))), ticktext=selected_columns),
                    yaxis=dict(tickvals=list(range(len(selected_columns))), ticktext=selected_columns),
                )

                # Guardar el mapa de calor en formato HTML
                fig.write_html("static/image_correlacion/resultado_correlacion.html")
                print("Mapa de calor guardado correctamente en 'static/image_correlacion/resultado_correlacion.html'")

                # mensaje para mostrar las dos variables con la correlación más alta
                message = f"Las dos variables con la correlación más alta son: <strong style='color: blue;'>{variable1}</strong> y <strong style='color: green;'>{variable2}</strong>. El coeficiente de correlación es <strong>{highest_corr}</strong>."

                # Generar el mapa de calor y el mensaje como diccionario
                result = {
                    "message": message,
                    "heatmap_path": "static/image_correlacion/resultado_correlacion.html"  # Ruta de la imagen del mapa de calor
                }

                # Devolver el resultado como un diccionario
                return result
            else:
                error_message = f"No se encontraron datos en la tabla {selected_table}."
        else:
            error_message = "La conexión a la base de datos no está activa."
    except Exception as e:
        error_message = f"Error inesperado: {e}"

    # Devuelve error_message (puede ser None si no se estableció ningún error)
    return error_message
