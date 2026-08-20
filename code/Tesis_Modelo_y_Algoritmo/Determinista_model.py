#%%=======================================================Import Libreries===============================================

#Modeling and optimization.
import gurobipy as gp
from gurobipy import GRB

#Data manipulation and analysis.
import pandas as pd

import Instancias

#Time registration.
import time

#Operating System Interface
import os

import statistics
#%%=======================================================Definición de parámetros========================================
da_time= pd.DataFrame(columns=["Iteración","gap de optimalidad","Tiempo por paciente", "cantidad de pacientes", "total de tiempo"])

resumen_excel = pd.DataFrame(columns=["Iteración","Patients with unfinished routes","Total number of events on hold", "Rate of events on hold", "Patienst with events derived","Events derived","Rate of events derived","Patients with tardiness in first event","Total tardiness in first event (days)","Rate tardiness in first event","Patients with tardiness in his events","Total tardiness","Rate of tardiness"])
tardines_excel = pd.DataFrame(columns=["Iteración","TT promedio (días)","N_TT(cantidad_eventos)","Fi_TT","Max_TT"])
largo_excel = pd.DataFrame(columns=["Iteración","Patología","LT promedio","LT Max","LT Min"])

#%%=======================================================Definición de parámetros========================================
#Parámetros
iteración = 2
máx_iteración = 2

#%%=======================================================Generación función========================================

def procesar_iteracion(x,y,dl, lista_dias, ruta_patologia, N, D_fict, Dprim, eta, fi, M, F_O, P, iteración):
    da_Offline = pd.DataFrame(columns=["F.O total","Total pacientes","F.O por evento","Paciente","Patología","Llegada del paciente","Evento","Eventos Dependendiente","Eventos derivados","Eventos en espera", "Largo agendados","Largo promedio", "Desviación del largo", "Error total", "Error promedio", "Desviación del Error","Día asignado"])
    da_Offline2 = pd.DataFrame(columns=["F.O total","Total pacientes","F.O por Paciente","Paciente","Patología","Llegada del paciente","Eventos derivados","Eventos en espera","Largo agendados","Largo promedio", "Desviación del largo", "Error total", "Error promedio", "Desviación del Error"])
    for p in dl.index:
        for n in N[p]:
            for d in D_fict:
                dependencia = ruta_patologia[dl.loc[p, 'Diagnóstico']].loc[n, 'DEPENDENCIA']
                if (x[n,p,d].x)>=0.95 or (y[n,p,d].x)>=0.95:
                    #--------------Info_Largo-----------------
                    # print(max(lista_dias[(p, n)] for n in N[p]))
                    Total_largo = max(lista_dias[(p, i)] for i in range(1,n+1))-dl.loc[p,'día de llegada']
                    promedio_largo = (Total_largo/n)
                    sum_cuadrados_diff = sum((eta[i,p].x - promedio_largo) ** 2 for i in range(1, n+1))
                    desviacion_estandar_largo = (sum_cuadrados_diff / n) ** 0.5
                    #------------------------------------------
                    #------------Info_Error-------------------
                    Total_Error = sum(fi[i,p].x for i in range(1,n+1))
                    promedio_Error = (Total_Error/n)
                    sum_cuadrados_diff_E = sum((fi[i,p].x - promedio_Error) ** 2 for i in range(1, n+1))
                    desviacion_estandar_Error = (sum_cuadrados_diff_E/ n) ** 0.5
                    #------------Función_Obj_paciente-------------------
                    if d in Dprim:
                        Espera= y[n,p,d].x
                        derivados=0
    
                    else:
                        Espera= 0
                        derivados= y[n,p,d].x     #change FI
                    da_Offline.loc[len(da_Offline)] = (F_O,len(P),eta[n,p].x + M*y[n,p,d].x, p,dl.loc[p,'Diagnóstico'],( dl.loc[p,'día de llegada']), n, dependencia,derivados,Espera,Total_largo , promedio_largo, desviacion_estandar_largo, Total_Error, promedio_Error,desviacion_estandar_Error, d)
                    #--------------Info_Largo-----------------
                    Total_largo2 = max(lista_dias[(p, i)] for i in N[p])-dl.loc[p,'día de llegada']
                    promedio_largo2 = (Total_largo2/len(N[p]))
                    sum_cuadrados_diff2 = sum((eta[i,p].x - promedio_largo2) ** 2 for i in N[p])
                    desviacion_estandar_largo2 = (sum_cuadrados_diff2 / len(N[p])) ** 0.5
                    #------------------------------------------
                    #------------Info_Error-------------------
                    Total_Error2 = sum(fi[i,p].x for i in N[p])
                    promedio_Error2 = (Total_Error2/len(N[p]))
                    sum_cuadrados_diff_E2 = sum((fi[i,p].x - promedio_Error2) ** 2 for i in N[p])
                    desviacion_estandar_Error2 = (sum_cuadrados_diff_E2/ len(N[p])) ** 0.5
                #------------Función_Obj_paciente------------------- CHANGE fi
                    Fun_Obj2= sum(eta[n,p].x for n in N[p])+ sum(M*(y[n,p,d].x) for n in N[p] for d in D_fict)
            
        da_Offline2.loc[len(da_Offline2)] = (F_O,len(P),Fun_Obj2, p,dl.loc[p,'Diagnóstico'],( dl.loc[p,'día de llegada']),sum(y[i,p,d].x for i in N[p] for d in D),sum(y[i,p,d].x for i in N[p] for d in Dprim),Total_largo2, promedio_largo2, desviacion_estandar_largo2, Total_Error2, promedio_Error2,desviacion_estandar_Error2)

    return da_Offline, da_Offline2

