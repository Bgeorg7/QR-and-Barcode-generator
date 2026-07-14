import pandas as pd
import barcode
from barcode.writer import ImageWriter
import qrcode
from PIL import Image, ImageDraw, ImageFont
import os

print("Iniciando Automatización Total de Escarapelas + QR de Emergencia...")

ARCHIVO_BASE_DATOS = 'base_completa.xlsx'
RUTA_LOGO = 'logo.jpg'
CARPETA_SALIDA = 'Escarapelas_Finales'
ARCHIVO_ADMINS = 'no_needed_escarapela.txt'
MODO_PRUEBA = False

MAPEO_TEMPLATES = {
    'Bogotá': 'template_bogota.png',
    'Bogota': 'template_bogota.png',
    'Medellín': 'template_medellin.png',
    'Medellin': 'template_medellin.png',
    'Manizales': 'template_manizales.png',
    'Amazonia': 'template_amazonia.png',
    'Amazonía': 'template_amazonia.png',
    'Tumaco': 'template_tumaco.png',
    'Caribe': 'template_caribe.png',
    'La Paz': 'template_la_paz.png',
    'Orinoquía': 'template_orinoquia.png',
    'Orinoquia': 'template_orinoquia.png',
    'Palmira': 'template_palmira.png'
}

RUTA_FUENTE_NOMBRE = 'Motter Corpus Std Condensed.otf'
RUTA_FUENTE_PRONOMBRE = 'ITC Souvenir Std Bold.otf'
RUTA_FUENTE_CORREO = 'ITC Souvenir Std Light Italic.otf'

config_diseno = {
    'fuentes': {
        'tamano_nombre': 70,
        'tamano_pronombre': 50,
        'tamano_rh': 50,
        'tamano_eps': 50,
        'tamano_campamento': 80,
        'tamano_correo': 20,
        'color': 'black'
    },
    'coordenadas': {
        'nombre': (1000, 550),
        'pronombre': (1020, 660),
        'rh': (1280, 660),
        'codigo_barras': (715, 990),
        'eps': (900, 1450),
        'qr': (1100, 1300),
        'campamento': (1000, 1700),
        'correo': (750, 1980)
    },
    'barcode': {
        'max_ancho_px': 700,
        'alto_px': 200
    },
    'qr': {
        'tamano_px': 208
    }
}

def limpiar(valor):
    texto = str(valor).strip()
    if texto.lower() in ['nan', 'na', 'none', 'null', '', '<na>']:
        return "No Aplica"
    return texto

diccionario_enfermedades = {
    "PERMANENT_MEDICATION": "Med. permanente",
    "ALLERGIES": "Alergias",
    "NON_NEUROTYPICAL": "No neurotípico",
    "OTHER": "Otro",
    "DIABETES": "Diabetes",
    "PREFER_NOT_TO_ANSWER": "Omitido",
    "ASTHMA": "Asma",
    "PSYCHOSOCIAL_DISABILITY": "Disc. psicosocial",
    "CARDIAC": "Cardíaco",
    "HYPERTENSION": "Hipertensión",
    "VISUAL_DISABILITY": "Disc. visual",
    "HEARING_DISABILITY": "Disc. auditiva"
}

def traducir_enfermedades(valor):
    texto = limpiar(valor)
    if texto == "No Aplica":
        return texto
    texto = texto.replace('{', '').replace('}', '')
    for eng, esp in diccionario_enfermedades.items():
        texto = texto.replace(eng, esp)
    return texto.replace('"', '').replace(',', ', ')

nombres_admins = set()
if os.path.exists(ARCHIVO_ADMINS):
    try:
        with open(ARCHIVO_ADMINS, 'r', encoding='utf-8') as f:
            nombres_admins = {line.strip().lower() for line in f if line.strip()}
        print(f"Lista de admins cargada. Se ignorarán {len(nombres_admins)} personas.")
    except Exception as e:
        print(f"Error al leer el archivo de admins: {e}")

