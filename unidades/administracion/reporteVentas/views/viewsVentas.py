from django.http import JsonResponse
from unidades.administracion.reporteVentas.models import Ventas, Clientes
from unidades.administracion.reporteVentas.views.viewsLineaPV import insertLineaVentaOdoo
from unidades.administracion.reporteVentas.controllers import ctrVentas
from unidades.produccionLogistica.maxMin.models import Productos
from datetime import datetime

# --------------------------------------------------------------------------------------------------
# * Función: insertVentas
# * Descripción: Obtiene las ventas de la base de datos de Odoo o de excel y los inserta en la base de datos de PostgreSQL
#
# ! Parámetros:
#     - Recibe un array de ventas, donde cada indice del array debe contener la siguiente informacion:
#           {  id, nombre, fechaCreacion, cliente, vendedor, direccionEnvio, unidad, totalVenta, tipoFactura, lineaProducto {[idProducto, nombreProducto, cantidad, precioUnitario, precioSubtotal, marca, categoria], ...}, pais, estado, ciudad  }
#
# ? Condiciones para insertar una venta:
#     1. La venta debe tener un idVenta o nombre disponible en la base de datos de PostgreSQL.
#
# ? Lógica para determinar el venta:
#     - Si "move_type" es igual a "out_invoice", significa que es una venta completada.
#     - Si "move_type" es igual a "out_refund", significa que es una nota de crédito.
# --------------------------------------------------------------------------------------------------
def insertVentas(ventas):
    #Llamar a las ventas, productos e insumos ya existentes en Postgres
    ventasPSQL = Ventas.objects.all().values_list('idVenta', flat=True)
    
    clientesObj = {c.idCliente: c for c in Clientes.objects.all()}
    
    ultimasVentas = {}
            
    ventasCreate = []
    clientesUpdate = []
    ventasPVCreate= []
    
    newVentas = 0
    newNota = 0
    
    for venta in ventas:
        if venta['name'] not in ventasPSQL:
            #Asignamos la distribución de la información en sus respectivas variables
            #Obtenemos al cliente
            clienteObj = clientesObj.get(venta['partner_id'][0])
            
            #Factura
            if venta['move_type'] == 'out_invoice':
                newVentas=newVentas+1
                clienteObj.numTransacciones+=1
            #Nota de credito
            if venta['move_type'] == 'out_refund':
                newNota=newNota+1

        
            ventaRec = ultimasVentas.get(clienteObj.idCliente)['invoice_date'] if ultimasVentas.get(clienteObj.idCliente) else None
            ventaAct = venta['invoice_date']
            
            if clienteObj.numTransacciones < 2:
                clienteObj.tipoCliente = 'Cliente Nuevo'
            else:
                if ventaRec:
                    if clienteObj.tipoCliente == 'Cliente Nuevo' and ventaAct.month == ventaRec.month and ventaAct.year == ventaRec.year:
                        clienteObj.tipoCliente = 'Cliente Nuevo'
                    elif (ventaAct - ventaRec).days >180:
                        clienteObj.tipoCliente = 'Cliente Recuperado'
                    else:
                        if clienteObj.tipoCliente == 'Cliente Recuperado' and ventaAct.month == ventaRec.month and ventaAct.year == ventaRec.year:
                            clienteObj.tipoCliente = 'Cliente Recuperado'
                        clienteObj.tipoCliente = 'Cliente Cartera'
                
            ventasCreate.append(
                Ventas(
                    idVenta         = venta['name'],
                    fecha           = venta['invoice_date'],
                    ciudadVenta     = venta['city'],
                    estadoVenta     = venta['state_id'],
                    paisVenta       = venta['country_id'],
                    unidad          = venta['branch_id'][1] if venta['branch_id'] else "",
                    vendedor        = venta['invoice_user_id'][1],
                    total           = venta['amount_total_signed'],
                    cliente         = clienteObj,
                    tipoCliente     = clienteObj.tipoCliente
                )
            )
            
            ventasPVCreate.extend(venta['productsLines'])
            
            clientesUpdate.append(clienteObj)
            
            ultimasVentas[clienteObj.idCliente] = venta

    try:
        Ventas.objects.bulk_create(ventasCreate, batch_size=1000)
        Clientes.objects.bulk_update(
            clientesUpdate,
            ['tipoCliente', 'numTransacciones'],
            batch_size=1000
        )
        #Llamamos a pull linea ventas para registrar todos los productos en Postgres
        insertLineaVentaOdoo(ventasPVCreate)
    except:
        try:
            for venta in ventasCreate:
                venta.save()       
        except Exception as e:
            print("Error en viewsVentas.insertLVentas | Venta no se inserto: ", e, venta)

    return({
        'status'  : 'success',
        'message' : [newVentas, newNota, (newVentas + newNota)]
    })
                    
                    
