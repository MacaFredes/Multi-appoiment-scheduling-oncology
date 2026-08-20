import pandas as pd
import re

#%%=======================================================Definición de parámetros========================================
def procesar_oferta(file_path):
    oferta_medica = pd.read_excel(file_path, sheet_name='OFERTA')

    def determinar_modalidad(bloque):
        if 'TELEMEDICINA' in bloque:
            return 'VIDEOLLAMADA'
        elif 'FONOCONSULTA' in bloque:
            return 'FONOLLAMADA'
        elif 'MIXTO' in bloque:
            return 'TODOS'
        else:
            return 'PRESENCIAL'

    def separar_cupos(row):
        bloque = row['NOMBRE_BLOQUE']
        total_cupos = row['CANTIDAD_CUPOS']
        sobrecupo = row.get('CANTIDAD_SOBRECUPO', 0)
        
        match = re.search(r'\(\s*(\d+)\s*CUPOS?\s*\)', bloque, re.IGNORECASE) or re.search(r'agendar en\s*(\d+)\s*cupos?', bloque, re.IGNORECASE)
        if match:
            nuevos_cupos = int(match.group(1))
            controles_cupos = total_cupos - nuevos_cupos
            
            row_nuevos = row.copy()
            row_nuevos['CANTIDAD_CUPOS'] = nuevos_cupos
            row_nuevos['CANTIDAD_CUPOS_MAXIMO'] = nuevos_cupos + sobrecupo
            row_nuevos['NOMBRE_BLOQUE'] = re.sub(r'\(\s*\d+\s*CUPOS?\s*\)', '', bloque, flags=re.IGNORECASE)
            row_nuevos['NOMBRE_BLOQUE'] = re.sub(r'agendar en\s*\d+\s*cupos?', '', row_nuevos['NOMBRE_BLOQUE'], flags=re.IGNORECASE)
            row_nuevos['NOMBRE_BLOQUE'] = row_nuevos['NOMBRE_BLOQUE'].replace('Control', 'Pacientes Nuevos')
            
            row_controles = row.copy()
            row_controles['CANTIDAD_CUPOS'] = controles_cupos
            row_controles['CANTIDAD_CUPOS_MAXIMO'] = controles_cupos + sobrecupo
            row_controles['NOMBRE_BLOQUE'] = re.sub(r'\(\s*\d+\s*CUPOS?\s*\)', '', bloque, flags=re.IGNORECASE)
            row_controles['NOMBRE_BLOQUE'] = re.sub(r'agendar en\s*\d+\s*cupos?', '', row_controles['NOMBRE_BLOQUE'], flags=re.IGNORECASE)
            row_controles['NOMBRE_BLOQUE'] = row_controles['NOMBRE_BLOQUE'].replace('Pacientes Nuevos', 'Control')
            
            return [row_nuevos, row_controles]
        else:
            return [row]

    new_rows = []
    for _, row in oferta_medica.iterrows():
        new_rows.extend(separar_cupos(row))

    oferta_medica_actualizada = pd.DataFrame(new_rows)

    oferta_medica_actualizada['MODALIDAD_ATENCION'] = oferta_medica_actualizada['NOMBRE_BLOQUE'].apply(determinar_modalidad)

    def determinar_motivo(bloque):
        if 'Pacientes Nuevos' in bloque or 'Pacientes nuevos' in bloque:
            return 'Nuevos pacientes'
        else:
            return 'Control'

    oferta_medica_actualizada['MOTIVO_CONSULTA'] = oferta_medica_actualizada['NOMBRE_BLOQUE'].apply(determinar_motivo)

    return oferta_medica_actualizada

# Ruta al archivo de oferta
file_path = 'Data/OFERTA.xlsx'

# Llamar a la función procesar_oferta
oferta_medica_actualizada = procesar_oferta(file_path)

seccion_agenda = pd.read_excel('Data/SECCION_AGENDA.xlsx',sheet_name ='SECCION_AGENDA')

bloqueos = pd.read_excel('Data/BLOQUEOS.xlsx',sheet_name ='BLOQUEOS')

# Eliminar espacios en blanco al principio y al final de NOMBRE_AGENDA XDXDXD
seccion_agenda['MEDICO'] = seccion_agenda['MEDICO'].str.strip()

#%%=======================================================Procesamiento Oferta========================================

# Seleccionar solo las columnas necesarias de SECCION_AGENDA
columnas_seccion_agenda = ['MEDICO', 'SECTION_SERVICE_CENTER_KEY', 'SECTION', 'SERVICE', 'CENTER']
seccion_agenda_seleccionada = seccion_agenda[columnas_seccion_agenda]

# Convertir la columna 'FECHA.FECHA' a tipo datetime
oferta_medica_actualizada['FECHA.FECHA'] = pd.to_datetime(oferta_medica_actualizada['FECHA.FECHA'], dayfirst=True)

