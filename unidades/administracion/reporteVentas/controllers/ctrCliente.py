import xmlrpc.client
from conexiones.conectionOdoo import OdooAPI
import pandas as pd
from datetime import datetime, timedelta

#?Intancia de conexión a Odoo
conn=OdooAPI()

#?Obtiene un archivo mendiante la url y lo abre en la pestaña necesaria para su posterior lectura
archivo = 'static/ContpaqBD.xlsx'

# --------------------------------------------------------------------------------------------------
# * Función: get_allClients
# * Descripción: Obtiene todos los clientes (que hayan hecho alguna compra) de Odoo
#
# ! Parámetros:
#   - No recibe ningún parámetro
#
# ? Condiciones para saber que clientes obtener
#   1. invoice_ids no debe ser False o estar vacio:
#   2. active debe ser True o False para que obtenga todos, incluso los archivados:
#
# ? Return:
#   - Caso success:
#       Retorna un JSON con el status success y una lista (array) de clientes. cada producto contiene los siguientes campos:
#       { id, name, city, state_id, country_id }
#   - Caso error: 
#       En caso de haber ocurrido algun error retorna un JSON con status error y el mensaje del error
# --------------------------------------------------------------------------------------------------
def get_allClients():
    #!Determinamos que haya algna conexión con Odoo
    if not conn.models:
        return ({
            'status'  : 'error',
            'message' : 'Error en la conexión con Odoo, no hay conexión Activa'
        })
    
    #Función try para obteners a todos lo clientes
    try:
        #Obtener todos los clientes que aparecen en los invoices
        partner_invoice = conn.models.execute_kw(
            conn.db, conn.uid, conn.password, 
            'account.move', 'read_group', 
            [[
                ('state', '=', 'posted'), 
                '|', ('move_type', '=', 'out_invoice'), ('move_type', '=', 'out_refund'), 
                ('branch_id', 'not ilike', 'STUDIO'), 
                ('branch_id', 'not ilike', 'TORRE'),
                ('team_id', 'not in', [8, 10, 12, 15, 16, 17, 21, 22]),
                '|', '|', ('name', 'ilike', 'INV/'), ('name', 'ilike', 'MUEST/'), ('name', 'ilike', 'BONIF/')
            ],['partner_id'],['partner_id']]
        )
        
        partner_ids = [group['partner_id'][0] for group in partner_invoice]
        
        #Obtener a todos los clientes que cumplan con las condiciones
        res_partner = conn.models.execute_kw(
            conn.db, conn.uid, conn.password, 
            'res.partner', 'search_read', 
            [[
                ('id', 'in', partner_ids),
                '|', ('active', '=', True), ('active', '=', False)
            ]],
            { 'fields' : ['name', 'city', 'state_id', 'country_id']}
        )
        
        #Retorna todos lo clientes encontrados
        return ({
            'status'  : 'success',
            'clientes' : res_partner
        })
        
    except xmlrpc.client.Fault as e:
        return ({
            'status'       : 'error',
            'message'      : f'Error al ejecutar la consulta a Odoo: {str(e)}',
            'fault_code'   : e.faultCode,
            'fault_string' : e.faultString,
        })
    
    
