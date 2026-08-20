#Data manipulation and analysis.
import pandas as pd

#%%=======================================================Excel========================================
# Leer datos de la tabla SECCION_AGENDA desde un archivo Excel
seccion_agenda_df = pd.read_excel('SECCION_AGENDA.xlsx')
servicios_agenda_unicos = seccion_agenda_df['SERVICE'].unique()
#%%=======================================================Generar información========================================
# Inicializamos una lista vacía para almacenar los datos
data = []

# Opciones para MOTIVO_CONSULTA
opciones_motivo_consulta = [
    "Control", 
    "Muestra de exámenes", 
    "Post operado", 
    "Primera Consulta", 
    "Resolución Comité", 
    "Seguimiento", 
    "Término de tratamiento"
]

# Función para seleccionar una opción de una lista
def seleccionar_opcion(lista_opciones, mensaje):
    print(mensaje)
    for i, opcion in enumerate(lista_opciones):
        print(f"{i + 1}. {opcion}")
    seleccion = int(input("Ingrese el número de la opción: "))
    return lista_opciones[seleccion - 1]

# Función para agregar eventos de un paciente
def agregar_eventos_paciente(rut_paciente):
    # Selección del tipo de previsión
    opciones_prevision = ["BENEFICIARIO", "FONASA", "ISAPRE", "PARTICULAR"]
    tipo_prevision = seleccionar_opcion(opciones_prevision, "Seleccione el tipo de previsión:")

    numero_evento = 1
    while True:
        periodicidad = int(input("Ingrese la periodicidad (días): "))
        maximo_dias = int(input("Ingrese el máximo de días: "))
        sobrecupos = int(input("¿Se consideran sobrecupos? (1 para sí, 0 para no): "))
        
        # Selección de la modalidad de atención
        opciones_modalidad = ["PRESENCIAL", "VIDEOLLAMADA", "FONOLLAMADA", "TODOS"]
        modalidad_atencion = seleccionar_opcion(opciones_modalidad, "Seleccione la modalidad de atención:")

        # Selección del motivo de consulta
        motivo_consulta = seleccionar_opcion(opciones_motivo_consulta, "Seleccione el motivo de consulta:")

        eventos_previos = [evento['NÚMERO'] for evento in data if evento['RUT_PACIENTE'] == rut_paciente]

        if eventos_previos:
            print("Seleccione los números de los eventos previos para la dependencia (separados por coma si son varios):")
            for num in eventos_previos:
                print(f"{num}")
            dependencias_input = input("Ingrese los números de los eventos para la dependencia: ")
            dependencias_list = [int(num) for num in dependencias_input.split(",")]
        else:
            dependencias_list = [0]

        print("Seleccione el servicio de la agenda de las siguientes opciones:")
        for i, servicio in enumerate(servicios_agenda_unicos):
            print(f"{i + 1}. {servicio}")
        servicio_seleccionado = int(input("Ingrese el número del servicio: "))
        servicio_agenda = servicios_agenda_unicos[servicio_seleccionado - 1]

        secciones_agenda_filtradas = seccion_agenda_df[seccion_agenda_df['SERVICE'] == servicio_agenda]['SECTION'].unique()

        print("Seleccione la sección de la agenda de las siguientes opciones:")
        for i, seccion in enumerate(secciones_agenda_filtradas):
            print(f"{i + 1}. {seccion}")
        seccion_seleccionada = int(input("Ingrese el número de la sección: "))
        seccion_agenda = secciones_agenda_filtradas[seccion_seleccionada - 1]

        medicos_filtrados = seccion_agenda_df[(seccion_agenda_df['SERVICE'] == servicio_agenda) & 
                                              (seccion_agenda_df['SECTION'] == seccion_agenda)]['MÉDICO'].unique()
        medicos_filtrados = list(medicos_filtrados) + ['TODOS']

        print("Seleccione el médico de las siguientes opciones:")
        for i, medico in enumerate(medicos_filtrados):
            print(f"{i + 1}. {medico}")
        medico_seleccionado = int(input("Ingrese el número del médico: "))
        medico = medicos_filtrados[medico_seleccionado - 1]

        if medico == 'TODOS':
            nombre_agenda = 'TODOS'
        else:
            nombre_agenda = seccion_agenda_df[(seccion_agenda_df['SERVICE'] == servicio_agenda) & 
                                              (seccion_agenda_df['SECTION'] == seccion_agenda) & 
                                              (seccion_agenda_df['MÉDICO'] == medico)]['NOMBRE_AGENDA'].unique()[0]

        registro = {
            "RUT_PACIENTE": rut_paciente,
            "TIPO_PREVISIÓN": tipo_prevision,
            "MODALIDAD_ATENCION": modalidad_atencion,
            "NÚMERO": numero_evento,
            "NOMBRE_AGENDA": nombre_agenda,
            "MOTIVO_CONSULTA": motivo_consulta,
            "PERIODICIDAD (DÍAS)": periodicidad,
            "MÁXIMO (DÍAS)": maximo_dias,
            "DEPENDENCIA": dependencias_list,
            "MEDICO": medico,
            "SERVICIO_AGENDA": servicio_agenda,
            "SECCION_AGENDA": seccion_agenda,
            "SOBRECUPOS": sobrecupos
        }

        data.append(registro)
        numero_evento += 1
        print("Evento agregado exitosamente.")

        otra_cita = input("¿Desea ingresar otra cita para este paciente? (s/n): ")
        if otra_cita.lower() != 's':
            break

