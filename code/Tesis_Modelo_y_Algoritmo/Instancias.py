#%%=======================================================Import Libreries===============================================
#Data manipulation and analysis.
import pandas as pd

#Numerical computing.
import numpy as np

#%%=======================================================Definición de parámetros========================================
###############################################Generación_de_ruta###############################################

class RutaMedica:
    def __init__(self):
        self.rutas = {
            "CANCER DE MAMAS": [
                {"EVENTO": "CONSULTA AMBULATORIA HEMATOLOGÍA", "PERIODICIDAD (DÍAS)": 0, "MÁXIMO (DÍAS)": 2, "DEPENDENCIA": 0},
                {"EVENTO": "IMAGEN", "PERIODICIDAD (DÍAS)": 1, "MÁXIMO (DÍAS)": 3, "DEPENDENCIA": 1},
                {"EVENTO": "LABORATORIO", "PERIODICIDAD (DÍAS)": 0, "MÁXIMO (DÍAS)": 4, "DEPENDENCIA": 2},
                {"EVENTO": "EXAMEN", "PERIODICIDAD (DÍAS)": 0, "MÁXIMO (DÍAS)": 2, "DEPENDENCIA": 1},
                {"EVENTO": "CIRUGIA", "PERIODICIDAD (DÍAS)": 1, "MÁXIMO (DÍAS)": 3, "DEPENDENCIA": 4}
            ]
            ,
            "CANCER DE TIROIDES": [
                {"EVENTO": "CONSULTA AMBULATORIA HEMATOLOGÍA", "PERIODICIDAD (DÍAS)": 0, "MÁXIMO (DÍAS)": 2, "DEPENDENCIA": 0},
                {"EVENTO": "IMAGEN", "PERIODICIDAD (DÍAS)": 1, "MÁXIMO (DÍAS)": 3, "DEPENDENCIA": 1},
                {"EVENTO": "LABORATORIO", "PERIODICIDAD (DÍAS)": 0, "MÁXIMO (DÍAS)": 4, "DEPENDENCIA": 2},
                {"EVENTO": "EXAMEN", "PERIODICIDAD (DÍAS)": 0, "MÁXIMO (DÍAS)": 2, "DEPENDENCIA": 1},
                {"EVENTO": "CIRUGIA", "PERIODICIDAD (DÍAS)": 1, "MÁXIMO (DÍAS)": 3, "DEPENDENCIA": 4}
            ]
        }
        
        # Crear DataFrame de las rutas
        self.Rutas = pd.DataFrame(
            [(patologia, evento["EVENTO"], evento["PERIODICIDAD (DÍAS)"], evento["MÁXIMO (DÍAS)"], evento["DEPENDENCIA"]) 
             for patologia, eventos in self.rutas.items() for evento in eventos],
            columns=["PATOLOGÍA", "EVENTO", "PERIODICIDAD (DÍAS)", "MÁXIMO (DÍAS)", "DEPENDENCIA"]
        )
        
        # Agregar la columna 'NÚMERO' que enumera los eventos dentro de cada patología
        self.Rutas['NÚMERO'] = self.Rutas.groupby('PATOLOGÍA').cumcount() + 1

    def obtener_patologias(self):
        return self.Rutas['PATOLOGÍA'].unique()

# Ejemplo de uso
generador = RutaMedica()
Rutas = generador.Rutas



###############################################Otras_instancias###############################################

  #Procedimientos
procedimientos=Rutas['EVENTO'].unique()

# Rango horizonte de tiempo
N_dias= 40

#Estimar rango del recurso
RMin =1 #Recurso minimo
RMax =2 #Recusro máximo

###############################################Control_llegada_pacientes###############################################

# lambda_rates = [3.8, 2.07] #x1
# lambda_rates = [5.7, 3.105] #x1.5
# lambda_rates = [1.9]  # x0.5
lambda_rates = [1.9, 1.035]  # x0.5

# Number of days befor of U
days = 1

# def distribuir_pacientes(total_pacientes):
#     """Distribuye el número total de pacientes según la proporción de lambda_rates."""
#     if total_pacientes == 1:
#         return [1, 0] if lambda_rates[0] > lambda_rates[1] else [0, 1]
    
#     pacientes_por_patologia = np.round((np.array(lambda_rates) / sum(lambda_rates)) * total_pacientes).astype(int)

#     while pacientes_por_patologia.sum() < total_pacientes:
#         pacientes_por_patologia[np.argmax(lambda_rates)] += 1  # Ajustar la asignación

#     return pacientes_por_patologia

