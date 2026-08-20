#%%=======================================================Import Libreries===============================================

#Modeling and optimization.
import gurobipy as gp
from gurobipy import GRB

#Data manipulation and analysis.
import pandas as pd

#Numerical computing.
import numpy as np

#Instance generation shared with the deterministic model.
import Instancias

#Time registration.
import time

#Random number generation.
import random as rand

#Playing sounds in Windows.
import winsound

#Mathematical operations.
import math

#Data visualization.
import matplotlib.pyplot as plt 

#Warning control.
import warnings

#Operating System Interface
import os

#Create Excel
import openpyxl
#%%=======================================================Definición de parámetros========================================
da_Miope_Rutas = pd.DataFrame(columns=["F.O total","Total pacientes","Horizonte de tiempo","F.O por evento","Paciente","Patología","Llegada del paciente","Evento","Eventos Dependendiente","Eventos derivados","Eventos en espera", "Largo total","Largo promedio", "Desviación del largo", "Error total", "Error promedio", "Desviación del Error","Día asignado"])
da_resource_Rutas = pd.DataFrame(columns=["F.O total","Total pacientes","Horizonte de tiempo","F.O por evento","Paciente","Patología","Llegada del paciente","Evento","Eventos Dependendiente","Eventos derivados","Eventos en espera", "Largo total","Largo promedio", "Desviación del largo", "Error total", "Error promedio", "Desviación del Error","Día asignado"])
da_Miope_Normal = pd.DataFrame(columns=["F.O total","Total pacientes","Horizonte de tiempo","F.O por evento","Paciente","Patología","Llegada del paciente","Evento","Eventos Dependendiente","Eventos derivados","Eventos en espera", "Largo total","Largo promedio", "Desviación del largo", "Error total", "Error promedio", "Desviación del Error","Día asignado"])


da_Miope_Rutas2 = pd.DataFrame(columns=["F.O total","Total pacientes","Horizonte de tiempo","F.O por Paciente","Paciente","Patología","Llegada del paciente","Eventos derivados","Eventos en espera", "Largo total","Largo promedio", "Desviación del largo", "Error total", "Error promedio", "Desviación del Error"])
da_resource_Rutas2 = pd.DataFrame(columns=["F.O total","Total pacientes","Horizonte de tiempo","F.O por Paciente","Paciente","Patología","Llegada del paciente","Eventos derivados","Eventos en espera", "Largo total","Largo promedio", "Desviación del largo", "Error total", "Error promedio", "Desviación del Error"])
da_Miope_Normal2 = pd.DataFrame(columns=["F.O total","Total pacientes","Horizonte de tiempo","F.O por Paciente","Paciente","Patología","Llegada del paciente","Eventos derivados","Eventos en espera", "Largo total","Largo promedio", "Desviación del largo", "Error total", "Error promedio", "Desviación del Error"])


da_time_ASAPS= pd.DataFrame(columns=["Tiempo total"])
da_time_Resource= pd.DataFrame(columns=["Tiempo total"])
da_time_PSS= pd.DataFrame(columns=["Tiempo total"])
#%%=======================================================Definición de parámetros========================================
#Parámetros

# Usa exactamente el mismo generador y la misma iteración del modelo determinista.
iteración = 2
lambda_rates, patologias, recurso, R, recursoT, recursoTInv, recursoTNorm, D, D_fict, Dprim, ruta_patologia, P, dl, M = Instancias.generar_instancia(iteración)

# Conserva una copia de la disponibilidad inicial para el reporte final.
recursoT_exp = recursoT.copy()

