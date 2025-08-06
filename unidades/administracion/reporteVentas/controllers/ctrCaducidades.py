import xmlrpc.client
from conexiones.conectionOdoo import OdooAPI
from datetime import datetime, timedelta

#?Intancia de conexión a Odoo
conn=OdooAPI()

# --------------------------------------------------------------------------------------------------
# * Función: get_allCaducidades
# * Descripción: Obtiene todas las caducidades de Odoo
#
# ! Parámetros:
#   - No recibe ningún parámetro
#
# ? Condiciones para saber que caducidades obtener
#   1. Ninguna
#
# ? Return:
#   - Caso success:
#       Retorna un JSON con el status success y una lista (array) de caducidades. cada producto contiene los siguientes campos:
#       { id, name, product_id, product_qty }
#   - Caso error: 
#       En caso de haber ocurrido algun error retorna un JSON con status error y el mensaje del error
# --------------------------------------------------------------------------------------------------
def get_allCaducidades():
    #!Determinamos que haya algna conexión con Odoo
    if not conn.models:
        return ({
            'status'  : 'error',
            'message' : 'Error en la conexión con Odoo, no hay conexión Activa'
        })
    
    #Función try para obteners a todos las caducidades
    try:
        #Obtiene todas las caducidades de Odoo
        caducidades = conn.models.execute_kw(
            conn.db, conn.uid, conn.password, 
            'stock.lot', 'search_read', 
            [[]],
            { 'fields' : ['name', 'product_id', 'product_qty']}
        )
        
        #Retornar todas las caducidades
        return ({
            'status'  : 'success',
            'caducidades' : caducidades
        })
    except xmlrpc.client.Fault as e:
        return ({
            'status'       : 'error',
            'message'      : f'Error al ejecutar la consulta a Odoo: {str(e)}',
            'fault_code'   : e.faultCode,
            'fault_string' : e.faultString,
        })
    

# --------------------------------------------------------------------------------------------------
# * Función: get_newCaducidades
# * Descripción: Obtiene todas las caducidades de Odoo que se crearon un dia antes
#
# ! Parámetros:
#   - No recibe ningún parámetro
#
# ? Condiciones para saber que caducidades obtener
#   1. create_date debe ser de un día anterior
#
# ? Return:
#   - Caso success:
#       Retorna un JSON con el status success y una lista (array) de caducidades. cada producto contiene los siguientes campos:
#       { id, name, product_id, product_qty }
#   - Caso error: 
#       En caso de haber ocurrido algun error retorna un JSON con status error y el mensaje del error
# --------------------------------------------------------------------------------------------------    
def get_newCaducidades():
    #!Determinamos que haya algna conexión con Odoo
    if not conn.models:
        return ({
            'status'  : 'error',
            'message' : 'Error en la conexión con Odoo, no hay conexión Activa'
        })
    
    #Función try para obteners a todos lo caducidades
    try:
        #Obtiene el dia anterior al que es hoy
        lastDay = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
        #Obtiene todas las caducidades de Odoo
        caducidades = conn.models.execute_kw(
            conn.db, conn.uid, conn.password, 
            'stock.lot', 'search_read', 
            [[['create_date', '>=', lastDay]]],
            { 'fields' : ['name', 'product_id', 'product_qty']}
        )
        
        #Retornar todas las caducidades
        return ({
            'status'  : 'success',
            'caducidades' : caducidades
        })
    except xmlrpc.client.Fault as e:
        return ({
            'status'       : 'error',
            'message'      : f'Error al ejecutar la consulta a Odoo: {str(e)}',
            'fault_code'   : e.faultCode,
            'fault_string' : e.faultString,
        })
    

# --------------------------------------------------------------------------------------------------
# * Función: update_Caducidades
# * Descripción: Obtiene todas las caducidades de Odoo
#
# ! Parámetros:
#   - No recibe ningún parámetro
#
# ? Condiciones para saber que caducidades obtener
#   1. ninguna
#
# ? Return:
#   - Caso success:
#       Retorna un JSON con el status success y una lista (array) de caducidades. cada producto contiene los siguientes campos:
#       { id, name, product_id, product_qty }
#   - Caso error: 
#       En caso de haber ocurrido algun error retorna un JSON con status error y el mensaje del error
# -------------------------------------------------------------------------------------------------- 
def update_Caducidades():
    #!Determinamos que haya algna conexión con Odoo
    if not conn.models:
        return ({
            'status'  : 'error',
            'message' : 'Error en la conexión con Odoo, no hay conexión Activa'
        })
    
    #Función try para obteners a todos lo caducidades
    try:
        #Obtiene todas las caducidades de Odoo
        caducidades = conn.models.execute_kw(
            conn.db, conn.uid, conn.password, 
            'stock.lot', 'search_read', 
            [[]],
            { 'fields' : ['name', 'product_id', 'product_qty']}
        )
        
        #Retornar todas las caducidades
        return ({
            'status'  : 'success',
            'caducidades' : caducidades
        })
    except xmlrpc.client.Fault as e:
        return ({
            'status'       : 'error',
            'message'      : f'Error al ejecutar la consulta a Odoo: {str(e)}',
            'fault_code'   : e.faultCode,
            'fault_string' : e.faultString,
        })