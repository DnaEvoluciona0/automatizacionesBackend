from django.http import JsonResponse
from unidades.administracion.reporteVentas.models import Clientes
from unidades.administracion.reporteVentas.controllers import ctrCliente


# --------------------------------------------------------------------------------------------------
# * Función: insertProducts
# * Descripción: Inserta productos en la base de datos PostgreSQL.
#
# ! Parámetros:
#     - Recibe una lista (array) de clientes. Cada cliente debe contener los siguientes campos:
#       { id, name, city, state_id, country_id }
#     - Nota: Solo el campo "id" es obligatorio; los demás son opcionales.
#
# ? Condiciones para insertar un producto en la base de datos:
#     1. El cliente debe un id único.
#
# --------------------------------------------------------------------------------------------------
def insertClients(clients):
    #Obtenemos todos los ids de clientes de Postgres
    clientesPSQL = Clientes.objects.all().values_list('idCliente', flat=True)
    
    newClientes = 0
    
    for cliente in clients:
        #Si el id no esta en la base de datos lo agrega
        if cliente['id'] not in clientesPSQL:
            #Asignamos la distribución de la información en sus respectivas variables
            Clientes.objects.create(
                idCliente           = cliente['id'],
                nombre              = cliente['name'] if cliente['name']!=False else "",
                ciudad              = cliente['city'] if cliente['city']!=False else "",
                estado              = cliente['state_id'][1] if cliente['state_id']!=False else "",
                pais                = cliente['country_id'][1] if cliente['country_id']!=False else "",
                tipoCliente         = "Cliente Nuevo",
                numTransacciones    = 0
            )
            newClientes=newClientes+1
    
    return ({
        'status'  : 'success',
        'message' : f'Los clientes son: {newClientes}'
    })
    

# --------------------------------------------------------------------------------------------------
# * Función: pullClientesOdoo
# * Descripción: Obtiene todos los clientes de Odoo y llama a la función de insertar datos
#
# ! Parámetros:
#     - request. Como se utiliza para URLS, recibe la información de la consulta
#
# ? Returns:
#     - Caso error:
#           Ocurre algún error en traer a los clientes de Odoo
#           La función insertClients retorna mensaje de error
#           Ocurre una excepción en la ejecución del código
#     - Caso success:
#           La función insertClients retorna mensaje success y envía mensaje con la cantidad de clientes agregados
# --------------------------------------------------------------------------------------------------
def pullClientesOdoo(request):
    try:
        
        #Trae todos los clientes de la base de datos
        clientesOdoo=ctrCliente.get_allClients()
        
        if clientesOdoo['status'] == 'success':
            
            #Llama a insertClientes y le envia todos lo clientes que obtuvo de Odoo
            response=insertClients(clientesOdoo['clientes'])
            if response['status'] == "success":
                message = response['message']
                return JsonResponse({
                    'status'  : 'success',
                    'message' : f'Se han agregado correctamente {message} Clientes nuevos'
                })
            return JsonResponse({
                'status'  : 'error',
                'message' : response['message']
            })
            
        else:
            return JsonResponse({
                'status'  : 'error',
                'message' : clientesOdoo['message']
            })
        
    except Exception as e:
        return JsonResponse({
            'status'  : 'error',
            'message' : f'Ha ocurrido un error al tratar de insertar los datos: {e}'
        })


# --------------------------------------------------------------------------------------------------
# * Función: createClientesOdoo
# * Descripción: Obtiene todos los clientes de Odoo que se haya creado desde un dia antes
#
# ! Parámetros:
#     - request. Como se utiliza para URLS, recibe la información de la consulta
#
# ? Returns:
#     - Caso error:
#           Ocurre algún error en traer a los clientes de Odoo
#           La función insertClients retorna mensaje de error
#           Ocurre una excepción en la ejecución del código
#     - Caso success:
#           La función insertClients retorna mensaje success y envía mensaje con la cantidad de clientes agregados
# --------------------------------------------------------------------------------------------------
def createClientesOdoo(request):
    try:
        #Traer todos los clientes de Odoo
        clientesOdoo=ctrCliente.get_newClients()
        
        if clientesOdoo['status'] == 'success':
            
            #Llama a insertClientes y le envia todos lo clientes que obtuvo de Odoo
            response=insertClients(clientesOdoo['clientes'])
            if response['status'] == "success":
                message = response['message']
                return JsonResponse({
                    'status'  : 'success',
                    'message' : f'Se han agregado correctamente {message} Clientes nuevos'
                })
            return JsonResponse({
                'status'  : 'error',
                'message' : response['message']
            })
            
        else:
            return JsonResponse({
                'status'  : 'error',
                'message' : clientesOdoo['message']
            })
        
    except Exception as e:
        return JsonResponse({
            'status'  : 'error',
            'message' : f'Ha ocurrido un error al tratar de insertar los datos de los nuevos clientes: {e}'
        })


