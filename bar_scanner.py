import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Control ENEUN", layout="wide")

with st.sidebar:
    st.header("Configuración de Control")
    
    categoria_control = st.selectbox(
        "Tipo de Control:",
        [
            "Ingreso al ENEUN (Check-in)", 
            "Buses", 
            "Alimentación Principal", 
            "Refrigerios", 
            "Asistencia a Lugares"
        ]
    )
    
    if categoria_control == "Ingreso al ENEUN (Check-in)":
        evento_actual = st.selectbox("Punto de Ingreso:", ["Llegada Manizales (Validar Requisitos)"])
    elif categoria_control == "Buses":
        evento_actual = st.selectbox("Ruta:", ["Ida: Bogotá -> Manizales", "Regreso: Manizales -> Bogotá"])
    elif categoria_control == "Alimentación Principal":
        evento_actual = st.selectbox("Comida:", ["Almuerzo Viernes", "Cena Viernes", "Almuerzo Sábado", "Cena Sábado", "Almuerzo Domingo"])
    elif categoria_control == "Refrigerios":
        evento_actual = st.selectbox("Refrigerio:", ["Refrigerio Viernes AM", "Refrigerio Viernes PM", "Refrigerio Sábado AM", "Refrigerio Sábado PM"])
    elif categoria_control == "Asistencia a Lugares":
        evento_actual = st.selectbox("Lugar:", ["Baños", "Auditorio Principal", "Zona Camping", "Zona de Alimentación"])

    st.divider()
    if st.button("Reiniciar Historial de Sesión"):
        if 'df' in st.session_state:
            del st.session_state['df']
        st.success("Base de datos reiniciada a cero.")
        st.rerun()

if 'df' not in st.session_state:
    try:
        df_inicial = pd.read_excel('base_completa.xlsx', sheet_name='attendees')
        df_inicial.columns = df_inicial.columns.str.strip()
        
        if 'email' in df_inicial.columns:
            df_inicial['email_limpio'] = df_inicial['email'].astype(str).str.strip().str.lower().str.replace(" ", "")
        elif 'email_x' in df_inicial.columns:
            df_inicial['email_limpio'] = df_inicial['email_x'].astype(str).str.strip().str.lower().str.replace(" ", "")
        else:
            st.error("No se encontro una columna de correo electronico valida en la base de datos.")
            st.stop()
            
        st.session_state.df = df_inicial
    except Exception as e:
        st.error(f"Error cargando base de datos: {e}")
        st.stop()

col_estado = f"{evento_actual}_Estado"
col_hora = f"{evento_actual}_Hora"

if col_estado not in st.session_state.df.columns:
    st.session_state.df[col_estado] = 'No'
if col_hora not in st.session_state.df.columns:
    st.session_state.df[col_hora] = ''

df_local = st.session_state.df

st.title(categoria_control)
st.write(f"Operando control de: **{evento_actual}**")

col_izq, col_der = st.columns([2, 1])

with col_izq:
    st.subheader("Escaner / Entrada Manual")
    with st.form(key='formulario_escaneo', clear_on_submit=True):
        codigo_escaneado = st.text_input("Correo Electronico de Escarapela:")
        boton_registrar = st.form_submit_button(label='Registrar Entrada')

    if boton_registrar and codigo_escaneado:
        correo_limpio = codigo_escaneado.strip().lower().replace(" ", "")
        filtro = df_local['email_limpio'] == correo_limpio

        if filtro.any():
            indice = df_local.index[filtro].tolist()[0]
            
            if 'badge_name' in df_local.columns and pd.notna(df_local.at[indice, 'badge_name']):
                nombre_comp = str(df_local.at[indice, 'badge_name']).strip()
            elif 'legal_name' in df_local.columns:
                nombre_comp = str(df_local.at[indice, 'legal_name']).strip()
            else:
                nombre_comp = "Sin Nombre"
                
            sede_user = df_local.at[indice, 'sede'] if 'sede' in df_local.columns else "Sin Sede"
            alimentacion = df_local.at[indice, 'Tipo_Alimentacion'] if 'Tipo_Alimentacion' in df_local.columns else "No especificado"
            talleres_completos = df_local.at[indice, 'Talleres_Obligatorios'] if 'Talleres_Obligatorios' in df_local.columns else "No especificado"

            estado_actual = df_local.at[indice, col_estado]
            
            if evento_actual in ["Ida: Bogotá -> Manizales", "Llegada Manizales (Validar Requisitos)"] and talleres_completos == 'No':
                st.error(f"DENEGADO: A {nombre_comp} le faltan talleres obligatorios.")
            
            elif categoria_control in ["Alimentación Principal", "Refrigerios"] and estado_actual == 'Sí':
                st.warning(f"YA ENTREGADO: {nombre_comp} ya reclamo esto a las {df_local.at[indice, col_hora]}.\n\nDieta: **{alimentacion}**")
            
            elif categoria_control in ["Ingreso al ENEUN (Check-in)", "Buses"] and estado_actual == 'Sí':
                st.warning(f"REPETIDO: {nombre_comp} ya fue registrado en {evento_actual} a las {df_local.at[indice, col_hora]}.")

            else:
                hora_actual = datetime.now().strftime("%H:%M:%S")
                es_reingreso = (categoria_control == "Asistencia a Lugares" and estado_actual == 'Sí')
                
                st.session_state.df.at[indice, col_estado] = 'Sí'
                st.session_state.df.at[indice, col_hora] = hora_actual
                
                if es_reingreso:
                    st.success("REINGRESO APROBADO")
                else:
                    st.success("ACCESO APROBADO")
                
                with st.container(border=True):
                    st.markdown(f"**Participante:** {nombre_comp}")
                    st.markdown(f"**Sede:** {sede_user}")
                    
                    if categoria_control in ["Alimentación Principal", "Refrigerios"]:
                        st.markdown(f"**Entregar Dieta:** {alimentacion}")
                    
                    st.markdown(f"**Registro:** {hora_actual}")
                
        else:
            st.error("DENEGADO: Correo no encontrado en la base de datos.")

total_registrados = len(df_local)
total_asistentes = len(df_local[df_local[col_estado] == 'Sí'])
porcentaje = (total_asistentes / total_registrados) if total_registrados > 0 else 0.0

with col_der:
    st.subheader("Resumen en Vivo")
    st.metric("Inscritos Totales", total_registrados)
    st.metric("Registrados hoy", total_asistentes)
    st.progress(float(porcentaje))
    
    st.divider()
    columnas_exportar = [col for col in df_local.columns if col != 'email_limpio']
    csv_exportable = df_local[columnas_exportar].to_csv(index=False).encode('utf-8')
    nombre_archivo = f"reporte_{evento_actual.replace(' ', '_').replace(':', '')}.csv"
    
    st.download_button(
        label="Guardar Datos Actuales (CSV)",
        data=csv_exportable,
        file_name=nombre_archivo,
        mime="text/csv"
    )
