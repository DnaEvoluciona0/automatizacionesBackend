from unidades.administracion.reporteVentas.models import VentasPVH, Ventas
from unidades.produccionLogistica.maxMin.models import Productos

# --------------------------------------------------------------------------------------------------
# * Función: insertLineaVentaOdoo
# * Descripción: Obtiene las lineas ventas de la base de datos de Odoo o de excel y los inserta en la base de datos de PostgreSQL
#
# ! Parámetros:
#     - Recibe un array de linea de venta, donde cada indice del array debe contener la siguiente informacion:
#           {  idProducto, nombreProducto, cantidad, precioUnitario, precioSubtotal, marca, categoria  }
#     - Recibe el idVenta de donde vienen los productos
#     - Recobe la fecha en que se hizo la venta
#     - Recibe la lista de Productos disponibles en odoo y la de insumos disponibles
#
# ? Condiciones para insertar una venta:
#     1. Para PVH no hay ninguna condicion 
#     2. Para PVA la primera condicion es que el id del producto exista en la base de datos de Postgres o si es de un excel que el sku exista en la BD, si no se encuentra no lo registra
#     3. Además si encuentra el Id en ambos casos intenta registrarlo con la llave foranea de Productos y si no lo encuentra en la tabla de productos lo intenta registrar en la llave foranea de Insumos, si no puede no lo registra
#       
#
# ? Lógica para determinar el venta:
#     - Si "move_type" es igual a "out_invoice", significa que es una venta completada.
#     - Si "move_type" es igual a "out_refund", significa que es una nota de crédito.
# --------------------------------------------------------------------------------------------------
def insertLineaVentaOdoo(productos):
    
    '''    
    subtotal = producto['price_subtotal'] if IDVenta.idVenta[0] != 'R' else (producto['price_subtotal']*(-1))
    '''
    ventasObj = {v.idVenta: v for v in Ventas.objects.all()}
    productos_id = {p.idProducto: p for p in Productos.objects.all()}
    productos_tmp_id = {p.idProductoTmp: p for p in Productos.objects.all()}
    
    lineasCreate=[]
    newLines = 0
    #Para cada producto lo intentara registrar en VentasPVH y Ventas PVA
    for producto in productos:
        if producto['product_id']:
            #Obtiene el nombre del producto el limpio
            productoObj = productos_id.get(producto['product_id'][0])
            
            ventaObj = ventasObj.get(producto['move_name'])
                    
            #Lo registra en ventasPVH
            lineasCreate.append(
                VentasPVH(
                    cantidad        = producto['quantity'],
                    precioUnitario  = producto['price_unit'],
                    subtotal        = producto['price_subtotal'] if ventaObj.idVenta[0] != 'R' else (producto['price_subtotal']*(-1)),
                    venta           = ventaObj,
                    producto        = productoObj
                )       
            )   
        
        else:
            lineasCreate.append(
                VentasPVH(
                    cantidad        = producto['quantity'],
                    precioUnitario  = producto['price_unit'],
                    subtotal        = producto['price_subtotal'] if ventaObj.idVenta[0] != 'R' else (producto['price_subtotal']*(-1)),
                    venta           = ventaObj
                )       
            ) 
    try:
        VentasPVH.objects.bulk_create(lineasCreate, batch_size=1000)
        newLines+=len(lineasCreate)
    except Exception as e:
        print('entre al error en lineaPV', e)
        try:
            for linea in lineasCreate:
                linea.save()
                newLines+=1
        except Exception as e:
            print("Error en viewsLineaPV.insertLineaVentaOdoo | VentaPVH no se inserto: ", e, producto)
                
    #Retorna un exito                
    return({
        'status'  : 'success',
        'message' : f'Todos los productos han sido registrados'
    })   
    