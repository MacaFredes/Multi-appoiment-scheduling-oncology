#Data manipulation and analysis.
import pandas as pd

#Numerical computing.
import numpy as np

import random

#%%=======================================================Importar información========================================
Demanda = pd.read_excel('Data/DEMANDA.xlsx', sheet_name='DEMANDA')

# y que no tengan ciertos valores específicos en PACIENTE
excluir_pacientes = [
    "RESERVA HEMATOLOGIA HEMATOLOGIA",
    "RESERVA PACIENTE TAMO",
    "RESERVA AGENDA MEDICA AGENDA",
    "DERIVACION GES RESERVA PRIMERA"
]

excluir_ruts = ["98.989.898-1"]

Demanda = Demanda[
    ~Demanda['ESTADO_CITA'].isin(['Cita Cancelada', 'Suple']) &
    Demanda['RUT_PACIENTE'].notna() &
    Demanda['MOTIVO_CONSULTA'].notna() &
    ~Demanda['PACIENTE'].isin(excluir_pacientes) &
    ~Demanda['RUT_PACIENTE'].isin(excluir_ruts)
]

# Convertir las columnas 'FECHA_CITA' y 'FECHA_AGENDAMIENTO' a tipo datetime
Demanda['FECHA_CITA'] = pd.to_datetime(Demanda['FECHA_CITA'], dayfirst=True)
Demanda['FECHA_AGENDAMIENTO'] = pd.to_datetime(Demanda['FECHA_AGENDAMIENTO'], dayfirst=True)

# Establecer el índice como el RUT
Demanda.set_index('RUT_PACIENTE', inplace=True)

Ruta = pd.DataFrame(columns=["RUT_PACIENTE","TIPO_PREVISIÓN","MODALIDAD_ATENCION", "NÚMERO","NOMBRE_AGENDA","MOTIVO_CONSULTA", "PERIODICIDAD (DÍAS)", "PROMEDIO", "MÁXIMO (DÍAS)", "DESVIACIÓN", "DEPENDENCIA","MEDICO" , "SERVICIO_AGENDA","SECCION_AGENDA", "SOBRECUPOS"])

#%%=====================================================Generación de rutas========================================

# Se obtienen los ruts de los pacientes
Rut = Demanda.index.unique()

# Ruta pacientes
ruta_paciente = {}  # Se genera un diccionario para separar las rutas por pacientes y patología

# Generar rutas por paciente y patología
for r in Rut:
    print(r)
    ruta_paciente[r] = pd.DataFrame(Demanda.loc[Demanda.index == r, Demanda.columns.tolist()]).reset_index(drop=True)
    # Ordenar cada DataFrame en el diccionario según la columna "FECHA_CITA"
    ruta_paciente[r].index = [i + 1 for i in ruta_paciente[r].index]
    ruta_paciente[r] = ruta_paciente[r].sort_values(by='FECHA_CITA')
    # Calcular los días hasta el próximo evento
    ruta_paciente[r]['DIAS_PROX_EVENTO'] = (ruta_paciente[r]['FECHA_CITA'].shift(-1) - ruta_paciente[r]['FECHA_CITA']).dt.days
    # Rellenar los valores NaN en 'DIAS_PROX_EVENTO' con 0
    ruta_paciente[r]['DIAS_PROX_EVENTO'] = ruta_paciente[r]['DIAS_PROX_EVENTO'].fillna(0)
    # Asegurarse de que DIAS_PROX_EVENTO no sea negativo
    ruta_paciente[r]['DIAS_PROX_EVENTO'] = ruta_paciente[r]['DIAS_PROX_EVENTO'].apply(lambda x: max(x, 0))

# Inicializar el diccionario para almacenar las duplas de valores de MOTIVO_CONSULTA
duplas_eventos = {}

