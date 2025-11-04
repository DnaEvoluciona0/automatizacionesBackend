from django.http import JsonResponse

from unidades.produccionLogistica.maxMin.models import Productos
from unidades.produccionLogistica.maxMin.controllers import ctrInsumo

#? Consultas a Base de datos PostgreSql
#* Controlador para obtener todos los insumos de la base de datos
def getInsumosPSQL(request):
    insumosPSQL = Productos.objects.all().values(  'id', 'nombre', 'sku', 'marca', 'existenciaActual', 'maxActual', 'minActual'  )
    return JsonResponse(list(insumosPSQL), safe=False)



# --------------------------------------------------------------------------------------------------
# * Función: insertInsumos
# * Descripción: Inserta INSUMOS en la base de datos PostgreSQL.
#
# ! Parámetros:
#     - Recibe una lista (array) de insumos. Cada producto debe contener los siguientes campos:
#       { id, name, sku, maxActual, minActual, existenciaActual, marca, categoría, proveedor }
#     - Nota: Solo el campo "id" es obligatorio; los demás son opcionales. No todos los insumos tienen proveedor
#
# ? Condiciones para insertar un insumo en la base de datos:
#     1. El producto debe tener un SKU válido (no vacío).
#     2. El producto no debe existir previamente en la base de datos PostgreSQL.
# --------------------------------------------------------------------------------------------------
def insertInsumos(insumos):
    #Traemos los insumos dentro de postgreSQL
    insumosPSQL = Productos.objects.all().values_list('idProductoTmp', flat=True)

    #Añadimos las insumos a la base de datos PosgreSQL
    new_insumos = 0
    for insumo in insumos:
        
        if insumo['id'] not in insumosPSQL:
            
            sku = insumo['default_code'] if insumo['default_code'] else ""
            marca = insumo['product_brand_id'][1] if insumo['product_brand_id'] else ""
            categoria = insumo['categ_id'][1]
            rutas = len(insumo['route_ids'])

            if insumo['active']==False:
                tipo = "DESCONTINUADO"
            else:
                if "MAQUILA" in categoria or "MT" in sku: 
                    tipo = "MAQUILAS"
                elif rutas > 0 and insumo['purchase_ok'] == True and insumo['active'] == True:
                    tipo = "RESURTIBLE"
                elif rutas == 0 or insumo['purchase_ok'] == False or insumo['active'] == False:
                    tipo = "NO RESURTIBLE"
                else:
                    tipo = "OTROS"
            
            createInsumo = Productos.objects.create(
                idProductoTmp = insumo['id'],
                idProducto = insumo['product_variant_id'][0] if insumo['product_variant_id'] else 0,
                nombre = insumo['name'],
                sku = sku,
                marca = marca,
                maxActual = insumo['product_max_qty'],
                minActual = insumo['product_min_qty'],
                existenciaActual = insumo['qty_available'],
                existenciaOC = insumo['oc'],
                categoria = categoria,
                tipo = tipo,
                fechaCreacion = insumo['create_date'],
                proveedor = insumo['provider'],
                tiempoEntrega = insumo['delay']
            )
            new_insumos+=1
    
    return ({
        'status'  : 'success',
        'message' : new_insumos
    })





# --------------------------------------------------------------------------------------------------
# * Función: pullInsumosOdoo
# * Descripción: Obtiene todos los insumos de Odoo y llama a la función correspondiente para insertart datos
# * Maneja posibles excepciones
#
# ! Parámetros:
#     - request. Como se utiliza para URLS, recibe la información de la consulta
#
# ? Returns:
#     - Caso error:
#           Ocurre algún error en traer los insumo de Odoo
#           La función insertInsumos retorna mensaje de error
#           Ocurre una excepción en la ejecución del código
#     - Caso succes:
#           La función insertInsumos retorna mensaje success y envía mensaje con la cantidad de productos agregados
# --------------------------------------------------------------------------------------------------
def pullInsumosOdoo(request):
    
    try:
        #Traemos los insumos de Odoo
        insumosOdoo = ctrInsumo.get_allInsumos()

        if insumosOdoo['status'] == 'success':
            
            response = insertInsumos(insumosOdoo['products'])
            
            if response['status'] == "success":
                total = response['message']
                return JsonResponse({
                    'status' : 'success',
                    'message' : f'Se han agregado correctamente {total} insumos de {len(insumosOdoo["products"])}'
                })

        else: 
            return JsonResponse({
                'status'  : 'error',
                'message' : insumosOdoo['message']
            })

    except Exception as e:
        return JsonResponse({
            'status'  : 'error',
            'message' : f'Ha ocurrido un error al tratar de insertar los datos {str(e)}'
        })
        
        
        
        
    
# --------------------------------------------------------------------------------------------------
# * Función: createInsumosOdoo
# * Descripción: Crea nuevos insumos registrados en Odoo a PostgreSQL
#
# ! Parámetros:
#     - request. Como se utiliza para URLS, recibe la información de la consulta
# 
# ? Diferencia con la función pullProductsOdoo
#     - Esta hace llamada a get_newInsumos del controlador, solo obteniendo los insumos que se han creado 
#           el día anterior a la ejecución del código
#
# ? Returns:
#     - Caso error:
#           Ocurre error al obtener los nuevos insumos
#           La función insertInsumos retorna mensaje de error
#           Ocurre una excepción en la ejecución del código
#     - Caso succes:
#           La función insertInsumos retorna mensaje success y envía mensaje con la cantidad de productos actualizados
# --------------------------------------------------------------------------------------------------
def createInsumosOdoo(request):
    try:
        #traemos los productos nuevos de odoo
        insumosOdoo = ctrInsumo.get_newInsumos()
        if insumosOdoo['status'] == 'success':

            response = insertInsumos(insumosOdoo['products'])
            
            if response['status'] == "success":
                total = response['message']
                return JsonResponse({
                    'status' : 'success',
                    'message' : f'Se han agregado correctamente {total} nuevos insumos de {len(insumosOdoo["products"])}'
                }) 
            
        return JsonResponse({
            'status'  : 'error',
            'message' : insumosOdoo['message']
        })
    except Exception as e:
        return JsonResponse({
            'status'  : 'error',
            'message' : f'Ha ocurrido un error al tratar de insertar los datos: {str(e)}'
        })        