# --------------------------------------------------------------------------------------------------
# * Función: get_newClients
# * Descripción: Obtiene todos los clientes nuevos de un dia antes
#
# ! Parámetros:
#   - No recibe ningún parámetro
#
# ? Condiciones para saber que clientes obtener
#   1. create_date debe ser de un día antes:
#   2. active debe ser True o False para que obtenga todos, incluso los archivados:
#
# ? Return:
#   - Caso success:
#       Retorna un JSON con el status success y una lista (array) de clientes. cada producto contiene los siguientes campos:
#       { id, name, city, state_id, country_id }
#   - Caso error: 
#       En caso de haber ocurrido algun error retorna un JSON con status error y el mensaje del error
# --------------------------------------------------------------------------------------------------
def get_newClients(clientesIDs):
    #!Determinamos que haya algna conexión con Odoo
    if not conn.models:
        return ({
            'status'  : 'error',
            'message' : 'Error en la conexión con Odoo, no hay conexión Activa'
        })
    
    #Función try para obteners a todos lo clientes
    try:        
        #Obtener todos los clientes que aparecen en los invoices
        partner_invoice = conn.models.execute_kw(
            conn.db, conn.uid, conn.password, 
            'account.move', 'read_group', 
            [[
                ('state', '=', 'posted'), 
                '|', ('move_type', '=', 'out_invoice'), ('move_type', '=', 'out_refund'), 
                ('branch_id', 'not ilike', 'STUDIO'), 
                ('branch_id', 'not ilike', 'TORRE'),
                ('team_id', 'not in', [8, 10, 12, 15, 16, 17, 21, 22]),
                '|', '|', ('name', 'ilike', 'INV/'), ('name', 'ilike', 'MUEST/'), ('name', 'ilike', 'BONIF/')
            ],['partner_id'],['partner_id']]
        )
        
        partner_ids = [group['partner_id'][0] for group in partner_invoice]
        
        #Obtener a todos los clientes que cumplan con las condiciones
        res_partner = conn.models.execute_kw(
            conn.db, conn.uid, conn.password, 
            'res.partner', 'search_read', 
            [[
                ('id', 'not in', clientesIDs),
                ('id', 'in', partner_ids),
                '|', ('active', '=', True), ('active', '=', False)
            ]],
            { 'fields' : ['name', 'city', 'state_id', 'country_id']}
        )
        
        #Retorna todos lo clientes encontrados
        return ({
            'status'  : 'success',
            'clientes' : res_partner
        })
    
    except xmlrpc.client.Fault as e:
        return ({
            'status'       : 'error',
            'message'      : f'Error al ejecutar la consulta a Odoo: {str(e)}',
            'fault_code'   : e.faultCode,
            'fault_string' : e.faultString,
        })


# --------------------------------------------------------------------------------------------------
# * Función: get_updateClients
# * Descripción: Obtiene todos los clientes que se hayan actualizado desde hace un día y actualiza sus registros
#
# ! Parámetros:
#   - No recibe ningún parámetro
#
# ? Condiciones para saber que clientes obtener
#   1. write_date debe ser de un día antes:
#   2. invoice_ids no debe ser False o estar vacio:
#   3. active debe ser True o False para que obtenga todos, incluso los archivados:
#
# ? Return:
#   - Caso success:
#       Retorna un JSON con el status success y una lista (array) de clientes. cada producto contiene los siguientes campos:
#       { id, name, city, state_id, country_id }
#   - Caso error: 
#       En caso de haber ocurrido algun error retorna un JSON con status error y el mensaje del error
# --------------------------------------------------------------------------------------------------
def get_updateClients(clientesIDs):
    #!Determinamos que haya algna conexión con Odoo
    if not conn.models:
        return ({
            'status'  : 'error',
            'message' : 'Error en la conexión con Odoo, no hay conexión Activa'
        })
    
    #Función try para obteners a todos lo clientes
    try:        
        #Obtener todos los clientes que aparecen en los invoices
        partner_invoice = conn.models.execute_kw(
            conn.db, conn.uid, conn.password, 
            'account.move', 'read_group', 
            [[
                ('state', '=', 'posted'), 
                '|', ('move_type', '=', 'out_invoice'), ('move_type', '=', 'out_refund'), 
                ('branch_id', 'not ilike', 'STUDIO'), 
                ('branch_id', 'not ilike', 'TORRE'),
                ('team_id', 'not in', [8, 10, 12, 15, 16, 17, 21, 22]),
                '|', '|', ('name', 'ilike', 'INV/'), ('name', 'ilike', 'MUEST/'), ('name', 'ilike', 'BONIF/')
            ],['partner_id'],['partner_id']]
        )
        
        partner_ids = [group['partner_id'][0] for group in partner_invoice]
        
        #Obtener a todos los clientes que cumplan con las condiciones
        res_partner = conn.models.execute_kw(
            conn.db, conn.uid, conn.password, 
            'res.partner', 'search_read', 
            [[
                ('id', 'in', clientesIDs),
                ('id', 'in', partner_ids), 
                '|', ('active', '=', True), ('active', '=', False)
            ]],
            { 'fields' : ['name', 'city', 'state_id', 'country_id']}
        )
        
        #Retorna todos lo clientes encontrados
        return ({
            'status'  : 'success',
            'clientes' : res_partner
        })
    
    except xmlrpc.client.Fault as e:
        return ({
            'status'       : 'error',
            'message'      : f'Error al ejecutar la consulta a Odoo: {str(e)}',
            'fault_code'   : e.faultCode,
            'fault_string' : e.faultString,
        })