# Función para editar eventos de un paciente
def editar_eventos_paciente():
    while True:
        ruts_disponibles = list(set(evento['RUT_PACIENTE'] for evento in data))

        if not ruts_disponibles:
            print("No hay rutas para editar.")
            return

        print("Seleccione el RUT del paciente que desea editar:")
        for i, rut in enumerate(ruts_disponibles):
            print(f"{i + 1}. {rut}")
        print(f"{len(ruts_disponibles) + 1}. Salir de edición")

        rut_seleccionado = int(input("Ingrese el número del RUT: ")) - 1

        if rut_seleccionado == len(ruts_disponibles):
            return

        rut_paciente = ruts_disponibles[rut_seleccionado]

        registros_paciente = [evento for evento in data if evento['RUT_PACIENTE'] == rut_paciente]

        while True:
            df = pd.DataFrame(registros_paciente)
            print(df)

            print("Seleccione el número del evento que desea editar:")
            for i, registro in enumerate(registros_paciente):
                print(f"{i + 1}. Evento {registro['NÚMERO']}")
            print(f"{len(registros_paciente) + 1}. Volver a seleccionar RUT")
            print(f"{len(registros_paciente) + 2}. Salir de edición")

            evento_seleccionado = int(input("Ingrese el número del evento: ")) - 1

            if evento_seleccionado == len(registros_paciente):
                break
            elif evento_seleccionado == len(registros_paciente) + 1:
                return

            registro_editar = registros_paciente[evento_seleccionado]

            while True:
                print("Seleccione el campo que desea modificar:")
                print("1. Servicio")
                print("2. Sección")
                print("3. Modalidad de Atención")
                print("4. Motivo de Consulta")
                print("5. Médico")
                print("6. Sobrecupos")
                print("7. Volver a seleccionar evento")
                print("8. Volver a seleccionar RUT")
                print("9. Salir de edición")
                campo_seleccionado = int(input("Ingrese el número del campo: "))

                if campo_seleccionado == 1:
                    print("Seleccione el nuevo servicio de la agenda de las siguientes opciones:")
                    for i, servicio in enumerate(servicios_agenda_unicos):
                        print(f"{i + 1}. {servicio}")
                    servicio_seleccionado = int(input("Ingrese el número del servicio: "))
                    servicio_agenda = servicios_agenda_unicos[servicio_seleccionado - 1]
                    registro_editar['SERVICIO_AGENDA'] = servicio_agenda

                    secciones_agenda_filtradas = seccion_agenda_df[seccion_agenda_df['SERVICE'] == servicio_agenda]['SECTION'].unique()
                    print("Seleccione la nueva sección de la agenda de las siguientes opciones:")
                    for i, seccion in enumerate(secciones_agenda_filtradas):
                        print(f"{i + 1}. {seccion}")
                    seccion_seleccionada = int(input("Ingrese el número de la sección: "))
                    seccion_agenda = secciones_agenda_filtradas[seccion_seleccionada - 1]
                    registro_editar['SECCION_AGENDA'] = seccion_agenda

                    medicos_filtrados = seccion_agenda_df[(seccion_agenda_df['SERVICE'] == servicio_agenda) &
                                                          (seccion_agenda_df['SECTION'] == seccion_agenda)]['MÉDICO'].unique()
                    medicos_filtrados = list(medicos_filtrados) + ['TODOS']
                    print("Seleccione el nuevo médico de las siguientes opciones:")
                    for i, medico in enumerate(medicos_filtrados):
                        print(f"{i + 1}. {medico}")
                    medico_seleccionado = int(input("Ingrese el número del médico: "))
                    medico = medicos_filtrados[medico_seleccionado - 1]
                    registro_editar['MEDICO'] = medico

                    if medico == 'TODOS':
                        nombre_agenda = 'TODOS'
                    else:
                        nombre_agenda = seccion_agenda_df[(seccion_agenda_df['SERVICE'] == servicio_agenda) & 
                                                          (seccion_agenda_df['SECTION'] == seccion_agenda) & 
                                                          (seccion_agenda_df['MÉDICO'] == medico)]['NOMBRE_AGENDA'].unique()[0]
                    registro_editar['NOMBRE_AGENDA'] = nombre_agenda

                elif campo_seleccionado == 2:
                    servicio_agenda = registro_editar['SERVICIO_AGENDA']
                    secciones_agenda_filtradas = seccion_agenda_df[seccion_agenda_df['SERVICE'] == servicio_agenda]['SECTION'].unique()
                    print("Seleccione la nueva sección de la agenda de las siguientes opciones:")
                    for i, seccion in enumerate(secciones_agenda_filtradas):
                        print(f"{i + 1}. {seccion}")
                    seccion_seleccionada = int(input("Ingrese el número de la sección: "))
                    seccion_agenda = secciones_agenda_filtradas[seccion_seleccionada - 1]
                    registro_editar['SECCION_AGENDA'] = seccion_agenda

                    medicos_filtrados = seccion_agenda_df[(seccion_agenda_df['SERVICE'] == servicio_agenda) &
                                                          (seccion_agenda_df['SECTION'] == seccion_agenda)]['MÉDICO'].unique()
                    medicos_filtrados = list(medicos_filtrados) + ['TODOS']
                    print("Seleccione el nuevo médico de las siguientes opciones:")
                    for i, medico in enumerate(medicos_filtrados):
                        print(f"{i + 1}. {medico}")
                    medico_seleccionado = int(input("Ingrese el número del médico: "))
                    medico = medicos_filtrados[medico_seleccionado - 1]
                    registro_editar['MEDICO'] = medico

                    if medico == 'TODOS':
                        nombre_agenda = 'TODOS'
                    else:
                        nombre_agenda = seccion_agenda_df[(seccion_agenda_df['SERVICE'] == servicio_agenda) & 
                                                          (seccion_agenda_df['SECTION'] == seccion_agenda) & 
                                                          (seccion_agenda_df['MÉDICO'] == medico)]['NOMBRE_AGENDA'].unique()[0]
                    registro_editar['NOMBRE_AGENDA'] = nombre_agenda

                elif campo_seleccionado == 3:
                    nueva_modalidad = seleccionar_opcion(["PRESENCIAL", "VIDEOLLAMADA", "FONOLLAMADA", "TODOS"], "Seleccione la nueva modalidad de atención:")
                    registro_editar['MODALIDAD_ATENCION'] = nueva_modalidad

                elif campo_seleccionado == 4:
                    nuevo_motivo = seleccionar_opcion(opciones_motivo_consulta, "Seleccione el nuevo motivo de consulta:")
                    registro_editar['MOTIVO_CONSULTA'] = nuevo_motivo

                elif campo_seleccionado == 5:
                    servicio_agenda = registro_editar['SERVICIO_AGENDA']
                    seccion_agenda = registro_editar['SECCION_AGENDA']
                    medicos_filtrados = seccion_agenda_df[(seccion_agenda_df['SERVICE'] == servicio_agenda) &
                                                          (seccion_agenda_df['SECTION'] == seccion_agenda)]['MÉDICO'].unique()
                    medicos_filtrados = list(medicos_filtrados) + ['TODOS']
                    print("Seleccione el nuevo médico de las siguientes opciones:")
                    for i, medico in enumerate(medicos_filtrados):
                        print(f"{i + 1}. {medico}")
                    medico_seleccionado = int(input("Ingrese el número del médico: "))
                    medico = medicos_filtrados[medico_seleccionado - 1]
                    registro_editar['MEDICO'] = medico

                    if medico == 'TODOS':
                        nombre_agenda = 'TODOS'
                    else:
                        nombre_agenda = seccion_agenda_df[(seccion_agenda_df['SERVICE'] == servicio_agenda) & 
                                                          (seccion_agenda_df['SECTION'] == seccion_agenda) & 
                                                          (seccion_agenda_df['MÉDICO'] == medico)]['NOMBRE_AGENDA'].unique()[0]
                    registro_editar['NOMBRE_AGENDA'] = nombre_agenda

                elif campo_seleccionado == 6:
                    nuevo_valor = int(input("Ingrese si se consideran sobrecupos (1 para sí, 0 para no): "))
                    registro_editar['SOBRECUPOS'] = nuevo_valor

                elif campo_seleccionado == 7:
                    break
                elif campo_seleccionado == 8:
                    break
                elif campo_seleccionado == 9:
                    return
                else:
                    print("Opción no válida, intente nuevamente.")

                print("Registro actualizado exitosamente.")
                otra_modificacion = input("¿Desea modificar otro campo? (s/n): ")
                if otra_modificacion.lower() != 's':
                    break