# --------------------------------------------------------------------------------------------------
# * Función: pullVentasOdoo
# * Descripción: Obtiene todos las ventas de Odoo y llama a la función de insertarVentas e intertarLinea
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
#           La función insertarVentas retorna mensaje success y envía mensaje con la cantidad de facturas y notas de credito agregadas
# --------------------------------------------------------------------------------------------------
def pullVentasOdoo(request):
    try:
        
        #Traer todos los clientes de Odoo
        ventasOdoo=ctrVentas.get_allSales()
        
        if ventasOdoo['status'] == 'success':
            
            #Llama a insertVentas y le envia todos las ventas que obtuvo de Odoo
            response=insertVentas(ventasOdoo['ventas'])
            
            if response['status'] == "success":
                return JsonResponse({
                    'status'  : 'success',
                    'message' : f'Se han agregado correctamente {response["message"][0]} ventas, {response["message"][1]} notas de credito dando un total de {response["message"][2]} de {len(ventasOdoo["ventas"])}'
                })
                
            return JsonResponse({
                'status'  : 'error',
                'message' : response['message']
            })
        
        else:
            return JsonResponse({
                'status'  : 'error',
                'message' : ventasOdoo['message']
            })
        
    except Exception as e:
        return JsonResponse({
            'status'  : 'error',
            'message' : f'Ha ocurrido un error en pull Ventas: {e}'
        })


# --------------------------------------------------------------------------------------------------
# * Función: createVentasOdoo
# * Descripción: Obtiene todos las ventas de Odoo que se hayan hecho hace un dia y llama a la función de insertarVentas e intertarLinea
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
#           La función insertarVentas retorna mensaje success y envía mensaje con la cantidad de facturas y notas de credito agregadas
# --------------------------------------------------------------------------------------------------        
def createVentasOdoo(request):
    try:
        ventasIDs = Ventas.objects.all().values_list('idVenta', flat=True)
        
        #Traer todos los clientes de Odoo
        ventasOdoo=ctrVentas.get_newSales(list(ventasIDs))
        
        if ventasOdoo['status'] == 'success':
            
            #Llama a insertVentas y le envia todos las ventas que obtuvo de Odoo
            response=insertVentas(ventasOdoo['ventas'])
            
            if response['status'] == "success":
                return JsonResponse({
                    'status'  : 'success',
                    'message' : f'Se han agregado correctamente {response["message"][0]} ventas nuevas, {response["message"][1]} notas de credito nuevas dando un total de {response["message"][2]} de {len(ventasOdoo["ventas"])}'
                })
                
            return JsonResponse({
                'status'  : 'error',
                'message' : response['message']
            })
        
        else:
            return JsonResponse({
                'status'  : 'error',
                'message' : ventasOdoo['message']
            })
        
    except Exception as e:
        return JsonResponse({
            'status'  : 'error',
            'message' : f'Ha ocurrido un error en pull Ventas: {e}'
        })


# --------------------------------------------------------------------------------------------------
# * Función: createSalesExcel
# * Descripción: Obtiene todos las ventas de Excel que se hayan hecho hace un dia y llama a la función de insertarVentas e intertarLinea
#
# ! Parámetros:
#     - request. Como se utiliza para URLS, recibe la información de la consulta
#
# ? Returns:
#     - Caso error:
#           Ocurre algún error en traer a los clientes de Excel
#           La función insertClients retorna mensaje de error
#           Ocurre una excepción en la ejecución del código
#     - Caso success:
#           La función insertarVentas retorna mensaje success y envía mensaje con la cantidad de facturas y notas de credito agregadas
# --------------------------------------------------------------------------------------------------  
def pullVentasExcel(request):
    try:
        
        #Traer todos los clientes de Odoo
        ventasOdoo=ctrVentas.get_VentasExcel()
        
        if ventasOdoo['status'] == 'success':
            
            #Llama a insertVentas y le envia todos las ventas que obtuvo de Odoo
            response=insertVentas(ventasOdoo['ventas'])
            
            if response['status'] == "success":
                return JsonResponse({
                    'status'  : 'success',
                    'message' : f'Se han agregado correctamente {response["message"][0]} ventas de Excel, {response["message"][1]} notas de credito de Excel dando un total de {response["message"][2]} de {len(ventasOdoo["ventas"])}'
                })
                
            return JsonResponse({
                'status'  : 'error',
                'message' : response['message']
            })
        
        else:
            return JsonResponse({
                'status'  : 'error',
                'message' : ventasOdoo['message']
            })
        
    except Exception as e:
        return JsonResponse({
            'status'  : 'error',
            'message' : f'Ha ocurrido un error en createSalesExcel: {e}'
        })