from unidades.administracion.reporteVentas.models import VentasPVH, VentasPVA
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
def insertLineaVentaOdoo(productos, idVenta, fechaVenta, productosPSQL):
    #Para cada producto lo intentara registrar en VentasPVH y Ventas PVA
    for producto in productos:
        try:
            if producto['product_id']:
                #Obtiene el nombre del producto el limpio
                try:
                    productoObj = Productos.objects.get(idProducto=producto['product_id'][0])
                except:
                    try:
                        sku = "" if producto['name'].find("]") == -1 else producto['name'][1:producto['name'].find("]")]
                        productoObj = Productos.objects.get(sku=sku)
                    except Exception as e:
                        print("No se encontro", e, producto)
                if productoObj:
                    #Lo registra en ventasPVH
                    try:
                        VentasPVH.objects.create(
                            cantidad        = producto['quantity'],
                            precioUnitario  = producto['price_unit'],
                            subtotal        = producto['price_subtotal'],
                            marca           = productoObj.marca,
                            categoria       = productoObj.categoria,
                            venta           = idVenta,
                            nombre          = productoObj.nombre,
                            sku             = productoObj.sku
                        )
                    except Exception as e:
                        print("VentasPVH", e, producto)
                    
                    try:
                        VentasPVA.objects.create(
                            fecha           = fechaVenta,
                            cantidad        = producto['quantity'],
                            producto        = productoObj
                        )
                    except Exception as e:
                        print("VentasPVA", e, producto)
                        
            elif producto['product_id'] == False and (producto['price_subtotal'] != 0 or producto['price_unit'] != 0):
                try:
                    VentasPVH.objects.create(
                            cantidad        = producto['quantity'],
                            precioUnitario  = producto['price_unit'],
                            subtotal        = producto['price_subtotal'],
                            marca           = "",
                            categoria       = "",
                            venta           = idVenta,
                            nombre          = "",
                            sku             = ""
                        )
                except Exception as e:
                        print("Ventas sin Id", e, producto)
            else:
                print("El precio es 0: ", producto)
                
        except Exception as e:
            print("Error general: ", e, producto)
    #Retorna un exito                
    return({
        'status'  : 'success',
        'message' : f'Todos los productos han sido registrados'
    })   
    