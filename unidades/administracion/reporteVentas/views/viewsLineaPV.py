from unidades.administracion.reporteVentas.models import VentasPVH, VentasPVA
from unidades.produccionLogistica.maxMin.models import Insumos, Productos

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
def insertLineaVentaOdoo(productos, idVenta, fechaVenta, productosPSQL, insumosPSQL):
    try:
        #Para cada producto lo intentara registrar en VentasPVH y Ventas PVA
        for producto in productos:
            if producto['name']!=False or producto['product_id']!=False:
                #Obtiene el nombre del producto el limpio
                nombreP = producto['name'] if producto['name'].find("]") == -1 else producto['name'][producto['name'].find("]")+2:]
                #Obtiene el SKU del producto
                skuP = "" if producto['name'].find("]") == -1 else producto['name'][1:producto['name'].find("]")]
                
                if len(nombreP) <= 100:
                    #Lo registra en ventasPVH  
                    VentasPVH.objects.create(
                        cantidad        = producto['quantity'],
                        precioUnitario  = producto['price_unit'],
                        subtotal        = producto['price_subtotal'],
                        marca           = producto['x_studio_marca'] if producto['x_studio_marca'] else "",
                        categoria       = producto['x_studio_related_field_e1jP7'] if producto['x_studio_related_field_e1jP7'] else "",
                        idVenta_id      = idVenta,
                        nombre          = nombreP,
                        sku             = skuP
                    )
                    
                    #Si el producto se encuentra en la lista de productos o de insumos en Postgres, entra en este if
                    if producto['product_id'] != False:
                        if producto['product_id'][0] in productosPSQL or producto['product_id'][0] in insumosPSQL:
                            #Intentar registrarlo como producto
                            try:
                                try:
                                    #Si el producto si tiene un id de producto lo registra
                                    VentasPVA.objects.create(
                                        fecha           = fechaVenta,
                                        cantidad        = producto['quantity'],
                                        idProducto_id   = producto['product_id'][0]
                                    )
                                except:
                                    #Si el producto no tenia un id de producto lo busca con base a su SKU y obtiene el id, este esta principalmente pensado para los productos de Excel/contpaq
                                    posibleID=Productos.objects.get(sku=skuP)
                                    VentasPVA.objects.create(
                                        fecha           = fechaVenta,
                                        cantidad        = producto['quantity'],
                                        idProducto_id   = posibleID.id
                                    )
                            #Intentar registrarlo como Insumo
                            except:
                                try:
                                    #Si el insumo si tiene un id de producto lo registra
                                    VentasPVA.objects.create(
                                        fecha           = fechaVenta,
                                        cantidad        = producto['quantity'],
                                        idInsumo_id     = producto['product_id'][0]
                                    )
                                except:
                                    #Si el insumo no tenia un id de producto lo busca con base a su SKU y obtiene el id, este esta principalmente pensado para los insumos de Excel/contpaq
                                    posibleID=Insumos.objects.get(sku=skuP)
                                    VentasPVA.objects.create(
                                        fecha           = fechaVenta,
                                        cantidad        = producto['quantity'],
                                        idInsumo_id     = posibleID.id
                                    )
                        else:
                            try:
                                try:
                                    #Si el producto no tenia un id de producto lo busca con base a su SKU y obtiene el id, este esta principalmente pensado para los productos de Excel/contpaq
                                    posibleID=Productos.objects.get(sku=skuP)
                                    VentasPVA.objects.create(
                                        fecha           = fechaVenta,
                                        cantidad        = producto['quantity'],
                                        idProducto_id   = posibleID.id
                                    )
                                except:
                                    #Si el insumo no tenia un id de producto lo busca con base a su SKU y obtiene el id, este esta principalmente pensado para los insumos de Excel/contpaq
                                    posibleID=Insumos.objects.get(sku=skuP)
                                    VentasPVA.objects.create(
                                        fecha           = fechaVenta,
                                        cantidad        = producto['quantity'],
                                        idInsumo_id     = posibleID.id
                                    )
                            except:
                                pass
        #Retorna un exito                
        return({
            'status'  : 'success',
            'message' : f'Todos los productos han sido registrados'
        })   
        
    except Exception as e:
        pass
    