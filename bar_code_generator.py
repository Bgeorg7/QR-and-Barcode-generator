import pandas as pd
import barcode
from barcode.writer import ImageWriter
import os

print("Iniciando logística de Códigos de Barras...")

ARCHIVO_CSV = 'datos_eneun.csv'
CARPETA_BASE = 'Escarapelas_Por_Sede'

try:
    df = pd.read_csv(ARCHIVO_CSV)
    print(f"Base de datos cargada. Procesando {len(df)} estudiantes...")
except Exception as e:
    print(f"Error al leer el CSV: {e}")
    exit()

print("Generando Códigos de Barras...")

for index, fila in df.iterrows():
    try:
        sede = str(fila['SEDE']).strip()
        carrera = str(fila['career']).strip()
        uuid_estudiante = str(fila['uuid']).strip()
        
        nombre_completo = f"{str(fila['first_name']).strip()} {str(fila['last_name']).strip()}"
        
        ruta_sede = os.path.join(CARPETA_BASE, sede)
        os.makedirs(ruta_sede, exist_ok=True)
        
        nombre_limpio = nombre_completo.replace("/", "-").replace(":", "").replace('"', '')
        carrera_limpia = carrera.replace("/", "-")
        
        nombre_archivo = f"{nombre_limpio}_{sede}_{carrera_limpia}"
        ruta_guardado = os.path.join(ruta_sede, nombre_archivo)
        

        opciones_imagen = {
            'module_width': 0.15,  
            'module_height': 10.0, 
            'font_size': 6,        
            'text_distance': 3.0,
        }
        
        codigo_obj = barcode.get('code128', uuid_estudiante, writer=ImageWriter())
        codigo_obj.save(ruta_guardado, options=opciones_imagen)
        
    except KeyError as e:
        print(f"ERROR CRÍTICO: No existe la columna {e}. Revisa el CSV.")
        break
    except Exception as e:
        print(f"Error al procesar a {nombre_completo}: {e}")

print(f"Códigos de barras generados y organizados en '{CARPETA_BASE}'.")