#%%=======================================================Generación función========================================

# Diccionarios para almacenar los resultados de cada iteración
resultados_offline = {}
resultados_offline2 = {}

while iteración <= máx_iteración:

    lambda_rates, patologias, recurso, R, recursoT, recursoTInv, recursoTNorm, D, D_fict, Dprim, ruta_patologia, P, dl, M = Instancias.generar_instancia(iteración)
    
    print(dl)
    
     #Conjuntos númericos para las variables
    N={}
    for p in P:
        N[p]=ruta_patologia[dl.loc[p,'Diagnóstico']]['NÚMERO'].unique()
        
        
      # Conjunto de dependencias
    Dep = {}
    for p in dl.index:
        # Lista para almacenar las tuplas
        tuples_list = []
        max_dependencia_numero = None
        max_dependencia_valor = float('-inf')
        for n in N[p]:
            # Obtener los valores de las Series y almacenarlos como tuplas
            numero = ruta_patologia[dl.loc[p, 'Diagnóstico']].loc[n,'NÚMERO']
            dependencia = ruta_patologia[dl.loc[p, 'Diagnóstico']].loc[n,'DEPENDENCIA']
            if dependencia != 0:
                # Almacenar la tupla en la lista
                tuples_list.append((dependencia,numero))
            # Actualizar el evento con mayor dependencia
            if dependencia > max_dependencia_valor:
                max_dependencia_numero = numero
                max_dependencia_valor = dependencia
            
        # Almacenar la tupla en E[p]
        Dep[p] = tuples_list
        print(Dep)
        
    
    E=[(n,p,d) for p in dl.index  for n in N[p] for d in D_fict]
    J=[(n,p) for p in dl.index for n in N[p]]