# Función para eliminar un evento específico
def eliminar_evento(rut_paciente):
    registros_paciente = [evento for evento in data if evento['RUT_PACIENTE'] == rut_paciente]

    while True:
        df = pd.DataFrame(registros_paciente)
        print(df)

        print("Seleccione el número del evento que desea eliminar:")
        for i, registro in enumerate(registros_paciente):
            print(f"{i + 1}. Evento {registro['NÚMERO']}")
        print(f"{len(registros_paciente) + 1}. Volver a seleccionar RUT")
        print(f"{len(registros_paciente) + 2}. Salir de eliminación")

        evento_seleccionado = int(input("Ingrese el número del evento: ")) - 1

        if evento_seleccionado == len(registros_paciente):
            break
        elif evento_seleccionado == len(registros_paciente) + 1:
            return

        evento_eliminar = registros_paciente[evento_seleccionado]
        data.remove(evento_eliminar)
        print("Evento eliminado exitosamente.")

        otra_eliminacion = input("¿Desea eliminar otro evento para este paciente? (s/n): ")
        if otra_eliminacion.lower() != 's':
            break

# Función para eliminar todos los eventos de un paciente
def eliminar_paciente(rut_paciente):
    data[:] = [evento for evento in data if evento['RUT_PACIENTE'] != rut_paciente]
    print("Todos los eventos del paciente han sido eliminados exitosamente.")

