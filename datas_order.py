import streamlit as st
import pandas as pd
import plotly.express as px 
import io

ARCHIVO = 'base_completa.xlsx'

st.set_page_config(layout="wide")

try:
    df = pd.read_excel(ARCHIVO, sheet_name='attendees')
    df.columns = df.columns.str.strip()
except Exception as e:
    st.error(f"Error al leer el archivo: {e}")
    st.stop()

df_conf = df.copy()

col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True):
        st.subheader("Asistentes por Sede")
        if 'sede' in df_conf.columns:
            conf_sede = df_conf['sede'].value_counts().reset_index()
            conf_sede.columns = ['Sede', 'Total']
            st.dataframe(conf_sede, hide_index=True, width='stretch')
            st.write(f"Total Nacional: {len(df_conf)}")
            
            fig_sede = px.pie(conf_sede, values='Total', names='Sede', hole=0.3) 
            fig_sede.update_traces(textposition='inside', textinfo='percent+label')
            fig_sede.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10), height=300)
            st.plotly_chart(fig_sede, use_container_width=True)
            
        else:
            st.warning("No se encontró la columna 'sede'.")

with col2:
    with st.container(border=True):
        st.subheader("Opciones de Alojamiento")
        if 'lodging_choice' in df_conf.columns:
            alojamiento_limpio = df_conf['lodging_choice'].copy()
            alojamiento_limpio = alojamiento_limpio.replace({
                'Holtel, Hostal, Airbnb, etc...': 'Hotel, Hostal, Airbnb, etc...',
                'Planea acampar': 'Planea Acampar'
            })
            alojamiento = alojamiento_limpio.value_counts().reset_index()
            alojamiento.columns = ['Alojamiento', 'Total']
            st.dataframe(alojamiento, hide_index=True, width='stretch')
        else:
            st.warning("No se encontró la columna 'lodging_choice'.")

with col3:
    with st.container(border=True):
        st.subheader("Salud y Emergencias")
        if 'health_condition_codes' in df_conf.columns:
            
            texto_limpio = df_conf['health_condition_codes'].astype(str).str.replace('{', '').str.replace('}', '').str.strip().str.upper()
            
            df_med = df_conf[
                (df_conf['health_condition_codes'].notna()) & 
                (texto_limpio != '') & 
                (texto_limpio != 'NAN') & 
                (texto_limpio != 'NONE')
            ]
            
            st.metric("Total con condiciones médicas reales", len(df_med))
            
            if len(df_med) > 0:
                st.write("Muestra de casos médicos:")
                df_med_mostrar = df_med[['legal_name', 'health_condition_codes']].copy()
                df_med_mostrar['health_condition_codes'] = df_med_mostrar['health_condition_codes'].str.replace('{', '').str.replace('}', '')
                st.dataframe(df_med_mostrar.head(5), hide_index=True, width='stretch')
            else:
                st.write("Ningún asistente ha reportado condiciones médicas.")
                
        else:
            st.warning("No se encontraron datos médicos.")

col4, col5 = st.columns(2)

with col4:
    with st.container(border=True):
        st.subheader("Facultades")
        if 'faculty' in df_conf.columns:
            facultades = df_conf['faculty'].value_counts().reset_index()
            facultades.columns = ['Facultad', 'Total']
            st.dataframe(facultades, hide_index=True, width='stretch')

with col5:
    with st.container(border=True):
        st.subheader("Género")
        if 'pronoun' in df_conf.columns:
            pronombres_limpios = df_conf['pronoun'].astype(str).str.strip().str.lower()
            
            df_pro = df_conf[
                (df_conf['pronoun'].notna()) & 
                (pronombres_limpios != '') & 
                (pronombres_limpios != 'nan') & 
                (pronombres_limpios != 'none')
            ]
            
            pronombres_totales = df_pro['pronoun'].value_counts().reset_index()
            pronombres_totales.columns = ['Pronombre', 'Total']
            st.dataframe(pronombres_totales, hide_index=True, width='stretch')
            
            fig_genero = px.pie(pronombres_totales, values='Total', names='Pronombre', hole=0.3)
            fig_genero.update_traces(textposition='inside', textinfo='percent+label')
            fig_genero.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10), height=300)
            st.plotly_chart(fig_genero, use_container_width=True)
            
        else:
            st.warning("No se encontró la columna 'pronoun'.")

st.write("")

with st.container(border=True):
    col_txt, col_btn = st.columns([3, 1])
    
    with col_txt:
        st.write("Descargar toda la base de datos logística con nombres, sedes, salud, emergencias y alojamiento.")
    
    with col_btn:
        columnas_descarga = [
            'identification_number', 'legal_name', 'email', 'sede', 'faculty', 'career',
            'blood_type_id', 'eps_id', 'health_condition_codes', 'health_details',
            'emergency_contact_name', 'emergency_contact_relationship', 'emergency_contact_phone',
            'lodging_choice', 'lodging_address', 'camping_confirmation'
        ]
        
        df_descarga = df_conf[[c for c in columnas_descarga if c in df_conf.columns]]
        
        buffer = io.BytesIO()
        df_descarga.to_excel(buffer, index=False, engine='xlsxwriter')
        st.download_button(
            label="Descargar Base Logística",
            data=buffer.getvalue(),
            file_name="Logistica_ENEUN_Organizado.xlsx",
            mime="application/vnd.ms-excel",
            use_container_width=True 
        )