for r in Rut:
    print(r)
    duplas = []
    for d in range(1, len(ruta_paciente[r].index)+1):  # Iterar hasta el penúltimo índice
        if d == 1:
            dias_prox_evento = (ruta_paciente[r].loc[d, 'FECHA_CITA'] - ruta_paciente[r].loc[d, 'FECHA_AGENDAMIENTO']).days
            dias_prox_evento = max(dias_prox_evento, 0)  # Asegurarse de que no sea negativo
            dupla = (
                'CONTACTO',
                ruta_paciente[r].loc[d, 'MOTIVO_CONSULTA'],
                dias_prox_evento
            )
        else:
            dupla = (
                ruta_paciente[r].loc[d, 'MOTIVO_CONSULTA'],
                ruta_paciente[r].loc[d + 1, 'MOTIVO_CONSULTA'] if d + 1 < len(ruta_paciente[r]) else None,
                ruta_paciente[r].loc[d, 'DIAS_PROX_EVENTO']
            )
        duplas.append(dupla)
    duplas_eventos[r] = duplas  # Agregar la lista de duplas al diccionario

# Mostrar las rutas de los pacientes y las duplas de eventos
for r in Rut:
    print(f"RUT: {r}")
    print(ruta_paciente[r])
    print("Duplas de eventos:", duplas_eventos[r])
    
#%%=======================================================Se almacena tiempo por duplas========================================
# Inicializar un diccionario para almacenar todos los valores de tiempo asociados con cada dupla (x, y)
tiempo = {}

# Iterar sobre cada paciente en la lista Rut
for r in Rut:
    for x, y, t in duplas_eventos[r]:
        # Obtener la dupla (x, y)
        dupla = (x, y)
        
        # Verificar si la dupla ya está en el diccionario tiempo
        if dupla in tiempo:
            # Si la dupla ya está en el diccionario, agregar el valor de tiempo a la lista existente
            tiempo[dupla].append(t)
        else:
            # Si la dupla no está en el diccionario, crear una nueva lista con el valor de tiempo
            tiempo[dupla] = [t]

#Mostrar el diccionario tiempo
# print(tiempo)

#%%=======================================================Se generan rutas========================================
tiempo_mínimo={}
promedio={}
tiempo_máximo={}
desviación={}
    
for r in Rut[:10]:
    for d in range(1,len(ruta_paciente[r].index)+1):
        if d < len(ruta_paciente[r].index):
            tiempos = tiempo[ruta_paciente[r].loc[d, 'MOTIVO_CONSULTA'], ruta_paciente[r].loc[d + 1, 'MOTIVO_CONSULTA']]
            tiempo_min = np.percentile(tiempos, 25)  # Percentil 25%
            tiempo_max = np.percentile(tiempos, 75)  # Percentil 75%
            
            tiempo_mínimo[(r,d)] = int(np.round(tiempo_min, decimals=0))
            promedio[(r,d)] = np.mean(tiempos)
            tiempo_máximo[(r,d)] = int(np.round(tiempo_max, decimals=0))
            desviación[(r,d)] = np.std(tiempos)
        else:
            tiempo_mínimo[(r,d)] = 0
            promedio[(r,d)] = 0
            tiempo_máximo[(r,d)] = 0
            desviación[(r,d)] = 0
        # Agregar datos a Ruta_LH
        Ruta.loc[len(Ruta)] = (r,ruta_paciente[r].loc[d, 'TIPO_PREVISION'],ruta_paciente[r].loc[d, 'TIPO_ATENCION'], d,ruta_paciente[r].loc[d, 'NOMBRE_AGENDA'],ruta_paciente[r].loc[d, 'MOTIVO_CONSULTA'], tiempo_mínimo.get((r, d), 0), promedio.get((r, d), 0), 
                                      tiempo_máximo.get((r, d), 0), desviación.get((r, d), 0), [d-1], ruta_paciente[r].loc[d, 'MEDICO'],ruta_paciente[r].loc[d, 'SERVICIO_AGENDA'],ruta_paciente[r].loc[d, 'SECCION_AGENDA'],random.choice([0, 1]))

with pd.ExcelWriter("Ruta1.xlsx") as writer:
    Ruta.to_excel(writer, sheet_name="Resultados", index=False)
    