# Función para eliminar un evento o todos los eventos de un paciente
def eliminar():
    while True:
        ruts_disponibles = list(set(evento['RUT_PACIENTE'] for evento in data))

        if not ruts_disponibles:
            print("No hay rutas para eliminar.")
            return

        print("Seleccione el RUT del paciente que desea eliminar:")
        for i, rut in enumerate(ruts_disponibles):
            print(f"{i + 1}. {rut}")
        print(f"{len(ruts_disponibles) + 1}. Salir de eliminación")

        rut_seleccionado = int(input("Ingrese el número del RUT: ")) - 1

        if rut_seleccionado == len(ruts_disponibles):
            return

        rut_paciente = ruts_disponibles[rut_seleccionado]

        print("Seleccione la acción a realizar:")
        print("1. Eliminar un evento específico")
        print("2. Eliminar todos los eventos del paciente")
        print("3. Volver a seleccionar RUT")
        print("4. Salir de eliminación")

        accion = int(input("Ingrese el número de la acción: "))

        if accion == 1:
            eliminar_evento(rut_paciente)
        elif accion == 2:
            eliminar_paciente(rut_paciente)
        elif accion == 3:
            continue
        elif accion == 4:
            return
        else:
            print("Opción no válida, intente nuevamente.")

# Función para mostrar los registros en forma de DataFrame
def mostrar_registros():
    df = pd.DataFrame(data)
    print(df)

# Función para guardar los datos en un archivo Excel
def guardar_en_excel():
    df = pd.DataFrame(data)
    columnas = [
        "RUT_PACIENTE",
        "TIPO_PREVISIÓN",
        "MODALIDAD_ATENCION",
        "NÚMERO",
        "NOMBRE_AGENDA",
        "MOTIVO_CONSULTA",
        "PERIODICIDAD (DÍAS)",
        "MÁXIMO (DÍAS)",
        "DEPENDENCIA",
        "MEDICO",
        "SERVICIO_AGENDA",
        "SECCION_AGENDA",
        "SOBRECUPOS"
    ]
    df = df[columnas]
    df.to_excel('registros_pacientes.xlsx', index=False)
    print("Datos guardados en 'registros_pacientes.xlsx'")

# Ejemplo de uso
while True:
    print("1. Agregar nuevo paciente")
    print("2. Editar rutas de paciente")
    print("3. Mostrar registros")
    print("4. Eliminar")
    print("5. Guardar y salir")
    opcion = input("Seleccione una opción: ")
    
    if opcion == '1':
        rut_paciente = input("Ingrese RUT del paciente: ")
        agregar_eventos_paciente(rut_paciente)
    elif opcion == '2':
        if data:
            editar_eventos_paciente()
        else:
            print("No hay rutas disponibles para editar.")
    elif opcion == '3':
        mostrar_registros()
    elif opcion == '4':
        if data:
            eliminar()
        else:
            print("No hay rutas disponibles para eliminar.")
    elif opcion == '5':
        guardar_en_excel()
        break
    else:
        print("Opción no válida, intente nuevamente.")