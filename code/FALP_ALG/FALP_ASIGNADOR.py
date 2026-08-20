#%%=======================================================Import Libreries===============================================
#Data manipulation and analysis.
import pandas as pd
from datetime import timedelta

#%%=======================================================Definición de parámetros========================================

ruta_df = pd.read_excel('Ruta.xlsx', sheet_name='Resultados')

# Ejecutar el script OFERTA_MEDICA.py
exec(open('OFERTA_MEDICA.py').read())

#%%=======================================================Función========================================

# Lista para almacenar las asignaciones
asignaciones = []
fechas_asignadas = {}
eventos_pendientes = {}

# Función para confirmar o bloquear fecha
def confirmar_fecha(horario_disponible, fecha_inicio, fecha_fin, periodicidad, modalidad_atencion):
    while True:
        # Filtrar las fechas dentro del rango permitido
        horario_disponible_rango = horario_disponible[
            (horario_disponible['FECHA.FECHA'] >= fecha_inicio) &
            (horario_disponible['FECHA.FECHA'] <= fecha_fin) &
            ((horario_disponible['MODALIDAD_ATENCION'] == modalidad_atencion) |
             (horario_disponible['MODALIDAD_ATENCION'] == 'TODOS'))
        ]

        # Verificar si hay fechas disponibles dentro del rango
        if horario_disponible_rango.empty:
            print("No hay más fechas disponibles dentro del rango permitido.")
            return None, None

        # Opción 1: Día más próximo disponible con cupos restantes
        dia_mas_proximo = horario_disponible_rango.loc[horario_disponible_rango['FECHA.FECHA'].idxmin()]

        # Opción 2: Día con la mayor cantidad de cupos restantes
        dia_mayor_cupos = horario_disponible_rango.loc[horario_disponible_rango['CANTIDAD_CUPOS_RESTANTES'].idxmax()]

        # Calcular atrasos
        atraso_mas_proximo = (dia_mas_proximo['FECHA.FECHA'] - fecha_inicio).days - periodicidad
        atraso_mayor_cupos = (dia_mayor_cupos['FECHA.FECHA'] - fecha_inicio).days - periodicidad

        print("\nOpciones de asignación:")
        print(f"1. Día más próximo disponible: {dia_mas_proximo['FECHA.FECHA']} con {dia_mas_proximo['CANTIDAD_CUPOS_RESTANTES']} cupos restantes. Atraso: {atraso_mas_proximo} días.")
        print(f"2. Día con mayor cantidad de cupos restantes: {dia_mayor_cupos['FECHA.FECHA']} con {dia_mayor_cupos['CANTIDAD_CUPOS_RESTANTES']} cupos restantes. Atraso: {atraso_mayor_cupos} días.")

        seleccion_opcion = int(input("Seleccione la opción de asignación (1 o 2): "))
        asignacion_final = dia_mas_proximo if seleccion_opcion == 1 else dia_mayor_cupos

        print(f"\nAsignación final: {asignacion_final['FECHA.FECHA']} con {asignacion_final['CANTIDAD_CUPOS_RESTANTES']} cupos restantes. Atraso: {(asignacion_final['FECHA.FECHA'] - fecha_inicio).days - periodicidad} días")
        
        confirmar = input(f"¿Confirma la fecha {asignacion_final['FECHA.FECHA']}? (s/n): ").strip().lower()
        if confirmar == 's':
            # Actualizar CUPOS_UTILIZADOS
            tabla_resultado.loc[
                (tabla_resultado['FECHA.FECHA'] == asignacion_final['FECHA.FECHA']) &
                (tabla_resultado['NOMBRE_BLOQUE'] == asignacion_final['NOMBRE_BLOQUE']) &
                (tabla_resultado['NOMBRE_MEDICO'] == asignacion_final['NOMBRE_MEDICO']) &
                (tabla_resultado['MODALIDAD_ATENCION'] == asignacion_final['MODALIDAD_ATENCION']),
                'CUPOS_UTILIZADOS'
            ] += 1

            # Recalcular CANTIDAD_CUPOS_RESTANTES después de actualizar CUPOS_UTILIZADOS
            tabla_resultado['CANTIDAD_CUPOS_RESTANTES'] = tabla_resultado['CANTIDAD_CUPOS_TOTALES'] - tabla_resultado['CUPOS_UTILIZADOS'] - tabla_resultado['CUPOS_BLOQUEADOS']

            return asignacion_final, (asignacion_final['FECHA.FECHA'] - fecha_inicio).days - periodicidad
        else:
            # Bloquear la fecha seleccionada y continuar con la siguiente disponible
            horario_disponible = horario_disponible[horario_disponible['FECHA.FECHA'] != asignacion_final['FECHA.FECHA']]
            if horario_disponible.empty:
                print("No hay más fechas disponibles.")
                return None, None

