import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import os

print("Iniciando Generador ")

ARCHIVO_BASE_DATOS = 'base_completa.xlsx'
RUTA_PLANTILLA = 'diploma_template.png' 
RUTA_FUENTE_DIPLOMA = 'LT Diploma.otf'
CARPETA_SALIDA = 'diplomas_Finales'
MODO_PRUEBA = False

config_diseno = {
    'fuentes': {
        'tamano_nombre': 70,
        'tamano_id': 50,
        'color': 'black'
    },
    'coordenadas': {
        'nombre': (1000, 550),
        'id': (1280, 660),
    }
}

os.makedirs(CARPETA_SALIDA, exist_ok=True)

try:
    print("Leyendo datos de asistentes...")
    df_att = pd.read_excel(ARCHIVO_BASE_DATOS, sheet_name='attendees')
    df_att.columns = df_att.columns.str.strip()
    print(f"Base de datos cargada. Procesando {len(df_att)} estudiantes...")
except Exception as e:
    print(f"Error al leer el archivo Excel: {e}")
    exit()

try:
    font_nombre = ImageFont.truetype(RUTA_FUENTE_DIPLOMA, config_diseno['fuentes']['tamano_nombre'])
    font_id = ImageFont.truetype(RUTA_FUENTE_DIPLOMA, config_diseno['fuentes']['tamano_id'])
    print("Fuente cargada correctamente.")
except IOError:
    print(f"No se encontró la fuente '{RUTA_FUENTE_DIPLOMA}'. Usando fuente por defecto.")
    font_nombre = ImageFont.load_default()
    font_id = ImageFont.load_default()

estudiantes_procesados = 0

for index, row in df_att.iterrows():
    try:
        nombre = str(row.get('badge_name', '')).strip()
        if not nombre or nombre.lower() == 'nan':
            nombre = str(row.get('legal_name', 'Nombre Desconocido')).strip()
            
        # Extraer ID / Documento
        documento_raw = str(row.get('identification_number', '')).strip()
        documento = documento_raw.replace('.0', '')
        if documento.lower() in ['nan', 'none', '']:
            documento = "Sin ID"
            
        # Extraer Sede (Solo para organizar las carpetas)
        sede_raw = str(row.get('sede', 'General')).strip()
        if sede_raw.lower() in ['nan', 'none', '']:
            sede = 'General'
        else:
            sede = sede_raw.replace("/", "-")

        # 4. Dibujar sobre la plantilla
        if not os.path.exists(RUTA_PLANTILLA):
            print(f"¡ERROR FATAL! No se encuentra la plantilla: {RUTA_PLANTILLA}")
            break

        with Image.open(RUTA_PLANTILLA).convert("RGBA") as base_image:
            draw = ImageDraw.Draw(base_image)
            color = config_diseno['fuentes']['color']
            
            # Dibujar textos (anchor="mm" centra el texto exacto en la coordenada X,Y)
            draw.text(config_diseno['coordenadas']['nombre'], nombre.upper(), font=font_nombre, fill=color, anchor="mm")
            
            # Puedes agregar prefijos como "C.C." o "ID:" si quieres
            texto_id = f"ID: {documento}" 
            draw.text(config_diseno['coordenadas']['id'], texto_id, font=font_id, fill=color, anchor="mm")

            # 5. Guardar el PDF
            ruta_sede = os.path.join(CARPETA_SALIDA, sede)
            os.makedirs(ruta_sede, exist_ok=True)
            
            nombre_limpio = nombre.replace(":", "").replace('"', '').replace("/", "-")
            nombre_archivo = f"Diploma_{nombre_limpio}_{documento}.pdf"
            ruta_guardado_final = os.path.join(ruta_sede, nombre_archivo)
            
            # Convertimos a RGB porque PDF no soporta el canal Alfa (RGBA)
            base_image.convert('RGB').save(ruta_guardado_final, 'PDF', resolution=300)
            
            estudiantes_procesados += 1
            print(f"[{estudiantes_procesados}] Generado diploma para: {nombre}")

        if MODO_PRUEBA and estudiantes_procesados >= 1:
            print("Modo prueba finalizado. Solo se generó 1 diploma.")
            break

    except Exception as e:
        print(f"Error en fila {index} ({nombre}): {e}")

print("--------------------------------------------------")
print(f"PROCESO TERMINADO: {estudiantes_procesados} diplomas generados en la carpeta '{CARPETA_SALIDA}'.")