# --------------------------------------------------------------------------------------------------
# * Función: get_ClientsExcel
# * Descripción: Obtiene todos los clientes del archivo contapqDB en la hoja de clientes
#
# ! Parámetros:
#   - Rebice idsClientes, una lista de IDs de clientes que ya se encuentran en la BD de Postgres
#
# ? Condiciones para saber que clientes obtener
#   1. Debe ser de un ID
#   2. Debe tener un nombre
#
# ? Return:
#   - Caso success:
#       Retorna un JSON con el status success y una lista (array) de clientes. cada producto contiene los siguientes campos:
#       { id, name, city, state_id, country_id }
#   - Caso error: 
#       En caso de haber ocurrido algun error retorna un JSON con status error y el mensaje del error
# --------------------------------------------------------------------------------------------------  
def get_clientsExcel(idsclientes):
    #!Determinamos que haya algna conexión con Odoo
    if not conn.models:
        return ({
            'status'  : 'error',
            'message' : 'Error en la conexión con Odoo, no hay conexión Activa'
        })
    
    #Función try para obteners a todos lo clientes
    try:
        #Abrimos el excel solo en la pagina de clientes
        df = pd.read_excel(archivo, sheet_name='Clientes')
        clientes=[]
        ids=[]
        
        #Obtenemos todos los id de clientes no esten ya registrados en odoo
        for index, cliente in df.iterrows():
            if cliente['idCliente'] not in idsclientes:
                ids.append(cliente['idCliente'])
                
        clientesData = {}
        
        #Busca todos lo clientes que contengan alguno de los ids de la lista anterior
        res_partner = conn.models.execute_kw(
            conn.db, conn.uid, conn.password, 
            'res.partner', 'search_read', 
            [[['id', 'in', ids], '|', ['active', '=', True], ['active', '=', False]]],
            { 'fields' : ['name', 'city', 'state_id', 'country_id']}
        )
        
        #A cada resultado de la lista de res_partner lo agrega como un objeto donde su propiedad es el id de cliente y la información es no obtenido de res_partner respecto al cliente
        for partner in res_partner:
            clientesData[partner['id']] = partner
        
        for index, cliente in df.iterrows():
            #Si el id del Cliente se encuentra en el objeto clientesData y además se encuentra en los ids que no estan en la BD de Postgres, agrega su información en Postrges
            if cliente["idCliente"] in clientesData and cliente["idCliente"] in ids:
                clientes.append(clientesData[cliente["idCliente"]])
            
            #Si el id del Cliente no se encuentra en el objeto clientesData y además se encuentra en los ids que no estan en la BD de Postgres, agrega su información en Postrges pero con algunos datos vacios   
            if cliente["idCliente"] not in clientesData and cliente["idCliente"] in ids:
                clientes.append({
                    'id': cliente["idCliente"],
                    'name': cliente["Cliente"],
                    'city': False,
                    'state_id': False,
                    'country_id': False,
                })
        
        #Retorna todos lo clientes encontrados
        return ({
            'status'  : 'success',
            'clientes' : clientes
        })
        
    except xmlrpc.client.Fault as e:
        return ({
            'status'       : 'error',
            'message'      : f'Error al ejecutar la consulta a Odoo: {str(e)}',
            'fault_code'   : e.faultCode,
            'fault_string' : e.faultString,
        })