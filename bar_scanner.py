import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Control ENEUN", layout="wide")

EVENTOS_COMIDA = ["Almuerzo Viernes", "Cena Viernes", "Almuerzo Sábado", "Cena Sábado"]
EVENTOS_BUSES = ["Abordaje Buses Bogotá - Manizales", "Abordaje Buses Manizales - Bogotá"]

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c4/Escudo_de_la_Universidad_Nacional_de_Colombia.svg/1200px-Escudo_de_la_Universidad_Nacional_de_Colombia.svg.png", width=120)
    st.header("Configuración de Control")
    
    evento_actual = st.selectbox(
        "Seleccione el evento a controlar:",
        [
            "Check-in Llegada a Manizales", 
            "Almuerzo Viernes", 
            "Cena Viernes", 
            "Abordaje Buses Bogotá - Manizales",
            "Entrada Plenaria Sábado",
            "Salida Final"
        ]
    )
    
    lugar_entrada = st.selectbox(
        "Ubicación de escaneo:",
        [
            "Entrada Principal",
            "Puerta Auditorio",
            "Zona Alimentación",
            "Área Baños",
            "Punto Buses",
            "Camping"
        ]
    )
    
    st.divider()
    if st.button("Reiniciar Historial de Sesión"):
        if 'df' in st.session_state:
            del st.session_state['df']
        st.success("Base de datos reiniciada a cero.")
        st.rerun()

if 'df' not in st.session_state:
    try:
        st.session_state.df = pd.read_csv('datos_eneun.csv')
        if 'uuid' in st.session_state.df.columns:
            st.session_state.df['uuid'] = st.session_state.df['uuid'].astype(str)
    except Exception as e:
        st.error(f"Error cargando base de datos: {e}")
        st.stop()

col_estado = f"{evento_actual}_Estado"
col_hora = f"{evento_actual}_Hora"
col_lugar = f"{evento_actual}_Lugar"

if col_estado not in st.session_state.df.columns:
    st.session_state.df[col_estado] = 'No'
if col_hora not in st.session_state.df.columns:
    st.session_state.df[col_hora] = ''
if col_lugar not in st.session_state.df.columns:
    st.session_state.df[col_lugar] = ''

df_local = st.session_state.df

st.title(f"Control de Asistencia: {evento_actual}")
st.write(f"Operando en: **{lugar_entrada}**")

col_izq, col_der = st.columns([2, 1])

with col_izq:
    st.subheader("Entrada de Datos")
    with st.form(key='formulario_escaneo', clear_on_submit=True):
        codigo_escaneado = st.text_input("UUID de Escarapela:")
        boton_registrar = st.form_submit_button(label='Registrar', use_container_width=True)

    if boton_registrar and codigo_escaneado:
        codigo_limpio = codigo_escaneado.strip()
        filtro = df_local['uuid'] == codigo_limpio

        if filtro.any():
            indice = df_local.index[filtro].tolist()[0]
            
            nombre_comp = f"{df_local.at[indice, 'first_name']} {df_local.at[indice, 'last_name']}" if 'first_name' in df_local.columns and 'last_name' in df_local.columns else "Sin Nombre"
            sede_user = df_local.at[indice, 'SEDE'] if 'SEDE' in df_local.columns else "Sin Sede"
            
            alimentacion = df_local.at[indice, 'Tipo_Alimentacion'] if 'Tipo_Alimentacion' in df_local.columns else "No especificado"
            talleres_completos = df_local.at[indice, 'Talleres_Obligatorios'] if 'Talleres_Obligatorios' in df_local.columns else "No especificado"

            if evento_actual in EVENTOS_BUSES and talleres_completos == 'No':
                st.error(f"DENEGADO: {nombre_comp} faltan talleres obligatorios.")
            
            elif evento_actual in EVENTOS_COMIDA and df_local.at[indice, col_estado] == 'Sí':
                st.warning(f"YA REGISTRADO: {nombre_comp} ya recibió {evento_actual} ({alimentacion}) a las {df_local.at[indice, col_hora]}.")
            
            elif df_local.at[indice, col_estado] == 'Sí' and evento_actual not in EVENTOS_COMIDA:
                st.warning(f"YA REGISTRADO: {nombre_comp} ya registró {evento_actual} a las {df_local.at[indice, col_hora]}.")
            
            else:
                hora_actual = datetime.now().strftime("%H:%M:%S")
                st.session_state.df.at[indice, col_estado] = 'Sí'
                st.session_state.df.at[indice, col_hora] = hora_actual
                st.session_state.df.at[indice, col_lugar] = lugar_entrada
                
                st.success("ACCESO APROBADO")
                
                with st.container(border=True):
                    st.markdown(f"**Participante:** {nombre_comp}")
                    st.markdown(f"**Sede:** {sede_user}")
                    st.markdown(f"**Alimentación:** {alimentacion}")
                    st.markdown(f"**Talleres Obligatorios:** {talleres_completos}")
                    st.markdown(f"**Registro:** {hora_actual} en {lugar_entrada}")
                
        else:
            st.error("DENEGADO: Código no encontrado en la base de datos.")

total_registrados = len(df_local)
total_asistentes = len(df_local[df_local[col_estado] == 'Sí'])
porcentaje = (total_asistentes / total_registrados) * 100 if total_registrados > 0 else 0

with col_der:
    st.subheader("Resumen en Tiempo Real")
    st.metric("Inscritos Totales", total_registrados)
    st.metric(f"Registrados", total_asistentes)
    st.progress(porcentaje / 100)
    
    st.divider()
    csv_exportable = df_local.to_csv(index=False).encode('utf-8')
    nombre_archivo = f"reporte_{evento_actual.replace(' ', '_')}.csv"
    st.download_button(
        label="Guardar Datos Actuales (CSV)",
        data=csv_exportable,
        file_name=nombre_archivo,
        mime="text/csv",
        use_container_width=True
    )