def distribuir_pacientes(total_pacientes):
    """Distribuye el número total de pacientes según la proporción de lambda_rates."""
    if len(lambda_rates) == 1:  # Caso cuando solo existe una patología
        return [total_pacientes]
    elif total_pacientes == 1:  # Mantienes tu lógica original cuando hay más de una patología
        return [1, 0] if lambda_rates[0] > lambda_rates[1] else [0, 1]
    
    pacientes_por_patologia = np.round((np.array(lambda_rates) / sum(lambda_rates)) * total_pacientes).astype(int)

    while pacientes_por_patologia.sum() < total_pacientes:
        pacientes_por_patologia[np.argmax(lambda_rates)] += 1  # Ajustar la asignación

    return pacientes_por_patologia

def generar_poisson(iteracion, patologias):
    

    data = []
    np.random.seed(10 * iteracion)
    
    for idx, lambda_rate in enumerate(lambda_rates):
        arrivals = np.random.poisson(lambda_rate, days)
        for day, count in enumerate(arrivals, 1):
            for _ in range(count):
                data.append({'Diagnóstico': patologias[idx], 'día de llegada': day})

    dl = pd.DataFrame(data)
    dl = dl.sort_values(by=['día de llegada'])
    return dl

def generar_constante(iteracion, patologias):
    """Genera llegadas constantes de pacientes cada día hasta 'days'."""
    data = []
    total_diario = iteracion  # Total de pacientes por día

    for day in range(1, days + 1):
        pacientes_por_patologia = distribuir_pacientes(total_diario)
        for idx, count in enumerate(pacientes_por_patologia):
            for _ in range(count):
                data.append({'Diagnóstico': patologias[idx], 'día de llegada': day})

    dl = pd.DataFrame(data).sort_values(by=['día de llegada'])
    return dl

def generar_decreciente(iteracion, patologias):
    """Genera llegadas de pacientes en forma decreciente hasta 'days'."""
    data = []
    pacientes_hoy = iteracion+5  # Pacientes que llegan el primer día

    for day in range(1, days + 1):
        if pacientes_hoy <= 0:
            break  # Si ya no hay pacientes, termina

        pacientes_por_patologia = distribuir_pacientes(pacientes_hoy)
        for idx, count in enumerate(pacientes_por_patologia):
            for _ in range(count):
                data.append({'Diagnóstico': patologias[idx], 'día de llegada': day})

        pacientes_hoy -= max(2, iteracion // days)  # Resta pacientes de forma uniforme

    dl = pd.DataFrame(data).sort_values(by=['día de llegada'])
    return dl

def generar_creciente(iteracion, patologias):
    """Genera llegadas de pacientes en forma creciente hasta 'days'."""
    data = []
    
    for day in range(1, days + 1):
        pacientes_hoy = int(iteracion * (day / days))  # Aumenta con los días
        
        pacientes_por_patologia = distribuir_pacientes(pacientes_hoy)
        for idx, count in enumerate(pacientes_por_patologia):
            for _ in range(count):
                data.append({'Diagnóstico': patologias[idx], 'día de llegada': day})

    dl = pd.DataFrame(data).sort_values(by=['día de llegada'])
    return dl

def generar_instancia(iteracion):
###############################################Otras_instancias###############################################
      #Patologías
    patologias=Rutas['PATOLOGÍA'].unique()  
    
    #Ruta clínica
    ruta_patologia = {} #Se genera un diccionario para separar las rutas de la lista.
    for r in patologias:
        ruta_patologia[r]= pd.DataFrame(Rutas.loc[Rutas['PATOLOGÍA'] == r, Rutas.columns.tolist()]).reset_index(drop=True)
        ruta_patologia[r].index = [i + 1 for i in ruta_patologia[r].index]
        # print(ruta_patologia [r])
        
      # Días de atención
    D = np.array(range(N_dias))
    Dprim = np.array(range(N_dias, N_dias + 1))  # La secuencia adicional desde N_dias hasta N_dias+1
    D_fict = np.append(D, Dprim)
    
      #Costo asociado por si el paciente llega en el último día
    M=200
    
      #Recursos
    R=['Box']
    
      #Recursos que utiliza cada evento
    np.random.seed(10)
    recurso=pd.DataFrame(index=procedimientos)
    recurso ['Box']= np.random.randint(1,2, size=len(procedimientos))
    # print('\n \033[1m Recursos ocupados en los eventos \033[0m \n', recurso)
    
      #Recurso disponibles por día para algoritmo Miope Rutas
    np.random.seed(10)
    recursoT=pd.DataFrame(index=D)
    recursoT ['Box']= np.random.randint(RMin,RMax, size=len(D))
    # Crear copias independientes
    recursoTInv = recursoT.copy()
    recursoTNorm = recursoT.copy()
    
    print('\n \033[1m Recursos por día \033[0m \n', recursoT)
        
    dl = generar_constante(iteracion,patologias)  # Aquí generas 'dl' usando cualquier funcion
    P = np.array(dl.index)  # Aquí se crea 'P' a partir de 'dl'
        
    return lambda_rates, patologias, recurso, R, recursoT, recursoTInv, recursoTNorm, D, D_fict, Dprim, ruta_patologia, P, dl, M

print(generar_instancia(1))