# Parámetros auxiliares propios de los algoritmos.
Nb = 1
Semanas = (len(D_fict) // 7) + 2

print(dl)
print('la cantidad de pacientes a atender es', len(P))

# Matriz de dependencias
A = {}
for r in patologias:
    A[r] = pd.DataFrame(columns=ruta_patologia[r]['NÚMERO'].unique(), index=ruta_patologia[r]['NÚMERO'].unique())
    for w in ruta_patologia[r]['NÚMERO'].unique():
        for h in ruta_patologia[r]['NÚMERO'].unique():
            A[r].loc[w, h] = 0
    for n in ruta_patologia[r].index.tolist():
        if ruta_patologia[r]['DEPENDENCIA'][n] != 0:
            A[r].loc[ruta_patologia[r]['DEPENDENCIA'][n], ruta_patologia[r]['NÚMERO'][n]] = 1

# Conjuntos numéricos derivados de la instancia compartida
N = {}
for p in P:
    N[p] = ruta_patologia[dl.loc[p, 'Diagnóstico']]['NÚMERO'].unique()
    
N_d = {}
for cp in patologias:
    N_d[cp] = ruta_patologia[cp]['NÚMERO'].unique()

#---------------------------

n_route = {p: len(N[p]) for p in P}

#%%=======================================================Calendario=========================================================
calendario = {}

for o in range(Semanas):
    cols= pd.MultiIndex.from_tuples([[0],[1],[2],[3],[4],[5],[6]])
    calendario[o] = pd.DataFrame(columns= cols,index=range(Nb))
    
for o in range(Semanas):    
    for e in (range(Nb)): 
        for j in range(7):
            calendario[o].loc[e][j]=0
            
#%%=======================================================Función=============================================================
#Actualizar recurso      
def actualizar_recurso(d,n,p,R):
    for r in R:
        if recurso.loc[ruta_patologia[dl.loc[p,'Diagnóstico']].loc[n,'EVENTO'],r] == 1:
            recursoT.loc[d,r]-=1
    return recursoT

def F1(x0, x1, x2, x3, x4, d, R):
    todos_cumplen = True  # Suponemos que todos cumplen inicialmente
    for r in R:
        if recurso.loc[ruta_patologia[dl.loc[x3,'Diagnóstico']].loc[x4,'EVENTO'], r] == 1:
            if recursoT.loc[d, r] <= 0:
                todos_cumplen = False  # Si al menos uno no cumple, cambiamos a False
    if todos_cumplen:
        return True
    else:
        return False


# Definición de la función para asignar un evento
def asignar_evento(p, n, dia_inicio):
    for o in range(Semanas):
        for d in D:
            for e in range(Nb):
                if d >= dia_inicio + ruta_patologia[dl.loc[p, 'Diagnóstico']].loc[n, 'PERIODICIDAD (DÍAS)']:
                    if d >= 7 * o and d <= 7 * o + 6:
                        t = d - (7 * o)
                        if F1(o, e, t, p, n, d, R):
                            eventos_programados.append((p, n, d))  # paciente, evento, día
                            eventos_ord_programados[p].remove((p, n))
                            actualizar_recurso(d,n,p,R)
                            return True
    return False

def derivar (p, n, dia_inicio):
        if dia_inicio + ruta_patologia[dl.loc[p, 'Diagnóstico']].loc[n, 'PERIODICIDAD (DÍAS)'] >=len(D):
            eventos_derivados.append((p,n,len(D)))
            eventos_programados.append((p, n, len(D)))
            eventos_ord_programados[p].remove((p, n))
        else:
            eventos_derivados.append((p,n,dia_inicio + ruta_patologia[dl.loc[p, 'Diagnóstico']].loc[n, 'PERIODICIDAD (DÍAS)']))
            eventos_programados.append((p, n, dia_inicio + ruta_patologia[dl.loc[p, 'Diagnóstico']].loc[n, 'PERIODICIDAD (DÍAS)']))
            eventos_ord_programados[p].remove((p, n))
        return True
        
#Recuperar día de atención paciente
def recuperar_paciente(p, n):
    for pp, nn, dd in eventos_programados:
        if p == pp and n == nn:
            return(dd)

def requerimientos(p, n):
    eventos_requerimientos=[]
    for nn in N[p]:
        if n != nn and A[dl.loc[p,'Diagnóstico']].loc[nn,n]==1:
            eventos_requerimientos.append((p,nn))
    return eventos_requerimientos  # Muestre eventos dependientes   

#------------------------------------------------------------Inverso-----------------------------------------------------------  

def obtener_rango_dias(p, n, dia_inicio, iterador):
    rango_inferior = min(dia_inicio + iterador + ruta_patologia[dl.loc[p, 'Diagnóstico']].loc[n, 'PERIODICIDAD (DÍAS)'],len(D))
    rango_superior = min(dia_inicio + iterador + ruta_patologia[dl.loc[p, 'Diagnóstico']].loc[n, 'MÁXIMO (DÍAS)']+1, len(D)) #+1 para que incluya el día
    if rango_inferior == rango_superior:
        return range(rango_inferior, rango_superior + 1)
    else:
        return range(rango_inferior, rango_superior)
    
def actualizar_recurso2(d,n,p,R):
    for r in R:
        if recurso.loc[ruta_patologia[dl.loc[p,'Diagnóstico']].loc[n,'EVENTO'],r] == 1:
            recursoTInv.loc[d,r]-=1
    return recursoTInv


def F2(x3, x4, d, recurso_maximo):
    if recursoTInv.loc[d, recurso_maximo] > 0:
        return True
    else:
        return False

def asignar_evento2(p, n, dia_inicio):
    iterador = 0
    while True:  # Bucle externo para continuar buscando hasta que se hayan asignado todos los eventos o se hayan agotado los días
        rango = obtener_rango_dias(p, n, dia_inicio, iterador)
        recursos_menores = {}  # Diccionario para almacenar los cuellos de botella menores por recurso para cada día
        if iterador + dia_inicio + ruta_patologia[dl.loc[p, 'Diagnóstico']].loc[n, 'PERIODICIDAD (DÍAS)'] >= len(D):
            break  # Si la suma de los días excede el límite, salir del bucle externo
        for d in rango:
            recursos_disponibles = []  # Lista para almacenar los recursos disponibles para este día
            for r in R:
                if recurso.loc[ruta_patologia[dl.loc[p, 'Diagnóstico']].loc[n, 'EVENTO'], r] == 1:
                    cuello_de_botella_actual = recursoTInv.loc[d, r]
                    if cuello_de_botella_actual >= 0:
                        recursos_disponibles.append((r, cuello_de_botella_actual))

            if recursos_disponibles:  # Si hay recursos disponibles para este día
                recurso_menor = min(recursos_disponibles, key=lambda x: x[1])  # Encontrar el recurso con el menor cuello de botella
                recursos_menores[d] = recurso_menor  # Almacenar el recurso con el menor cuello de botella para este día

        # Encontrar el día con el mayor recurso entre los menores
        if recursos_menores:
            d_max_recurso_menor = max(recursos_menores, key=lambda x: recursos_menores[x][1])
            recurso_maximo = recursos_menores[d_max_recurso_menor][0]
            if recurso_maximo is not None:
                if F2(p, n, d_max_recurso_menor, recurso_maximo):
                    eventos_programados.append((p, n, d_max_recurso_menor))  # paciente, evento, día
                    eventos_ord_programados[p].remove((p, n))
                    actualizar_recurso2(d_max_recurso_menor, n, p, R)
                    return True
        iterador += 1  # Incrementar el iterador para buscar en el siguiente día
    return False

def derivar2 (p, n, dia_inicio):
        if dia_inicio + ruta_patologia[dl.loc[p, 'Diagnóstico']].loc[n, 'PERIODICIDAD (DÍAS)'] >=len(D):
            eventos_derivados.append((p,n,len(D)))
            eventos_programados.append((p, n, len(D)))
            eventos_ord_programados[p].remove((p, n))
        else:
            eventos_derivados.append((p,n,dia_inicio + ruta_patologia[dl.loc[p, 'Diagnóstico']].loc[n, 'PERIODICIDAD (DÍAS)']))
            eventos_programados.append((p, n, dia_inicio + ruta_patologia[dl.loc[p, 'Diagnóstico']].loc[n, 'PERIODICIDAD (DÍAS)']))
            eventos_ord_programados[p].remove((p, n))
        return True
 
#------------------------------------------------------------Normal-----------------------------------------------------------
def actualizar_recurso3(d,n,p,R):
    for r in R:
        if recurso.loc[ruta_patologia[dl.loc[p,'Diagnóstico']].loc[n,'EVENTO'],r] == 1:
            recursoTNorm.loc[d,r]-=1
    return recursoTNorm

    
#%%=======================================================Inicio Algoritmo ASAPS=============================================================
eventos_programados = [] # Inicializa una lista vacía para almacenar los eventos programados
eventos_ord_programados={}
eventos_derivados=[]

start_time_ASAP = time.time()

for p in dl.index:
    eventos_ord_programados[p] = []
    for n in N[p]:
        eventos_ord_programados[p].append((p,n)) #me da el orden de los eventos
        
# Ordenar eventos por la menor periodicidad
for p in dl.index:
    eventos_ord_programados[p].sort(key=lambda event: ruta_patologia[dl.loc[event[0], 'Diagnóstico']].loc[event[1], 'PERIODICIDAD (DÍAS)'])

        
# Ahora, puedes iterar a través del diccionario para asignar los eventos
for p in dl.index:
    while len(eventos_ord_programados[p]) > 0:
        evento_asignado = False
        for p,n in eventos_ord_programados[p]:
            dependencia = ruta_patologia[dl.loc[p, 'Diagnóstico']].loc[n, 'DEPENDENCIA']
            if dependencia == 0 or dependencia in [event[1] for event in eventos_programados if event[0] == p]:
                if dependencia == 0:
                    dia_inicio = dl.loc[p, 'día de llegada']
                else:
                    evento_anterior = next((event for event in eventos_programados if event[0] == p and event[1] == dependencia), None)
                    dia_inicio = evento_anterior[2] if evento_anterior else dl.loc[p, 'día de llegada']
    
                if asignar_evento(p, n, dia_inicio):
                    evento_asignado = True
                else:
                    derivar(p, n, dia_inicio)
                    evento_asignado = True
    
        if not evento_asignado:
            break
        
#time to solve model
end_time_ASAP = time.time()
elapsed_time_ASAP = end_time_ASAP - start_time_ASAP

da_time_ASAPS.loc[len(da_time_ASAPS)]= (elapsed_time_ASAP)  

#%%=======================================================Se calculan excedente ASAPS=============================================================
# Inicializar un diccionario 
dias_excedidos = {}
dia_actual = {}

for p in dl.index:
    for n in N[p]:
        dependencia = ruta_patologia[dl.loc[p, 'Diagnóstico']].loc[n, 'DEPENDENCIA']
        dia_llegada = dl.loc[p, 'día de llegada']
        if dependencia == 0:
            dia_actual[(p,n)]=recuperar_paciente(p, n) #Se calcula los días en que fueron realizados los eventos
            if dia_actual[(p,n)] - dia_llegada >=  ruta_patologia[dl.loc[p, 'Diagnóstico']].loc[n, 'MÁXIMO (DÍAS)']:
                dias_excedidos[(p, n)] = dia_actual[(p,n)] - dia_llegada - ruta_patologia[dl.loc[p, 'Diagnóstico']].loc[n, 'MÁXIMO (DÍAS)']
            else:
                dias_excedidos[(p, n)] = 0
        else:
            dia_actual[(p,n)]= recuperar_paciente(p, n)-recuperar_paciente(p, dependencia) #Se calcula los días en que fueron realizados los eventos
            if dia_actual[(p,n)] >= ruta_patologia[dl.loc[p, 'Diagnóstico']].loc[n, 'MÁXIMO (DÍAS)']:
                dias_excedidos[(p, n)] = dia_actual[(p,n)]-ruta_patologia[dl.loc[p, 'Diagnóstico']].loc[n, 'MÁXIMO (DÍAS)']
            else:
                dias_excedidos[(p, n)] = 0
    
Fun_cua= gp.quicksum(dias_excedidos[(p, n)] for p in dl.index for n in N[p])**2+len(eventos_derivados)*M
Fun_Lin= gp.quicksum(dias_excedidos[(p, n)] for p in dl.index for n in N[p])+len(eventos_derivados)*M
            

#%%=======================================================Datos del Largo de espera ASAPS===========================================
#Largo total de los tiempos de espera de los pacientes.
Largo_List= {}
for p in P:
    for n in N[p]:
        dependencia = ruta_patologia[dl.loc[p, 'Diagnóstico']].loc[n, 'DEPENDENCIA']
        dia_llegada = dl.loc[p, 'día de llegada'] 
        if dependencia == 0:
            Largo_List[(p,n)] = recuperar_paciente(p, n) - dia_llegada
            # Largo_List.append(dia_inicio)
        else:
            Largo_List[(p,n)] = recuperar_paciente(p, n) - recuperar_paciente(p, dependencia)
            # Largo_List.append(dia_inicio)
            
lista_dias={}
for p in P:
    for n in N[p]:
        if recuperar_paciente(p, n) in D:
            lista_dias[(p,n)]= recuperar_paciente(p, n)
        else:
            lista_dias[(p,n)]= recuperar_paciente(p, 1)


#%%=======================================================Datos del Error de espera ASAPS===========================================


derivados={}
espera={}
for p in dl.index:
    for n in N[p]:
        derivados[(p,n)]= 0
        espera[(p,n)]=0
        
for p in dl.index:
    for n in N[p]:
        for d in D_fict:
            print('Va en el primer algoritmo en el paciente',p)
            #--------------------------Derivados-------------------------------
            if (p, n, d) in eventos_derivados:
                if d in D:
                    derivados[(p,n)]= 1
                else:
                    espera[(p,n)] =1
            dependencia = ruta_patologia[dl.loc[p, 'Diagnóstico']].loc[n, 'DEPENDENCIA']
            #-------------------------Eventos----------------------------------
            if (p,n,d) in eventos_programados:
                Fun2= sum((dias_excedidos[(p, i)] +(derivados[(p,i)]+espera[(p,i)])*M) for i in N[p])
        #------------------------------------------------------------------
        #------------------------Datos_Largo-------------------------------

                Total_largo = max(lista_dias[(p,i)] for i in range(1,n+1))-dl.loc[p,'día de llegada']
                promedio_largo = (Total_largo/n)
                sum_cuadrados_diff = sum((Largo_List[(p,i)] - promedio_largo) ** 2 for i in range(1, n+1))
                desviacion_estandar_largo = (sum_cuadrados_diff / n) ** 0.5
        #------------------------------------------------------------------
        #----------------------Datos_Error---------------------------------
                Total_Error = sum(dias_excedidos[(p, i)] for i in range(1,n+1))
                promedio_Error = (Total_Error/n)
                sum_cuadrados_diff_E = sum((dias_excedidos[(p, i)] - promedio_Error) ** 2 for i in range(1, n+1))
                desviacion_estandar_Error = (sum_cuadrados_diff_E / n) ** 0.5
                Fun= dias_excedidos[(p,n)]+(derivados[(p,n)]+espera[(p,n)])*M
                
                da_Miope_Rutas.loc[len(da_Miope_Rutas)] = (Fun_Lin,len(P),len(D),Fun, p,dl.loc[p,'Diagnóstico'],( dl.loc[p,'día de llegada']), n, dependencia,derivados[(p,n)],espera[(p,n)], Total_largo, promedio_largo, desviacion_estandar_largo, Total_Error, promedio_Error,desviacion_estandar_Error,d)
        #-----------------------------Infor por paciente------------------------
        #------------------------Datos_Largo-------------------------------

                Total_largo2 = max(lista_dias[(p,i)] for i in N[p])-dl.loc[p,'día de llegada']
                promedio_largo2 = (Total_largo2/len(N[p]))
                sum_cuadrados_diff2 = sum((Largo_List[(p,i)] - promedio_largo2) ** 2 for i in N[p])
                desviacion_estandar_largo2 = (sum_cuadrados_diff2 / len(N[p])) ** 0.5
        #------------------------------------------------------------------
        #----------------------Datos_Error---------------------------------
                Total_Error2 = sum(dias_excedidos[(p, i)] for i in N[p])
                promedio_Error2 = (Total_Error2/len(N[p]))
                sum_cuadrados_diff_E2 = sum((dias_excedidos[(p, i)] - promedio_Error2) ** 2 for i in N[p])
                desviacion_estandar_Error2 = (sum_cuadrados_diff_E2 / len(N[p])) ** 0.5
 
    da_Miope_Rutas2.loc[len(da_Miope_Rutas2)] = (Fun_Lin,len(P),len(D),Fun2, p,dl.loc[p,'Diagnóstico'],( dl.loc[p,'día de llegada']),sum(derivados[(p,i)] for i in N[p]),sum(espera[(p,i)] for i in N[p]), Total_largo2, promedio_largo2, desviacion_estandar_largo2, Total_Error2, promedio_Error2,desviacion_estandar_Error2)

#%%=======================================================Inicio Algoritmo Alg Resource=============================================================
eventos_programados = [] # Inicializa una lista vacía para almacenar los eventos programados
eventos_ord_programados={}
eventos_derivados=[]

start_time_Resource = time.time()

for p in dl.index:
    eventos_ord_programados[p] = []
    for n in N[p]:
        eventos_ord_programados[p].append((p,n)) #me da el orden de los eventos
        
# Ordenar eventos por la menor periodicidad
for p in dl.index:
    eventos_ord_programados[p].sort(key=lambda event: ruta_patologia[dl.loc[event[0], 'Diagnóstico']].loc[event[1], 'PERIODICIDAD (DÍAS)'])

        
# Ahora, puedes iterar a través del diccionario para asignar los eventos
for p in dl.index:
    print("Va en el segundo algoritmo en el paciente", p)
    while len(eventos_ord_programados[p]) > 0:
        evento_asignado = False
        for p,n in eventos_ord_programados[p]:
            dependencia = ruta_patologia[dl.loc[p, 'Diagnóstico']].loc[n, 'DEPENDENCIA']
            if dependencia == 0 or dependencia in [event[1] for event in eventos_programados if event[0] == p]:
                if dependencia == 0:
                    dia_inicio = dl.loc[p, 'día de llegada']
                else:
                    evento_anterior = next((event for event in eventos_programados if event[0] == p and event[1] == dependencia), None)
                    dia_inicio = evento_anterior[2] if evento_anterior else dl.loc[p, 'día de llegada']
    
                if asignar_evento2(p, n, dia_inicio):
                    evento_asignado = True
                else:
                    derivar2(p, n, dia_inicio)
                    evento_asignado = True
    
        if not evento_asignado:
            break
        
#time to solve model
end_time_Resource = time.time()
elapsed_time_Resource = end_time_Resource - start_time_Resource

da_time_Resource.loc[len(da_time_Resource)]= (elapsed_time_Resource)  


#%%=======================================================Se calculan excedente Alg Resource=============================================================
# Inicializar un diccionario 
dias_excedidos = {}
dia_actual = {}

for p in P:
    for n in N[p]:
        dependencia = ruta_patologia[dl.loc[p, 'Diagnóstico']].loc[n, 'DEPENDENCIA']
        dia_llegada = dl.loc[p, 'día de llegada']
        if dependencia == 0:
            dia_actual[(p,n)]=recuperar_paciente(p, n) #Se calcula los días en que fueron realizados los eventos
            if dia_actual[(p,n)] - dia_llegada >=  ruta_patologia[dl.loc[p, 'Diagnóstico']].loc[n, 'MÁXIMO (DÍAS)']:
                dias_excedidos[(p, n)] = dia_actual[(p,n)] - dia_llegada - ruta_patologia[dl.loc[p, 'Diagnóstico']].loc[n, 'MÁXIMO (DÍAS)']
            else:
                dias_excedidos[(p, n)] = 0
        else:
            dia_actual[(p,n)]= recuperar_paciente(p, n)-recuperar_paciente(p, dependencia) #Se calcula los días en que fueron realizados los eventos
            if dia_actual[(p,n)] >= ruta_patologia[dl.loc[p, 'Diagnóstico']].loc[n, 'MÁXIMO (DÍAS)']:
                dias_excedidos[(p, n)] = dia_actual[(p,n)]-ruta_patologia[dl.loc[p, 'Diagnóstico']].loc[n, 'MÁXIMO (DÍAS)']
            else:
                dias_excedidos[(p, n)] = 0
                
Fun_cua= gp.quicksum(dias_excedidos[(p, n)] for p in P for n in N[p])**2+len(eventos_derivados)*M
Fun_Lin= gp.quicksum(dias_excedidos[(p, n)] for p in P for n in N[p])+len(eventos_derivados)*M

#%%=======================================================Datos del Largo de espera Alg Resource===========================================
#Largo total de los tiempos de espera de los pacientes.
Largo_List= {}
for p in P:
    for n in N[p]:
        dependencia = ruta_patologia[dl.loc[p, 'Diagnóstico']].loc[n, 'DEPENDENCIA']
        dia_llegada = dl.loc[p, 'día de llegada'] 
        if dependencia == 0:
            Largo_List[(p,n)] = recuperar_paciente(p, n) - dia_llegada
            # Largo_List.append(dia_inicio)
        else:
            Largo_List[(p,n)] = recuperar_paciente(p, n) - recuperar_paciente(p, dependencia)
            # Largo_List.append(dia_inicio)

lista_dias={}
for p in P:
    for n in N[p]:
        if recuperar_paciente(p, n) in D:
            lista_dias[(p,n)]= recuperar_paciente(p, n)
        else:
            lista_dias[(p,n)]= recuperar_paciente(p, 1)


#%%=======================================================Datos del Error de espera Alg Resource===========================================

derivados={}
espera={}
for p in dl.index:
    for n in N[p]:
        derivados[(p,n)]= 0
        espera[(p,n)]=0
        
for p in dl.index:
    for n in N[p]:
        for d in range(len(D)+1000):  
            print('va en el segundo algoritmo en el paciente',p)
            #--------------------------Derivados-------------------------------
            if (p, n, d) in eventos_derivados:
                if d in D:
                    derivados[(p,n)]= 1
                else:
                    espera[(p,n)] =1
            dependencia = ruta_patologia[dl.loc[p, 'Diagnóstico']].loc[n, 'DEPENDENCIA']
            #-------------------------Eventos----------------------------------
            if (p,n,d) in eventos_programados:
                Fun2= sum((dias_excedidos[(p, i)] +(derivados[(p,i)]+espera[(p,i)])*M) for i in N[p])
        #------------------------------------------------------------------
        #------------------------Datos_Largo-------------------------------

                Total_largo = max(lista_dias[(p,i)] for i in range(1,n+1))-dl.loc[p,'día de llegada']
                promedio_largo = (Total_largo/n)
                sum_cuadrados_diff = sum((Largo_List[(p,i)] - promedio_largo) ** 2 for i in range(1, n+1))
                desviacion_estandar_largo = (sum_cuadrados_diff / n) ** 0.5
        #------------------------------------------------------------------
        #----------------------Datos_Error---------------------------------
                Total_Error = sum(dias_excedidos[(p, i)] for i in range(1,n+1))
                promedio_Error = (Total_Error/n)
                sum_cuadrados_diff_E = sum((dias_excedidos[(p, i)] - promedio_Error) ** 2 for i in range(1, n+1))
                desviacion_estandar_Error = (sum_cuadrados_diff_E / n) ** 0.5
                Fun= dias_excedidos[(p,n)]+(derivados[(p,n)]+espera[(p,n)])*M
                
                da_resource_Rutas.loc[len(da_resource_Rutas)] = (Fun_Lin,len(P),len(D),Fun, p,dl.loc[p,'Diagnóstico'],( dl.loc[p,'día de llegada']), n, dependencia,derivados[(p,n)],espera[(p,n)], Total_largo, promedio_largo, desviacion_estandar_largo, Total_Error, promedio_Error,desviacion_estandar_Error,d)
        #-----------------------------Infor por paciente------------------------
            #------------------------Datos_Largo-------------------------------

                Total_largo2 =  max(lista_dias[(p,i)] for i in N[p])-dl.loc[p,'día de llegada']
                promedio_largo2 = (Total_largo2/len(N[p]))
                sum_cuadrados_diff2 = sum((Largo_List[(p,i)] - promedio_largo2) ** 2 for i in N[p])
                desviacion_estandar_largo2 = (sum_cuadrados_diff2 /len(N[p])) ** 0.5
            #------------------------------------------------------------------
            #----------------------Datos_Error---------------------------------
                Total_Error2 = sum(dias_excedidos[(p, i)] for i in N[p])
                promedio_Error2 = (Total_Error2/len(N[p]))
                sum_cuadrados_diff_E2 = sum((dias_excedidos[(p, i)] - promedio_Error2) ** 2 for i in N[p])
                desviacion_estandar_Error2 = (sum_cuadrados_diff_E2 /len(N[p])) ** 0.5
                
    da_resource_Rutas2.loc[len(da_resource_Rutas2)] = (Fun_Lin,len(P),len(D),Fun2, p,dl.loc[p,'Diagnóstico'],( dl.loc[p,'día de llegada']),sum(derivados[(p,i)] for i in N[p]),sum(espera[(p,i)] for i in N[p]), Total_largo2, promedio_largo2, desviacion_estandar_largo2, Total_Error2, promedio_Error2,desviacion_estandar_Error2)

#%%=======================================================Inicio Algoritmo  Real=============================================================

patient = {i : (dl.loc[i,'día de llegada'],dl.loc[i,'Diagnóstico']) for i in P}

print(patient)
def rand_route(cp):
    dict_ = {}
    for n in N_d[cp] :
        dict_[n] = (ruta_patologia[cp].loc[n, 'DEPENDENCIA'], ruta_patologia[cp].loc[n, 'PERIODICIDAD (DÍAS)'], ruta_patologia[cp].loc[n, 'MÁXIMO (DÍAS)']) #dependencia, min, máx.
    return dict_

clinic_route = { i : rand_route(i) for i in patologias}


schedule = {t : [] for t in D_fict}
old_patient = {}


def update_schedule(t,p,D_fict, clinic_route,old_patient,recursoTNorm,recurso):
    for tt in range(t + clinic_route[patient[p][1]][old_patient[p][0]][1], len(D_fict)+20):
        if t == tt and tt in D:
            wait_time2 = 0
            while all(recursoTNorm.loc[tt, r] > 0 for r in R if recurso.loc[ruta_patologia[dl.loc[p, 'Diagnóstico']].loc[old_patient[p][0], 'EVENTO'], r] == 1) and p in old_patient and wait_time2 == 0:
                schedule[tt].append((p, old_patient[p][0]))
                actualizar_recurso3(tt,old_patient[p][0],p,R)
                eventos_programados.append((p, old_patient[p][0], tt))
                old_patient[p].remove(old_patient[p][0])
                wait_time2 = clinic_route[patient[p][1]][old_patient[p][0]][1]
                if old_patient[p] == []:
                    del old_patient[p]
                    
        elif  p in old_patient and tt in range(t + clinic_route[patient[p][1]][old_patient[p][0]][1], len(D)):
            if all(recursoTNorm.loc[tt, r] > 0 for r in R if recurso.loc[ruta_patologia[dl.loc[p, 'Diagnóstico']].loc[old_patient[p][0], 'EVENTO'], r] == 1):
                schedule[tt].append((p, old_patient[p][0]))
                eventos_programados.append((p, old_patient[p][0], tt))
                actualizar_recurso3(tt,old_patient[p][0],p,R)
                old_patient[p].remove(old_patient[p][0])
                if old_patient[p] == []:
                    del old_patient[p]
                break
            #26
        if  tt >= len(D):
            schedule[len(D)].append((p, old_patient[p][0]))
            eventos_derivados.append((p, old_patient[p][0], len(D)))
            eventos_programados.append((p, old_patient[p][0], len(D)))
            old_patient[p].remove(old_patient[p][0])
            if old_patient[p] == []:
                del old_patient[p]
            break
        
    return old_patient, recursoTNorm, eventos_programados

eventos_programados = []
eventos_derivados=[]

start_time_PSS = time.time()

for t in D_fict:
    for (p,n) in schedule[t]: #paciente, evento
        if p in old_patient:
            old_patient, recursoTNorm, eventos_programados = update_schedule(t,p,D_fict, clinic_route,old_patient,recursoTNorm,recurso)

    new_patient = [s for s in P if patient[s][0] == t]

    for p in new_patient:
        old_patient[p] = [i for i in clinic_route[patient[p][1]].keys()]
        
        old_patient, recursoTNorm, eventos_programados = update_schedule(t,p,D_fict, clinic_route,old_patient,recursoTNorm,recurso)

#time to solve model
end_time_PSS = time.time()
elapsed_time_PSS = end_time_PSS - start_time_PSS

da_time_PSS.loc[len(da_time_PSS)]= (elapsed_time_PSS)  
#%%=======================================================Se calculan excedente Algoritmo Normal=============================================================
# Inicializar un diccionario 
dias_excedidos = {}
dia_actual = {}

for p in P:
    for n in N[p]:
        dependencia = ruta_patologia[dl.loc[p, 'Diagnóstico']].loc[n, 'DEPENDENCIA']
        dia_llegada = dl.loc[p, 'día de llegada']
        if dependencia == 0:
            dia_actual[(p,n)]=recuperar_paciente(p, n) #Se calcula los días en que fueron realizados los eventos
            if dia_actual[(p,n)] - dia_llegada >=  ruta_patologia[dl.loc[p, 'Diagnóstico']].loc[n, 'MÁXIMO (DÍAS)']:
                dias_excedidos[(p, n)] = dia_actual[(p,n)] - dia_llegada - ruta_patologia[dl.loc[p, 'Diagnóstico']].loc[n, 'MÁXIMO (DÍAS)']
            else:
                dias_excedidos[(p, n)] = 0
        else:
            dia_actual[(p,n)]= recuperar_paciente(p, n)-recuperar_paciente(p, dependencia) #Se calcula los días en que fueron realizados los eventos
            if dia_actual[(p,n)] >= ruta_patologia[dl.loc[p, 'Diagnóstico']].loc[n, 'MÁXIMO (DÍAS)']:
                dias_excedidos[(p, n)] = dia_actual[(p,n)]-ruta_patologia[dl.loc[p, 'Diagnóstico']].loc[n, 'MÁXIMO (DÍAS)']
            else:
                dias_excedidos[(p, n)] = 0

Fun_cua= gp.quicksum(dias_excedidos[(p, n)] for p in P for n in N[p])**2+len(eventos_derivados)*M
Fun_Lin= gp.quicksum(dias_excedidos[(p, n)] for p in P for n in N[p])+len(eventos_derivados)*M
        
#%%=======================================================Datos del Largo de espera Algoritmo Normal===========================================
#Largo total de los tiempos de espera de los pacientes.
Largo_List= {}
for p in P:
    for n in N[p]:
        dependencia = ruta_patologia[dl.loc[p, 'Diagnóstico']].loc[n, 'DEPENDENCIA']
        dia_llegada = dl.loc[p, 'día de llegada'] 
        if dependencia == 0:
            Largo_List[(p,n)] = recuperar_paciente(p, n) - dia_llegada
        else:
            Largo_List[(p,n)] = recuperar_paciente(p, n) - recuperar_paciente(p, dependencia)

            
lista_dias={}
for p in P:
    for n in N[p]:
        if recuperar_paciente(p, n) in D:
            lista_dias[(p,n)]= recuperar_paciente(p, n)
        else:
            lista_dias[(p,n)]= recuperar_paciente(p, 1)
            
#%%=======================================================Datos del Error de espera Algoritmo Normal===========================================

derivados={}
espera={}
for p in dl.index:
    for n in N[p]:
        derivados[(p,n)]= 0
        espera[(p,n)]=0
                
for p in dl.index:
    for n in N[p]:
        for d in range(len(D)+1000):
            print('va en el último algoritmo en el paciente',p)
            #--------------------------Derivados-------------------------------
            if (p, n, d) in eventos_derivados:
                if d in D:
                    derivados[(p,n)]= 1
                else:
                    espera[(p,n)] =1
            dependencia = ruta_patologia[dl.loc[p, 'Diagnóstico']].loc[n, 'DEPENDENCIA']
            #-------------------------Eventos----------------------------------
            if (p,n,d) in eventos_programados:
                Fun2= sum(dias_excedidos[(p,i)]+(derivados[(p,i)]+espera[(p,i)])*M for i in N[p])
        #------------------------------------------------------------------
        #------------------------Datos_Largo-------------------------------

                Total_largo = max(lista_dias[(p,i)] for i in range(1,n+1))-dl.loc[p,'día de llegada']
                promedio_largo = (Total_largo/n)
                sum_cuadrados_diff = sum((Largo_List[(p,i)] - promedio_largo) ** 2 for i in range(1, n+1))
                desviacion_estandar_largo = (sum_cuadrados_diff / n) ** 0.5
        #------------------------------------------------------------------
        #----------------------Datos_Error---------------------------------
                Total_Error = sum(dias_excedidos[(p, i)] for i in range(1,n+1))
                promedio_Error = (Total_Error/n)
                sum_cuadrados_diff_E = sum((dias_excedidos[(p, i)] - promedio_Error) ** 2 for i in range(1, n+1))
                desviacion_estandar_Error = (sum_cuadrados_diff_E / n) ** 0.5
                Fun= dias_excedidos[(p,n)]+(derivados[(p,n)]+espera[(p,n)])*M
                da_Miope_Normal.loc[len(da_Miope_Normal)] = (Fun_Lin,len(P),len(D),Fun, p,dl.loc[p,'Diagnóstico'],( dl.loc[p,'día de llegada']), n, dependencia,derivados[(p,n)],espera[(p,n)], Total_largo, promedio_largo, desviacion_estandar_largo, Total_Error, promedio_Error,desviacion_estandar_Error,d)
                
        #------------------------Infor por paciente------------------------------
        #------------------------Datos_Largo-------------------------------
                Total_largo2 = max(lista_dias[(p,i)] for i in N[p])-dl.loc[p,'día de llegada']
                promedio_largo2 = (Total_largo2/len(N[p]))
                sum_cuadrados_diff2 = sum((Largo_List[(p,i)] - promedio_largo2) ** 2 for i in N[p])
                desviacion_estandar_largo2 = (sum_cuadrados_diff2 /len(N[p])) ** 0.5
        #------------------------------------------------------------------
        #----------------------Datos_Error---------------------------------
                Total_Error2 = sum(dias_excedidos[(p, i)] for i in N[p])
                promedio_Error2 = (Total_Error2/len(N[p]))
                sum_cuadrados_diff_E2 = sum((dias_excedidos[(p, i)] - promedio_Error2) ** 2 for i in N[p])
                desviacion_estandar_Error2 = (sum_cuadrados_diff_E2 /len(N[p])) ** 0.5
                
    da_Miope_Normal2.loc[len(da_Miope_Normal2)] = (Fun_Lin,len(P),len(D),Fun2, p,dl.loc[p,'Diagnóstico'],( dl.loc[p,'día de llegada']),sum(derivados[(p,i)] for i in N[p]),sum(espera[(p,i)] for i in N[p]), Total_largo2, promedio_largo2, desviacion_estandar_largo2, Total_Error2, promedio_Error2,desviacion_estandar_Error2)
#%%=======================================================Excel===========================================

with pd.ExcelWriter("Algoritmos_0.5.xlsx") as writer:
    da_Miope_Rutas.to_excel(writer, sheet_name="ASAPS", index=False)
    da_resource_Rutas.to_excel(writer, sheet_name="Resource", index=False)
    da_Miope_Normal.to_excel(writer, sheet_name="PSS", index=False)
    
with pd.ExcelWriter("Algoritmos_Paciente_0.5.xlsx") as writer:
    da_Miope_Rutas2.to_excel(writer, sheet_name="ASAPS", index=False)
    da_resource_Rutas2.to_excel(writer, sheet_name="Resource", index=False)
    da_Miope_Normal2.to_excel(writer, sheet_name="PSS", index=False)
    
with pd.ExcelWriter("Otros datos_0.5.xlsx") as writer:
    da_time_ASAPS.to_excel(writer, sheet_name="Tiempo_ASAPS", index=False)
    da_time_Resource.to_excel(writer, sheet_name="Tiempo_Resource", index=False)
    da_time_PSS.to_excel(writer, sheet_name="Tiempo_PSS", index=False)
    recursoT.to_excel(writer, sheet_name='Recursos_ASAPS')
    recursoTInv.to_excel(writer, sheet_name='Recursos_Resource')
    recursoTNorm.to_excel(writer, sheet_name='Recursos_PSS')
    recursoT_exp.to_excel(writer, sheet_name='RecursoTotal')

    
