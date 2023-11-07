import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import pearsonr
import mysql.connector
from models.db_connection import get_db_connection

def analizar_correlacion(selected_table, selected_columns):
    error_message = None  # Inicializa error_message como None

    try:
        # Conectar a la base de datos
        print("Conexión exitosa a la base de datos MySQL.")
        
        db = get_db_connection()

        if db.is_connected():
            cursor = db.cursor()

            # Obtener los datos de las columnas seleccionadas
            query = f"SELECT {', '.join(selected_columns)} FROM {selected_table}"
            print("Query SQL:", query)  # Agrega esta línea para verificar la consulta
            cursor.execute(query)
            result = cursor.fetchall()
            
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

                # Generar el mapa de calor con seaborn
                plt.figure(figsize=(7, 5)) # Define el tamaño de la figura
                sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', cbar=True, linewidths=0.5, fmt=".2f", annot_kws={"size": 12})
                plt.title(f"Mapa de Calor de Correlación ({selected_table})", fontsize=18)
                plt.xlabel("Variables", fontsize=11)
                plt.ylabel("Variables", fontsize=11)
                plt.xticks(fontsize=11)
                plt.yticks(fontsize=11)

                # Guardar el mapa de calor en la carpeta "static"
                plt.savefig('static/mapa_de_calor.png')
                print("Mapa de calor guardado correctamente en 'static/mapa_de_calor.png'")


                # Crear un mensaje para mostrar las dos variables con la correlación más alta
                message = f"Las dos variables con la correlación más alta son: {variable1} y {variable2}. El coeficiente de correlación es {highest_corr}."

                # Generar el mapa de calor y el mensaje como diccionario
                result = {
                    "message": message,
                    "heatmap_path": "static/mapa_de_calor.png"  # Ruta de la imagen del mapa de calor
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
