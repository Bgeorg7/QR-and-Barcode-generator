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
        st.session_state.df = pd.read_excel('base_completa.xlsx',sheet_name='attendees')
        st.session_state.df.columns = st.session_state.df.columns.str.strip()
        if 'uuid' in st.session_state.df.columns:
            st.session_state.df['uuid'] = st.session_state.df['uuid'].astype(str)
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

st.title(f"{categoria_control}")
st.write(f"Operando control de: **{evento_actual}**")

col_izq, col_der = st.columns([2, 1])

with col_izq:
    st.subheader("Escáner / Entrada Manual")
    with st.form(key='formulario_escaneo', clear_on_submit=True):
        codigo_escaneado = st.text_input("UUID de Escarapela:")
        boton_registrar = st.form_submit_button(label='Registrar Entrada')

    if boton_registrar and codigo_escaneado:
        codigo_limpio = codigo_escaneado.strip()
        filtro = df_local['uuid'] == codigo_limpio

        if filtro.any():
            indice = df_local.index[filtro].tolist()[0]
            
            nombre_comp = f"{df_local.at[indice, 'first_name']} {df_local.at[indice, 'last_name']}" if 'first_name' in df_local.columns and 'last_name' in df_local.columns else "Sin Nombre"
            sede_user = df_local.at[indice, 'SEDE'] if 'SEDE' in df_local.columns else "Sin Sede"
            alimentacion = df_local.at[indice, 'Tipo_Alimentacion'] if 'Tipo_Alimentacion' in df_local.columns else "No especificado"
            talleres_completos = df_local.at[indice, 'Talleres_Obligatorios'] if 'Talleres_Obligatorios' in df_local.columns else "No especificado"

            
            if evento_actual in ["Ida: Bogotá -> Manizales", "Llegada Manizales (Validar Requisitos)"] and talleres_completos == 'No':
                st.error(f"DENEGADO: A {nombre_comp} le faltan talleres obligatorios.")
            
            elif categoria_control in ["Alimentación Principal", "Refrigerios"] and df_local.at[indice, col_estado] == 'Sí':
                st.warning(f"YA ENTREGADO: {nombre_comp} ya reclamó esto a las {df_local.at[indice, col_hora]}.\n\nDieta: **{alimentacion}**")
            
            elif categoria_control in ["Ingreso al ENEUN (Check-in)", "Buses"] and df_local.at[indice, col_estado] == 'Sí':
                st.warning(f"R️EPETIDO: {nombre_comp} ya fue registrado en {evento_actual} a las {df_local.at[indice, col_hora]}.")

            else:
                hora_actual = datetime.now().strftime("%H:%M:%S")
                
                es_reingreso = (categoria_control == "Asistencia a Lugares" and df_local.at[indice, col_estado] == 'Sí')
                
                st.session_state.df.at[indice, col_estado] = 'Sí'
                st.session_state.df.at[indice, col_hora] = hora_actual
                
                if es_reingreso:
                    st.success(f"REINGRESO APROBADO")
                else:
                    st.success(f"ACCESO APROBADO")
                
                with st.container(border=True):
                    st.markdown(f"**Participante:** {nombre_comp}")
                    st.markdown(f"**Sede:** {sede_user}")
                    
                    if categoria_control in ["Alimentación Principal", "Refrigerios"]:
                        st.markdown(f"**Entregar Dieta:** 🍽️ {alimentacion}")
                    
                    st.markdown(f"**Registro:** {hora_actual}")
                
        else:
            st.error("DENEGADO: Código no encontrado en la base de datos.")

total_registrados = len(df_local)
total_asistentes = len(df_local[df_local[col_estado] == 'Sí'])
porcentaje = (total_asistentes / total_registrados) * 100 if total_registrados > 0 else 0

with col_der:
    st.subheader("Resumen en Vivo")
    st.metric("Inscritos Totales", total_registrados)
    st.metric(f"Registrados hoy", total_asistentes)
    st.progress(porcentaje / 100)
    
    st.divider()
    csv_exportable = df_local.to_csv(index=False).encode('utf-8')
    nombre_archivo = f"reporte_{evento_actual.replace(' ', '_').replace(':', '')}.csv"
    st.download_button(
        label="Guardar Datos Actuales (CSV)",
        data=csv_exportable,
        file_name=nombre_archivo,
        mime="text/csv"
    )