#%%=======================================================Definición de modelo offline========================================
    #-------------------------------------------Model-------------------------------
    
    m = gp.Model('FALP')
    #    m.setParam("OutputFlag",1)
    
    #------------------------------------------Variables----------------------------
    print("Iniciando variables")
    x=m.addVars(E, vtype=GRB.BINARY, lb = 0)
    y=m.addVars(E, vtype=GRB.BINARY, lb = 0)
    eta=m.addVars(J, vtype=GRB.CONTINUOUS, lb=0)
    fi=m.addVars(J, vtype=GRB.CONTINUOUS, lb=0)
    print("Finalizando variables")
    # ------------------------------------------Objective Function-------------------
    
    costo=gp.quicksum(fi[n,p] for p in dl.index for n in N[p])
    # costo=gp.quicksum((eta[n,p]+eta[N[p][0],p]) for p in dl.index for n in N[p])
    costofict=gp.quicksum(M*y[n,p,d] for p in dl.index for n in N[p] for d in D_fict)
    m.setObjective(costo+costofict, GRB.MINIMIZE)
    #------------------------------------------Restricciones------------------------
    print("Iniciando restricciones")
    
    for p in dl.index:
        print("paciente",p)
        #Restricción 6, se considera el tiempo de llegada del paciente.
        m.addConstr(gp.quicksum(d*(x[N[p][0],p,d]) for d in D) + gp.quicksum(d*(y[N[p][0],p,d]) for d in Dprim)
                    -(( dl.loc[p,'día de llegada'])) == eta[N[p][0],p])
        for n in N[p]:
            #Restricción 1, se asigna un evento médico en algún día posterior a la llegada del paciente.
            m.addConstr(gp.quicksum(x[n,p,d] + y[n,p,d] for d in D_fict) == 1)
            m.addConstr(gp.quicksum(x[n,p,d] + y[n,p,d] for d in D_fict if d < (dl.loc[p,'día de llegada'])) == 0)
            m.addConstr(gp.quicksum(x[n,p,d] for d in Dprim) == 0)
            #Restricción 7, El error se define como la diferencia entre el tiempo de asignación que tuvo el evento menos su tolerancia máxima permitida.        
            m.addConstr(eta[n,p]-ruta_patologia[dl.loc[p,'Diagnóstico']].loc[n,'MÁXIMO (DÍAS)']<= fi[n,p])
            #Restricción 4, Las ventanas generadas entre la diferencia de un evento y otro, será relacionado por un eta.
        for (n,j) in Dep[p]:
            #Constraints 4, Se tiene que respetar las procedencias de los eventos, y su LB y UB.
            m.addConstr(gp.quicksum(d*(x[j,p,d]-x[n,p,d]+y[j,p,d]-y[n,p,d]) for d in D_fict)>= ruta_patologia[dl.loc[p,'Diagnóstico']].loc[j,'PERIODICIDAD (DÍAS)']*(1-gp.quicksum(y[j,p,d] for d in Dprim)))
            #Constraints 5, se considera la ventana de tiempo de los eventos.
            m.addConstr(gp.quicksum(d*(x[j,p,d]-x[n,p,d]+y[j,p,d]-y[n,p,d]) for d in D_fict) == eta[j,p])
    #Restricción 2, se debe respetar los recursos disponibles.
    for r in R:
        for d in D:
            m.addConstr(gp.quicksum(x[n,p,d]*recurso.loc[ruta_patologia[dl.loc[p,'Diagnóstico']].loc[n,'EVENTO'],r] 
                              for p in dl.index for n in N[p])<= recursoT.loc[d,r])
            
    print("Finaliza restricciones")
    m.setParam(GRB.Param.TimeLimit, 11400)
    m.setParam(GRB.Param.Cuts, 0)
    m.setParam(GRB.Param.Seed, 123)
    
    #--------------------------------------------Results------------------------------------------------------
    start_time = time.time()
    
    #Set up solver to solve the model
    m.optimize()
    
    #time to solve model
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    #------------------------------------------Information capture--------------------------------------------
    #Result of objective function
    F_O = m.objVal
    
    #gap de optimalidad
    # Best_UB = m.ObjVal
    # Best_LB = m.ObjBound
    gap_opt = m.MIPGap * 100

        
