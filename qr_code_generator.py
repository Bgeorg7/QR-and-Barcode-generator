import pandas as pd
import qrcode
import os

print("Iniciando logistica de Codigos QR...")

ARCHIVO_CSV = 'datos_eneun.csv'
CARPETA_BASE = 'escarapela_estudiantes_qr'

try:
    df = pd.read_csv(ARCHIVO_CSV)
    print(f"Base de datos cargada. Procesando {len(df)} estudiantes...")
except Exception as e:
    print(f"Error al leer el CSV: {e}")
    exit()

print("Generando Codigos QR optimizados...")

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
        

        nombre_archivo = f"{nombre_limpio}_{sede}_{carrera_limpia}.png"
        ruta_guardado = os.path.join(ruta_sede, nombre_archivo)
        
        qr = qrcode.make(uuid_estudiante)
        qr.save(ruta_guardado)
        
    except KeyError as e:
        print(f"ERROR CRITICO: No existe la columna {e}. Revisa el CSV.")
        break
    except Exception as e:
        print(f"Error al procesar a {nombre_completo}: {e}")

print(f"Codigos QR generados y organizados en '{CARPETA_BASE}'.")