try:
    print("Cruzando datos de asistentes y registros...")
    df_att = pd.read_excel(ARCHIVO_BASE_DATOS, sheet_name='attendees')
    df_reg = pd.read_excel(ARCHIVO_BASE_DATOS, sheet_name='registations')
    
    df_att.columns = df_att.columns.str.strip()
    df_reg.columns = df_reg.columns.str.strip()
    
    df_att['llave_doc'] = df_att['identification_number'].astype(str).str.replace('.0', '', regex=False).str.strip()
    df_reg['llave_doc'] = df_reg['document_number'].astype(str).str.replace('.0', '', regex=False).str.strip()
    
    df_reg = df_reg.drop_duplicates(subset='llave_doc', keep='first')
    
    df_cruzado = pd.merge(df_att, df_reg, on='llave_doc', how='left')
    df_cruzado = df_cruzado.fillna('')
    print(f"Base de datos cruzada. Procesando {len(df_cruzado)} estudiantes...")
except Exception as e:
    print(f"Error al leer o cruzar el archivo Excel: {e}")
    exit()

try:
    font_nombre = ImageFont.truetype(RUTA_FUENTE_NOMBRE, config_diseno['fuentes']['tamano_nombre'])
    font_pronombre = ImageFont.truetype(RUTA_FUENTE_PRONOMBRE, config_diseno['fuentes']['tamano_pronombre'])
    font_rh = ImageFont.truetype(RUTA_FUENTE_PRONOMBRE, config_diseno['fuentes']['tamano_rh'])
    font_eps = ImageFont.truetype(RUTA_FUENTE_PRONOMBRE, config_diseno['fuentes']['tamano_eps'])
    font_campamento = ImageFont.truetype(RUTA_FUENTE_PRONOMBRE, config_diseno['fuentes']['tamano_campamento'])
    font_correo = ImageFont.truetype(RUTA_FUENTE_CORREO, config_diseno['fuentes']['tamano_correo'])
except IOError:
    print("No se encontraron los archivos de fuentes.")
    font_nombre = ImageFont.load_default()
    font_pronombre = ImageFont.load_default()
    font_rh = ImageFont.load_default()
    font_eps = ImageFont.load_default()
    font_campamento = ImageFont.load_default()
    font_correo = ImageFont.load_default()

estudiantes_procesados = 0

