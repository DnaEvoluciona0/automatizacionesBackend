from django.http import JsonResponse
from unidades.administracion.reporteVentas.models import Ventas, Clientes
from unidades.administracion.reporteVentas.views.viewsLineaPV import insertLineaVentaOdoo
from unidades.administracion.reporteVentas.controllers import ctrVentas
from unidades.produccionLogistica.maxMin.models import Insumos, Productos

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
    productosPSQL = Productos.objects.all().values_list('id', flat=True)
    insumosPSQL = Insumos.objects.all().values_list('id', flat=True)
    
    newVentas = 0
    newNota = 0
    
    for venta in ventas:
        if venta['name'] not in ventasPSQL:
            #Asignamos la distribución de la información en sus respectivas variables
            try:
                Ventas.objects.create(
                idVenta         = venta['name'],
                fecha           = venta['invoice_date'],
                ciudadVenta     = venta['city'],
                estadoVenta     = venta['state_id'],
                paisVenta       = venta['country_id'],
                unidad          = venta['branch_id'][1] if venta['branch_id'] else "",
                vendedor        = venta['invoice_user_id'][1],
                total           = venta['amount_total_signed'],
                idCliente_id    = venta['partner_id'][0]
                )
                #Llamamos a pull linea ventas para registrar todos los productos en Postgres
                insertLineaVentaOdoo(venta['productsLines'], venta['name'], venta['invoice_date'], productosPSQL, insumosPSQL)
                #Factura
                if venta['move_type'] == 'out_invoice':
                    newVentas=newVentas+1
                #Nota de credito
                if venta['move_type'] == 'out_refund':
                    newNota=newNota+1
                try:
                    #Obtenemos al cliente
                    cliente = Clientes.objects.get(idCliente = venta['partner_id'][0])
                    #Sumamos una nueva venta en el cliente
                    cliente.numTransacciones=cliente.numTransacciones+1
                    if cliente.numTransacciones >= 2:
                        cliente.tipoCliente = 'Cartera'
                    else:
                        cliente.tipoCliente = 'Nuevo Cliente'
                    #Guardamos los cambios
                    cliente.save()
                except:
                    pass
            except:
                pass
    return({
        'status'  : 'success',
        'message' : f'{newVentas} ventas nuevas y {newNota} nuevas notas de credito'
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
                    'message' : response['message']
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
        
        #Traer todos los clientes de Odoo
        ventasOdoo=ctrVentas.get_newSales()
        
        if ventasOdoo['status'] == 'success':
            
            #Llama a insertVentas y le envia todos las ventas que obtuvo de Odoo
            response=insertVentas(ventasOdoo['ventas'])
            if response['status'] == "success":
                return JsonResponse({
                    'status'  : 'success',
                    'message' : response['message']
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
def createSalesExcel(request):
    try:
        
        #Traer todos los clientes de Odoo
        ventasOdoo=ctrVentas.pullVentasExcel()
        
        if ventasOdoo['status'] == 'success':
            
            #Llama a insertVentas y le envia todos las ventas que obtuvo de Odoo
            response=insertVentas(ventasOdoo['ventas'])
            if response['status'] == "success":
                return JsonResponse({
                    'status'  : 'success',
                    'message' : response['message']
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