# Función para verificar dependencias
def verificar_dependencias(registro_ruta, eventos_pendientes):
    dependencias = registro_ruta['DEPENDENCIA']
    rut_paciente = registro_ruta['RUT_PACIENTE']
    numero_evento = registro_ruta['NÚMERO']

    if any([int(dep) in eventos_pendientes.get(rut_paciente, []) for dep in dependencias.strip('[]').split(',')]):
        print(f"El evento {numero_evento} del paciente {rut_paciente} queda pendiente debido a dependencias pendientes.")
        asignaciones.append({
            'RUT_PACIENTE': rut_paciente,
            'NÚMERO': numero_evento,
            'NOMBRE_AGENDA': registro_ruta['NOMBRE_AGENDA'],
            'SERVICE': registro_ruta['SERVICIO_AGENDA'],
            'SECTION': registro_ruta['SECCION_AGENDA'],
            'MEDICO': registro_ruta['MEDICO'],
            'NOMBRE_BLOQUE': 'Pendiente',
            'FECHA_HORA_MEDICA': 'Pendiente',
            'ATRASO_DIAS': 'Pendiente',
            'MODALIDAD_ATENCION': registro_ruta['MODALIDAD_ATENCION']
        })
        if rut_paciente not in eventos_pendientes:
            eventos_pendientes[rut_paciente] = []
        eventos_pendientes[rut_paciente].append(numero_evento)
        return False
    return True

# Función para filtrar el horario y recalcular los cupos restantes
def filtrar_horario(tabla_resultado, servicio_seleccionado, seccion_seleccionada, considerar_sobrecupos):
    horario_filtrado = tabla_resultado[
        (tabla_resultado['SERVICE'] == servicio_seleccionado) &
        (tabla_resultado['SECTION'] == seccion_seleccionada)
    ]
    if considerar_sobrecupos:
        horario_filtrado.loc[:, 'CANTIDAD_CUPOS_TOTALES'] = horario_filtrado['CANTIDAD_CUPOS'] + horario_filtrado['CANTIDAD_SOBRECUPO']
    else:
        horario_filtrado.loc[:, 'CANTIDAD_CUPOS_TOTALES'] = horario_filtrado['CANTIDAD_CUPOS']
    horario_filtrado.loc[:, 'CANTIDAD_CUPOS_RESTANTES'] = horario_filtrado['CANTIDAD_CUPOS_TOTALES'] - horario_filtrado['CUPOS_UTILIZADOS'] - horario_filtrado['CUPOS_BLOQUEADOS']
    return horario_filtrado

# Función para gestionar asignación pendiente
def asignar_pendiente(registro_ruta, motivo):
    print(motivo)
    rut_paciente = registro_ruta['RUT_PACIENTE']
    numero_evento = registro_ruta['NÚMERO']
    asignaciones.append({
        'RUT_PACIENTE': rut_paciente,
        'NÚMERO': numero_evento,
        'NOMBRE_AGENDA': registro_ruta['NOMBRE_AGENDA'],
        'SERVICE': registro_ruta['SERVICIO_AGENDA'],
        'SECTION': registro_ruta['SECCION_AGENDA'],
        'MEDICO': registro_ruta['MEDICO'],
        'NOMBRE_BLOQUE': 'Pendiente',
        'FECHA_HORA_MEDICA': 'Pendiente',
        'ATRASO_DIAS': 'Pendiente',
        'MODALIDAD_ATENCION': registro_ruta['MODALIDAD_ATENCION']
    })
    if rut_paciente not in eventos_pendientes:
        eventos_pendientes[rut_paciente] = []
    eventos_pendientes[rut_paciente].append(numero_evento)