for index, row in df_cruzado.iterrows():
    try:
        nombre = str(row.get('badge_name', '')).strip()
        if not nombre:
            nombre = str(row.get('legal_name', 'Nombre Desconocido')).strip()
            
        if nombre.lower() in nombres_admins:
            print(f"Omitiendo administrador: {nombre}")
            continue
            
        sede_raw = str(row.get('sede', 'Bogotá')).strip()
        if sede_raw.lower() in ['nan', 'none', '']:
            sede = 'Bogotá'
        else:
            sede = sede_raw
            
        email_val = row.get('email_x') if 'email_x' in row else row.get('email')
        mail = limpiar(email_val).replace(" ", "")
        if mail == "No Aplica":
            mail = f"sin_correo_{index + 1}"
        
        pronombre = str(row.get('pronoun', '')).strip()
        texto_pronombre = f"{pronombre}".strip().upper()
        
        rh = str(row.get('blood_type_id', '')).strip()
        texto_rh = f"{rh}".strip()

        eps = limpiar(row.get('eps_id'))
        texto_eps = f"{eps}".strip() if eps != "No Aplica" else ""
        
        alojamiento = str(row.get('lodging_choice', '')).strip()

        correo = limpiar(email_val)
        texto_correo = correo if correo != "No Aplica" else ""

        documento = limpiar(row.get('identification_number'))
        alergias = limpiar(row.get('allergies'))
        condicion = limpiar(row.get('disability_specify'))
        enfermedades = traducir_enfermedades(row.get('health_condition_codes'))
        contacto_nom = limpiar(row.get('emergency_contact_name'))
        contacto_num = limpiar(row.get('emergency_contact_phone'))

        ruta_plantilla = MAPEO_TEMPLATES.get(sede)
        if not ruta_plantilla or not os.path.exists(ruta_plantilla):
            print(f"No se encuentra la plantilla para la sede: {sede}. Usando Bogotá por defecto.")
            ruta_plantilla = MAPEO_TEMPLATES['Bogotá']

        barcode_writer = ImageWriter()
        opciones_imagen_barras = {
            'module_width': 0.2,
            'module_height': 15.0,
            'write_text': False,
            'quiet_zone': 2.0
        }

        codigo_obj = barcode.get('code128', mail, writer=barcode_writer)
        barcode_image_raw = codigo_obj.render(opciones_imagen_barras)
        barcode_final = barcode_image_raw.resize(
            (config_diseno['barcode']['max_ancho_px'], config_diseno['barcode']['alto_px']),
            Image.Resampling.LANCZOS
        )

        lineas_qr = [f"EMERGENCIA\n{nombre}\nCC:{documento} RH:{texto_rh}"]
        if eps != "No Aplica":
            lineas_qr.append(f"EPS:{eps}")
        if alergias != "No Aplica":
            lineas_qr.append(f"Alergia:{alergias}")
        if enfermedades != "No Aplica":
            lineas_qr.append(f"Enf:{enfermedades}")
        if condicion != "No Aplica":
            lineas_qr.append(f"Cond:{condicion}")
        lineas_qr.append(f"Tel:{contacto_nom} {contacto_num}")

        texto_qr = "\n".join(lineas_qr)

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=2
        )

        qr.add_data(texto_qr)
        qr.make(fit=True)

        img_qr = qr.make_image(fill_color="black", back_color="white").convert('RGB')
        tamano_qr = config_diseno['qr']['tamano_px']
        img_qr = img_qr.resize((tamano_qr, tamano_qr), Image.Resampling.LANCZOS)

        if os.path.exists(RUTA_LOGO):
            try:
                logo = Image.open(RUTA_LOGO).convert('RGB')
                s = int(tamano_qr * 0.18)
                logo = logo.resize((s, s), Image.Resampling.LANCZOS)
                img_qr.paste(logo, ((tamano_qr - s) // 2, (tamano_qr - s) // 2))
            except:
                pass

        with Image.open(ruta_plantilla).convert("RGBA") as base_image:
            draw = ImageDraw.Draw(base_image)
            color = config_diseno['fuentes']['color']
            
            draw.text(config_diseno['coordenadas']['nombre'], nombre.upper(), font=font_nombre, fill=color, anchor="mm")
            draw.text(config_diseno['coordenadas']['pronombre'], texto_pronombre, font=font_pronombre, fill=color, anchor="mm")
            draw.text(config_diseno['coordenadas']['rh'], texto_rh, font=font_rh, fill=color, anchor="mm")
            draw.text(config_diseno['coordenadas']['eps'], texto_eps, font=font_eps, fill=color, anchor="mm")
            draw.text(config_diseno['coordenadas']['correo'], texto_correo, font=font_correo, fill=color, anchor="mm")
            
            if alojamiento == "Planea Acampar":
                draw.text(config_diseno['coordenadas']['campamento'], "CAMPAMENTO", font=font_campamento, fill=color, anchor="mm")
            
            base_image.paste(barcode_final, config_diseno['coordenadas']['codigo_barras'])
            base_image.paste(img_qr, config_diseno['coordenadas']['qr'])

            ruta_sede = os.path.join(CARPETA_SALIDA, sede.replace("/", "-"))
            os.makedirs(ruta_sede, exist_ok=True)
            
            nombre_limpio = nombre.replace(":", "").replace('"', '').replace("/", "-")
            nombre_archivo = f"{nombre_limpio}_{documento}_{sede}.pdf"
            ruta_guardado_final = os.path.join(ruta_sede, nombre_archivo)
            
            base_image.convert('RGB').save(ruta_guardado_final, 'PDF', resolution=300)
            
            estudiantes_procesados += 1
            print(f"Generada escarapela para: {nombre}")

        if MODO_PRUEBA:
            break

    except Exception as e:
        print(f"Error en fila {index} ({nombre}): {e}")

if not MODO_PRUEBA:
    print(f"{estudiantes_procesados} escarapelas generadas en '{CARPETA_SALIDA}'.")