# --------------------------------------------------------------------------------------------------
# * Función: updateInsumosOdoo
# * Descripción: Actualiza los insumos registrados de PostgreSQL conforme a los datos de Odoo
#
# ! Parámetros:
#     - request. Como se utiliza para URLS, recibe la información de la consulta
#
# ? Condiciones de la actualización
#     - Siempre actualizará todos los insumos registrados en Odoo y que existan en la base de datos PostgreSQL, 
#       esto debido a que no hay una forma clara de obtener la información necesaria de Odoo de los campos 
#       actualizados y qué insumos han sido actualizados y cuáles no
#       !Nota: Está función puede actualizarse y optimizarse resolviendo esta problemática.
#     - Debe de cumplir con la lógica y las condiciones de la función insertInsumos
#     - La función modificará todos los campos del producto en cuestión a excepción del ID
#
# ? Returns:
#     - Caso error:
#           La función insertInsumos retorna mensaje de error
#           Ocurre una excepción en la ejecución del código
#     - Caso succes:
#           La función insertInsumos retorna mensaje success y envía mensaje con la cantidad de productos actualizados
# --------------------------------------------------------------------------------------------------
def updateInsumosOdoo(request):
    try:
        #? Traemos los insumos de odoo
        insumosOdoo = ctrInsumo.get_allInsumos()
        
        if insumosOdoo['status'] == 'success':
            updatedInsumos=0
            
            for insumo in insumosOdoo['products']:
                try:
                    #Busca el ID del insumo en Postgres
                    insumoObj = Productos.objects.get(idProductoTmp=insumo['id'])
                    
                    sku = insumo['default_code'] if insumo['default_code'] else ""
                    marca = insumo['product_brand_id'][1] if insumo['product_brand_id'] else ""
                    categoria = insumo['categ_id'][1]
                    rutas = len(insumo['route_ids'])

                    if insumo['active']==False:
                        tipo = "DESCONTINUADO"
                    else:
                        if "MAQUILAS" in categoria or "MT" in sku: 
                            tipo = "MAQUILAS"
                        elif "PC" in sku:
                            tipo = "PRODUCTO COMERCIAL"
                        elif "PT" in sku and rutas > 0 and insumo['purchase_ok'] == True and insumo['active'] == True:
                            tipo = "RESURTIBLE"
                        elif "PT" in sku and (rutas == 0 or insumo['purchase_ok'] == False or insumo['active'] == False):
                            tipo = "NO RESURTIBLE"
                        else:
                            tipo = "OTROS"

                    # Asigna los nuevos valores de Odoo a los insumos de PostgreSQL
                    insumoObj.nombre           = insumo['name']
                    insumoObj.sku              = sku
                    insumoObj.marca            = marca
                    insumoObj.maxActual        = insumo['product_max_qty']
                    insumoObj.minActual        = insumo['product_min_qty']
                    insumoObj.existenciaActual = insumo['qty_available']
                    insumoObj.existenciaOC     = insumo['oc']
                    insumoObj.categoria        = categoria
                    insumoObj.tipo             = tipo
                    insumoObj.proveedor        = insumo['provider']
                    insumoObj.tiempoEntrega    = insumo['delay']

                    insumoObj.save()
                    updatedInsumos+=1
                except:
                    pass
            
            return JsonResponse({
                'status'  : 'success',
                'message' : f'Se han actualizado correctamente {updatedInsumos} insumos de {len(insumosOdoo["products"])}'
            })
        return JsonResponse({
            'status'  : 'error',
            'message' : f"Error en realizar la consulta a Odoo: {insumosOdoo['message']} "
        })
    except Exception as e:
        return JsonResponse({
            'status'  : 'error',
            'message' : f'Ha ocurrido un error al tratar de insertar los datos {str(e)}'
        })





# --------------------------------------------------------------------------------------------------
# * Función: updateMaxMin
# * Descripción: Actualiza máximos y mínimos de la base de datos de PostgreSQL y llama a la función para
# *              actualizar los valores de la base de datos de Odoo
#
# ! Parámetros:
#     - insumo, objeto de tipo Insumo, de aqui optiene el id del insumo a actualizar
#     - max, cantidad maxima nueva
#     - min, cantidad minima nueva
#
# ? Returns:
#     - Caso error:
#           Ocurre error al modificar la regla en odoo
#           Ocurre una excepción en la ejecución del código
#     - Caso succes:
#           Se modifican correctamente los valores tanto en Odoo como en PostgreSQL
# --------------------------------------------------------------------------------------------------
def updateMaxMin(insumo, max, min):
    try:

        response = ctrInsumo.updateMaxMinOdoo(insumo.id, max, min)
        if response['status'] == 'success':

            insumo.maxActual = int(round(max))
            insumo.minActual = int(round(min))

            insumo.save(update_fields=['maxActual', 'minActual'])
        
            return ({
                'status'  : 'success',
                'message' : f'Se ah actualizado correctamente el insumo {insumo.nombre}'
            })

        return ({
            'status'  : 'error',
            'message' : response['message']
        })

    except Exception as e:
        return ({
            'status'  : 'error',
            'message' : f'Ha ocurrido un error al tratar de insertar los datos {str(e)}'
        })