# Definir la fecha desde la cual queremos filtrar (por ejemplo, 19-06-2024)
fecha_inicio = pd.to_datetime('19-06-2024', dayfirst=True)

# Filtrar los datos desde la fecha especificada en adelante
oferta_filtrada = oferta_medica_actualizada[oferta_medica_actualizada['FECHA.FECHA'] >= fecha_inicio]

# Filtrar las filas donde 'ACTIVE' es igual a 1
oferta_activa = oferta_filtrada[oferta_filtrada['ACTIVE'] == 1]

# Seleccionar las columnas relevantes de oferta_medica
columnas_interes = ['NOMBRE_MEDICO', 'FECHA.FECHA', 'CANTIDAD_CUPOS', 'CANTIDAD_SOBRECUPO', 'NOMBRE_BLOQUE', 'SECTION_SERVICE_CENTER_KEY', 'NOMBRE_AGENDA', 'AGENDA_SCHEDULE_KEY', 'MODALIDAD_ATENCION', 'MOTIVO_CONSULTA']
oferta_seleccionada = oferta_activa[columnas_interes]

# Agrupar por NOMBRE_MEDICO, NOMBRE_BLOQUE y FECHA.FECHA, y sumar CANTIDAD_CUPOS y CANTIDAD_SOBRECUPO
tabla_resultado = oferta_seleccionada.groupby(['NOMBRE_MEDICO', 'NOMBRE_BLOQUE', 'FECHA.FECHA', 'SECTION_SERVICE_CENTER_KEY', 'NOMBRE_AGENDA', 'AGENDA_SCHEDULE_KEY', 'MODALIDAD_ATENCION', 'MOTIVO_CONSULTA']).agg(
    {'CANTIDAD_CUPOS': 'sum', 'CANTIDAD_SOBRECUPO': 'sum'}
).reset_index()

# Inicialmente, establecer CANTIDAD_CUPOS_TOTALES igual a CANTIDAD_CUPOS
tabla_resultado['CANTIDAD_CUPOS_TOTALES'] = tabla_resultado['CANTIDAD_CUPOS']

# Agrupar y sumar los bloqueos por AGENDA_SCHEDULE_KEY, NOMBRE_AGENDA y OFERTA_AGENDA.FECHA.FECHA
bloqueos_agrupados = bloqueos.groupby(['AGENDA_SCHEDULE_KEY', 'NOMBRE_AGENDA', 'OFERTA_AGENDA.FECHA.FECHA']).agg(
    {'CUPOS_BLOQUEADOS': 'sum'}
).reset_index()

# Renombrar la columna de fecha en bloqueos_agrupados para coincidir con oferta_medica
bloqueos_agrupados = bloqueos_agrupados.rename(columns={'OFERTA_AGENDA.FECHA.FECHA': 'FECHA.FECHA'})

# Realizar el merge con tabla_resultado para restar los bloqueos
tabla_resultado = pd.merge(tabla_resultado, bloqueos_agrupados, 
                           how='left', 
                           left_on=['AGENDA_SCHEDULE_KEY', 'NOMBRE_AGENDA', 'FECHA.FECHA'], 
                           right_on=['AGENDA_SCHEDULE_KEY', 'NOMBRE_AGENDA', 'FECHA.FECHA'])

# Rellenar los NaN en CUPOS_BLOQUEADOS con 0
tabla_resultado['CUPOS_BLOQUEADOS'] = tabla_resultado['CUPOS_BLOQUEADOS'].fillna(0)

# Agregar la columna CUPOS_UTILIZADOS y llenarla con ceros
tabla_resultado['CUPOS_UTILIZADOS'] = 0

# Calcular los cupos restantes
tabla_resultado['CANTIDAD_CUPOS_RESTANTES'] = tabla_resultado['CANTIDAD_CUPOS_TOTALES'] - tabla_resultado['CUPOS_UTILIZADOS'] - tabla_resultado['CUPOS_BLOQUEADOS']

# Realizar el merge con SECCION_AGENDA para agregar las columnas SECTION, SERVICE, CENTER
tabla_resultado = pd.merge(tabla_resultado, seccion_agenda_seleccionada, 
                            how='left', 
                            left_on=['NOMBRE_MEDICO', 'SECTION_SERVICE_CENTER_KEY'], 
                            right_on=['MEDICO', 'SECTION_SERVICE_CENTER_KEY'])

# # Eliminar la columna 'MÉDICO'
# tabla_resultado = tabla_resultado.drop(columns=['MÉDICO'])

# Ordenar la tabla resultante por 'FECHA.FECHA' desde la más próxima hasta la más lejana
tabla_resultado = tabla_resultado.sort_values(by='FECHA.FECHA', ascending=True)

# Guardar la tabla resultante en un nuevo archivo Excel (opcional)
tabla_resultado.to_excel('tabla_resultado.xlsx', index=False)