# --------------------------------------------------------------------------------------------------
# * Función: updateClientesOdoo
# * Descripción: Obtiene todos los clientes de Odoo que se haya creado desde un dia antes
#
# ! Parámetros:
#     - request. Como se utiliza para URLS, recibe la información de la consulta
#
# ? Returns:
#     - Caso error:
#           Ocurre algún error en traer a los clientes de Odoo
#           La función insertClients retorna mensaje de error
#           Ocurre una excepción en la ejecución del código
#     - Caso success:
#           La función retorna mensaje success y envía mensaje con la cantidad de clientes modificados
# --------------------------------------------------------------------------------------------------
def updateClientesOdoo(request):
    try:
        #Traer todos los clientes de Odoo que se actualizaron
        clientesOdoo=ctrCliente.update_Clients()
        
        if clientesOdoo['status'] == 'success':
            newClientes = 0
            
            for cliente in clientesOdoo['clientes']:
                try:
                    #Busca el ID del cliente en Postgres
                    clienteAct = Clientes.objects.get(idCliente=cliente['id'])
                    
                    #Cambia los valores de la Postgres por los nuevos valores que hay en odoo
                    clienteAct.nombre              = cliente['name'] if cliente['name']!=False else ""
                    clienteAct.ciudad              = cliente['city'] if cliente['city']!=False else ""
                    clienteAct.estado              = cliente['state_id'][1] if cliente['state_id']!=False else ""
                    clienteAct.pais                = cliente['country_id'][1] if cliente['country_id']!=False else ""
                    
                    #Guarda los cambios de cliente
                    clienteAct.save()
                    newClientes=newClientes+1
                except:
                    pass
            
            return JsonResponse({
                'status'  : 'success',
                'message' : f'Los clientes modificados son: {newClientes}'
            })
        else:
            return JsonResponse({
                'status'  : 'error',
                'message' : clientesOdoo['message']
            })
        
    except Exception as e:
        return JsonResponse({
            'status'  : 'error',
            'message' : f'Ha ocurrido un error al tratar de insertar los datos: {e}'
        })


# --------------------------------------------------------------------------------------------------
# * Función: createClientesExcel
# * Descripción: Obtiene todos los clientes de un excel y llama a la función de insertar datos
#
# ! Parámetros:
#     - request. Como se utiliza para URLS, recibe la información de la consulta
#
# ? Returns:
#     - Caso error:
#           Ocurre algún error en traer a los clientes de Odoo
#           La función insertClients retorna mensaje de error
#           Ocurre una excepción en la ejecución del código
#     - Caso success:
#           La función insertClients retorna mensaje success y envía mensaje con la cantidad de clientes agregados
# --------------------------------------------------------------------------------------------------
def createClientesExcel(request):
    try:
        clientesPSQL = Clientes.objects.all().values_list('idCliente', flat=True)
        #Traer todos los clientes de Odoo
        clientesOdoo=ctrCliente.pullClientsExcel(clientesPSQL)
        
        if clientesOdoo['status'] == 'success':
            
            #Llama a insertClientes y le envia todos lo clientes que obtuvo del Excel y Odoo
            response=insertClients(clientesOdoo['clientes'])
            if response['status'] == "success":
                message = response['message']
                return JsonResponse({
                    'status'  : 'success',
                    'message' : f'Se han agregado correctamente {message} Clientes nuevos'
                })
            return JsonResponse({
                'status'  : 'error',
                'message' : response['message']
            })
            
        else:
            return JsonResponse({
                'status'  : 'error',
                'message' : clientesOdoo['message']
            })
        
    except Exception as e:
        return JsonResponse({
            'status'  : 'error',
            'message' : f'Ha ocurrido un error al tratar de insertar los datos de los nuevos clientes: {e}'
        })