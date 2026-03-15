import pandas as pd
from datetime import datetime
import time
import msvcrt
import os

ARCHIVO_CSV = 'datos_eneun.csv'

print("Iniciando sistema de control de acceso...")

try:
    df = pd.read_csv(ARCHIVO_CSV)
    df['uuid'] = df['uuid'].astype(str).str.strip()
    
    if 'Asistencia' not in df.columns:
        df['Asistencia'] = 'No'
    if 'Hora_Ingreso' not in df.columns:
        df['Hora_Ingreso'] = ''
        
    print(f"Base de datos cargada: {len(df)} registros.")
except Exception as e:
    print(f"Error al cargar el archivo: {e}")
    exit()

print("-" * 50)
print("Sistema activo. Esperando lectura del escaner.")
print("Escriba 'SALIR' para apagar el sistema.")
print("-" * 50)

while True:
    print("\nIngrese codigo: ", end="", flush=True)
    
    caracteres = []
    
    primer_tecla = msvcrt.getch()
    inicio = time.time()
    
    if primer_tecla == b'\r':
        continue
    caracteres.append(primer_tecla.decode('utf-8', errors='ignore'))
    
    while True:
        tecla = msvcrt.getch()
        if tecla == b'\r':
            break
        caracteres.append(tecla.decode('utf-8', errors='ignore'))
        
    tiempo_total = time.time() - inicio
    codigo_escaneado = "".join(caracteres).strip()
    
    if codigo_escaneado.upper() == 'SALIR':
        print("\nGuardando datos y cerrando...")
        df.to_csv(ARCHIVO_CSV, index=False)
        break

    print(codigo_escaneado) 

    if tiempo_total > 0.5:
        print("no puede pasar señor agente")
        continue

    filtro = df['uuid'] == codigo_escaneado

    if filtro.any():
        indice = df.index[filtro].tolist()[0]
        nombre = f"{df.at[indice, 'first_name']} {df.at[indice, 'last_name']}"
        sede = df.at[indice, 'SEDE']
        
        if str(df.at[indice, 'Asistencia']).strip().lower() in ['sí', 'si', 'yes']:
            print(f"Denegado: {nombre} ya habia registrado su ingreso previamente.")
        else:
            hora_actual = datetime.now().strftime("%H:%M:%S")
            df.at[indice, 'Asistencia'] = 'Sí'
            df.at[indice, 'Hora_Ingreso'] = hora_actual
            
            print(f"Acceso aprobado: {nombre} (Sede: {sede})")
            
            df.to_csv(ARCHIVO_CSV, index=False)
    else:
        print("no puede pasar señor agente")

print("Sistema finalizado.")