#%%=======================================================Datos del Largo de espera modelo===========================================

    # Largo total máximo de tiempo de espera de un pacientes.
    lista_dias={}
    dias={}
    for p in P:
        for n in N[p]:
            for d in D_fict:
                if x[n,p,d].x != 0 or y[n,p,d].x != 0:
                    dias[(p,n)]= d
    
    for p in P:
        for n in N[p]:
            for d in D_fict:
                if x[n,p,d].x != 0 or y[n,p,d].x != 0:
                    if d in D:
                        lista_dias[(p,n)]= d
                    else:
                        lista_dias[(p,n)]= dias[(p,1)]
 
    #----------------------------------------Resumen datos--------------------------------------
    lista_de_espera=[]
    lista_de_derivados=[]
    lista_de_tardanza = []
    lista_de_largos = {diag: [] for diag in dl['Diagnóstico'].unique()}
    for p in P:
        if sum(fi[n,p].x for n in N[p]) != 0:
            lista_de_tardanza.append(sum(fi[n,p].x for n in N[p]))
        for d in Dprim:
            if sum(y[n,p,d].x for n in N[p]) != 0:
                lista_de_espera.append(sum(y[n,p,d].x for n in N[p]))
        for d in D:
            if sum(y[n,p,d].x for n in N[p]) != 0:
                lista_de_derivados.append(sum(y[n,p,d].x for n in N[p]))
        if sum(y[n,p,d].x for n in N[p] for d in Dprim) == 0:
            diagnostico = dl.loc[p, 'Diagnóstico']
            largo = max(lista_dias[(p, n)] for n in N[p]) - dl.loc[p, 'día de llegada']
            lista_de_largos[diagnostico].append(largo)
                
    #Recolección de datos por iteración 
    resumen_excel.loc[len(resumen_excel)] = (iteración, len(lista_de_espera),sum(lista_de_espera),sum(lista_de_espera) / len(lista_de_espera) if len(lista_de_espera) != 0 else 0, len(lista_de_derivados),sum(lista_de_derivados),sum(lista_de_derivados) / len(lista_de_derivados) if len(lista_de_derivados) != 0 else 0, sum(1 for p in P if fi[1, p].x != 0),sum(fi[1, p].x for p in P), sum(fi[1, p].x for p in P)/ sum(1 for p in P if fi[1, p].x != 0) if sum(1 for p in P if fi[1, p].x != 0) != 0 else 0, len(lista_de_tardanza), sum(lista_de_tardanza), sum(lista_de_tardanza) / len(lista_de_tardanza) if len(lista_de_tardanza) != 0 else 0)
    tardines_excel.loc[len(tardines_excel)] = (iteración,  sum(lista_de_tardanza) / len(lista_de_tardanza) if len(lista_de_tardanza) != 0 else 0,sum(1 for p in P for n in N[p] if fi[n, p].x != 0),statistics.stdev(lista_de_tardanza) if len(lista_de_tardanza) > 1 else 0, max(lista_de_tardanza) if len(lista_de_tardanza) >= 1 else 0)
    for pt in patologias:
        largo_excel.loc[len(largo_excel)] = (iteración,pt,sum(lista_de_largos[pt])/len(lista_de_largos[pt]) if len(lista_de_largos[pt]) != 0 else 0 ,max(lista_de_largos[pt]) if len(lista_de_largos[pt]) != 0 else 0, min(lista_de_largos[pt]) if len(lista_de_largos[pt]) != 0 else 0)
    
    da_time.loc[iteración]= (iteración, gap_opt ,elapsed_time/len(P), len(P),elapsed_time) 
    # Procesar datos
    resultados_offline[iteración], resultados_offline2[iteración] = procesar_iteracion(x,y,dl, lista_dias, ruta_patologia, N, D_fict, Dprim, eta, fi, M, F_O, P, iteración)
    
    iteración += 2
  
#%%=======================================================Excel===========================================

with pd.ExcelWriter('Importante_Tardiness_1.xlsx') as writer:
    resumen_excel.to_excel(writer, sheet_name="Resumen", index=False)    
    tardines_excel.to_excel(writer, sheet_name="Tardiness", index=False) 
    largo_excel.to_excel(writer, sheet_name="Largo", index=False) 
    da_time.to_excel(writer, sheet_name="Tiempo", index=False)
    
# Nombre del archivo Excel
archivo_excel = "MILP_eventos_Tardiness_1.xlsx"
archivo_excel2 = "MILP_pacientes_Tardiness_1.xlsx"

# Verificar si el archivo existe
if os.path.exists(archivo_excel):
    # El archivo existe, agregar nuevas hojas
    with pd.ExcelWriter(archivo_excel) as writer:
        for iterador, df in resultados_offline.items():
            df.to_excel(writer, index=False, sheet_name=f"{iterador}")
else:
    # El archivo no existe, crear uno nuevo
    with pd.ExcelWriter(archivo_excel) as writer:
        for iterador, df in resultados_offline.items():
            df.to_excel(writer, index=False, sheet_name=f"{iterador}")
    
# Verificar si el archivo existe
if os.path.exists(archivo_excel2):
    # El archivo existe, agregar nuevas hojas
    with pd.ExcelWriter(archivo_excel2) as writer:
        for iterador, df2 in resultados_offline2.items():
            df2.to_excel(writer, index=False, sheet_name=f"{iterador}")
else:
    # El archivo no existe, crear uno nuevo
    with pd.ExcelWriter(archivo_excel2) as writer:
        
        for iterador, df2 in resultados_offline2.items():
            df2.to_excel(writer, index=False, sheet_name=f"{iterador}")