# Función para obtener motivo de consulta correcto
def obtener_motivo_consulta(motivo_consulta):
    if motivo_consulta == 'Primera Consulta':
        return 'Nuevos pacientes'
    else:
        return 'Control'

# Iterar sobre cada registro en el archivo Ruta.xlsx
for _, registro_ruta in ruta_df.iterrows():
    # Obtener datos del registro
    rut_paciente = registro_ruta['RUT_PACIENTE']
    servicio_seleccionado = registro_ruta['SERVICIO_AGENDA']
    seccion_seleccionada = registro_ruta['SECCION_AGENDA']
    medico_necesitado = registro_ruta['MEDICO']
    periodicidad = registro_ruta['PERIODICIDAD (DÍAS)']
    maximo_dias = registro_ruta['MÁXIMO (DÍAS)']
    considerar_sobrecupos = bool(registro_ruta['SOBRECUPOS'])
    numero_evento = registro_ruta['NÚMERO']
    modalidad_atencion = registro_ruta['MODALIDAD_ATENCION']
    motivo_consulta = obtener_motivo_consulta(registro_ruta['MOTIVO_CONSULTA'])

    # Verificar dependencias
    if not verificar_dependencias(registro_ruta, eventos_pendientes):
        continue

    # Filtrar la tabla para mostrar solo las filas correspondientes al servicio y sección seleccionados
    horario_filtrado = filtrar_horario(tabla_resultado, servicio_seleccionado, seccion_seleccionada, considerar_sobrecupos)

    # Filtrar por motivo de consulta
    horario_filtrado = horario_filtrado[horario_filtrado['MOTIVO_CONSULTA'] == motivo_consulta]

    # Verificar si el médico necesitado está disponible
    if medico_necesitado != 'TODOS' and medico_necesitado not in horario_filtrado['NOMBRE_MEDICO'].unique():
        # Verificar si hay otras modalidades disponibles para el médico
        otras_modalidades = horario_filtrado[
            (horario_filtrado['NOMBRE_MEDICO'] == medico_necesitado) &
            (horario_filtrado['MODALIDAD_ATENCION'] != modalidad_atencion)
        ]
        if not otras_modalidades.empty:
            print(f"El médico {medico_necesitado} no tiene disponibilidad en la modalidad {modalidad_atencion}, pero tiene en las siguientes modalidades:")
            modalidades_disponibles = otras_modalidades['MODALIDAD_ATENCION'].unique()
            for i, modalidad in enumerate(modalidades_disponibles, start=1):
                print(f"{i}. {modalidad}")
            print(f"{len(modalidades_disponibles) + 1}. Buscar con TODOS los médicos")
            print(f"{len(modalidades_disponibles) + 2}. Quedar agendada como Pendiente")
            opcion_fallback = int(input(f"Seleccione una opción (1-{len(modalidades_disponibles) + 2}): "))
            if opcion_fallback == len(modalidades_disponibles) + 1:
                medico_seleccionado = "TODOS"
            elif opcion_fallback == len(modalidades_disponibles) + 2:
                asignar_pendiente(registro_ruta, "La asignación ha quedado como 'Pendiente'.")
                continue
            else:
                modalidad_atencion = modalidades_disponibles[opcion_fallback - 1]
        else:
            print(f"El médico {medico_necesitado} no tiene disponibilidad en la modalidad {modalidad_atencion} y no hay otras modalidades disponibles.")
            opcion_fallback = int(input("Seleccione 1 para buscar con TODOS los médicos, 2 para quedar agendada como Pendiente: "))
            if opcion_fallback == 1:
                medico_seleccionado = "TODOS"
            else:
                asignar_pendiente(registro_ruta, "La asignación ha quedado como 'Pendiente'.")
                continue
    else:
        medico_seleccionado = medico_necesitado

    # Filtrar la tabla para mostrar solo las filas correspondientes al médico seleccionado o todos los médicos
    if medico_seleccionado == "TODOS":
        horario_final = horario_filtrado
    else:
        horario_final = horario_filtrado[horario_filtrado['NOMBRE_MEDICO'] == medico_seleccionado]

    # Mostrar el horario del servicio, sección, y médico seleccionados
    if not horario_final.empty:
        print(f"Horario de oferta para el servicio {servicio_seleccionado}, sección {seccion_seleccionada}, médico {medico_seleccionado}:" if medico_seleccionado != "TODOS" else f"Horario de oferta para el servicio {servicio_seleccionado}, sección {seccion_seleccionada}, todos los médicos:")
        print(horario_final)

        # Filtrar los horarios disponibles
        horario_disponible = horario_final[
            (horario_final['CANTIDAD_CUPOS_RESTANTES'] > 0) &
            ((horario_final['MODALIDAD_ATENCION'] == modalidad_atencion) |
             (horario_final['MODALIDAD_ATENCION'] == 'TODOS'))
        ]

        if not horario_disponible.empty:
            # Determinar la fecha de inicio en función de las dependencias
            if registro_ruta['DEPENDENCIA'] == '[0]':
                fecha_inicio = horario_disponible['FECHA.FECHA'].min() + timedelta(days=periodicidad)
            else:
                fechas_dependencias = [fechas_asignadas[rut_paciente][int(dep)] for dep in registro_ruta['DEPENDENCIA'].strip('[]').split(',') if rut_paciente in fechas_asignadas and int(dep) in fechas_asignadas[rut_paciente]]
                fecha_inicio = max(fechas_dependencias) + timedelta(days=periodicidad) if fechas_dependencias else horario_disponible['FECHA.FECHA'].min() + timedelta(days=periodicidad)

            # Calcular la fecha de fin según el máximo de días permitido
            fecha_fin = fecha_inicio + timedelta(days=maximo_dias)
            print(f"Asignando evento {numero_evento} para el paciente {rut_paciente}. La fecha de inicio es {fecha_inicio} y la fecha final es {fecha_fin}. Modalidad de atención: {modalidad_atencion}.")
            
            asignacion_final, atraso_dias = confirmar_fecha(horario_disponible, fecha_inicio, fecha_fin, periodicidad, modalidad_atencion)
            if asignacion_final is not None:
                # Agregar la asignación a la lista
                asignaciones.append({
                    'RUT_PACIENTE': registro_ruta['RUT_PACIENTE'],
                    'NÚMERO': registro_ruta['NÚMERO'],
                    'NOMBRE_AGENDA': registro_ruta['NOMBRE_AGENDA'],
                    'SERVICE': servicio_seleccionado,
                    'SECTION': seccion_seleccionada,
                    'MEDICO': asignacion_final['NOMBRE_MEDICO'],
                    'NOMBRE_BLOQUE': asignacion_final['NOMBRE_BLOQUE'],
                    'FECHA_HORA_MEDICA': asignacion_final['FECHA.FECHA'],
                    'ATRASO_DIAS': atraso_dias,
                    'MODALIDAD_ATENCION': modalidad_atencion
                })
                if rut_paciente not in fechas_asignadas:
                    fechas_asignadas[rut_paciente] = {}
                fechas_asignadas[rut_paciente][numero_evento] = asignacion_final['FECHA.FECHA']
            else:
                asignar_pendiente(registro_ruta, f"No hay más fechas disponibles dentro del rango permitido para el evento {numero_evento} del paciente {rut_paciente}.")
        else:
            asignar_pendiente(registro_ruta, f"No hay cupos disponibles para el evento {numero_evento} del paciente {rut_paciente}.")
    else:
        asignar_pendiente(registro_ruta, f"No se encontraron ofertas para el servicio: {servicio_seleccionado}, sección: {seccion_seleccionada}, médico: {medico_seleccionado}")

# Guardar todas las asignaciones en un archivo Excel
asignaciones_df = pd.DataFrame(asignaciones)
columnas = [
    "RUT_PACIENTE",
    "NÚMERO",
    "NOMBRE_AGENDA",
    "SERVICE",
    "SECTION",
    "MEDICO",
    "NOMBRE_BLOQUE",
    "FECHA_HORA_MEDICA",
    "ATRASO_DIAS",
    "MODALIDAD_ATENCION"
]
asignaciones_df = asignaciones_df[columnas]
asignaciones_df.to_excel('rutas_asignadas.xlsx', index=False)

#que se vayan incorporando a 'CUPOS_UTILIZADOS'.