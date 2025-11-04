from django.http import JsonResponse

from unidades.produccionLogistica.maxMin.models import Productos
from unidades.produccionLogistica.maxMin.controllers import ctrProducto

#? Consultas a Base de datos PostgreSQL
#* Controlador para traer todos los productos de la base de datos
def getProductsPSQL(request):
    productsPSQL = Productos.objects.all().values(  'id', 'nombre', 'sku', 'marca', 'existenciaActual'  ) 
    return JsonResponse(list(productsPSQL), safe=False)




# --------------------------------------------------------------------------------------------------
# * Función: insertProducts
# * Descripción: Inserta productos en la base de datos PostgreSQL.
#
# ! Parámetros:
#     - Recibe una lista (array) de productos. Cada producto debe contener los siguientes campos:
#       { id, name, sku, existenciaActual, marca, categoría, rutas, fechaCreacion }
#     - Nota: Solo el campo "id" es obligatorio; los demás son opcionales.
#
# ? Condiciones para insertar un producto en la base de datos:
#     1. El producto debe tener un SKU válido (no vacío).
#     2. El producto no debe existir previamente en la base de datos PostgreSQL.
#
# ? Lógica para determinar el tipo de producto:
#     - Si la categoría contiene "MAQUILAS" o el SKU contiene "MT" → Tipo: MAQUILAS.
#     - Si el SKU contiene "PC" → Tipo: PRODUCTO COMERCIAL.
#     - Si el SKU contiene "PT":
#         · Si contiene una o más rutas → Tipo: INTERNO RESURTIBLE.
#         · Si no contiene rutas → Tipo: INTERNO NO RESURTIBLE.
#     - Si no cumple con ninguna de las condiciones anteriores → Tipo: OTROS.
# --------------------------------------------------------------------------------------------------
def insertProducts(products):
    #traemos los productos existentes de PostgreSQL
    productsPSQL = Productos.objects.all().values_list('idProductoTmp', flat=True)

    #añadir los productos a la base de datos de PostgreSQL
    new_products = 0
    for product in products:
        
        if product['id'] not in productsPSQL:
        
            sku = product['default_code'] if product['default_code'] else ""
            marca = product['product_brand_id'][1] if product['product_brand_id'] else ""
            categoria = product['categ_id'][1]
            rutas = len(product['route_ids'])

            if product['active']==False:
                tipo = "DESCONTINUADO"
            else:
                if "MAQUILAS" in categoria or "MT" in sku: 
                    tipo = "MAQUILAS"
                elif "PC" in sku:
                    tipo = "PRODUCTO COMERCIAL"
                elif "PT" in sku and rutas > 0 and product['sale_ok'] == True and product['active'] == True:
                    tipo = "RESURTIBLE"
                elif "PT" in sku and (rutas == 0 or product['sale_ok'] == False or product['active'] == False):
                    tipo = "NO RESURTIBLE"
                else:
                    tipo = "OTROS"
            
            createProduct = Productos.objects.create(
                idProductoTmp = product['id'],
                idProducto = product['product_variant_id'][0] if product['product_variant_id'] != False else 0,
                sku = sku,
                nombre = product['name'],
                existenciaActual =  product['qty_available'],
                marca = marca,
                categoria = categoria,
                tipo = tipo,
                fechaCreacion = product['create_date']
            )
            new_products+=1

    return ({
        'status'  : 'success',
        'message' : new_products
    })





# --------------------------------------------------------------------------------------------------
# * Función: pullProductsOdoo
# * Descripción: Obtiene todos los productos de Odoo y llama a la función correspondiente para insertart datos
# * Maneja posibles excepciones
#
# ! Parámetros:
#     - request. Como se utiliza para URLS, recibe la información de la consulta
#
# ? Returns:
#     - Caso error:
#           Ocurre algún error en traer los productos de Odoo
#           La función insertProducts retorna mensaje de error
#           Ocurre una excepción en la ejecución del código
#     - Caso succes:
#           La función insertProducts retorna mensaje success y envía mensaje con la cantidad de productos agregados
# --------------------------------------------------------------------------------------------------
def pullProductsOdoo(request):
    try:
        #Prductos de Odoo
        productsOdoo = ctrProducto.get_allProducts()
        #Realiza inserción de los datos
        
        if productsOdoo['status'] == 'success':
            response = insertProducts(productsOdoo['products'])

            if response['status'] == "success":
                totalRows = response['message']
                return JsonResponse({
                    'status'  : 'success',
                    'message' : f'Se han agregado correctamente {totalRows} productos de {len(productsOdoo["products"])}'
                })

            return JsonResponse({
                'status'  : 'error',
                'message' : response['message']
            })
        
        return JsonResponse({
            'status'  : 'error',
            'message' : productsOdoo['message']
        })
    
    except Exception as e:
        return JsonResponse({
            'status'  : 'error',
            'message' : f'Ha ocurrido un error al tratar de insertar los datos: {str(e)}'
        })





# --------------------------------------------------------------------------------------------------
# * Función: createNewProductsFromOdoo
# * Descripción: Crea nuevos productos registrados en Odoo a PostgreSQL
#
# ! Parámetros:
#     - request. Como se utiliza para URLS, recibe la información de la consulta
# 
# ? Diferencia con la función pullProductsOdoo
#     - Esta hace llamada a get_newProducts del controlador, solo obteniendo los productos que se han creado 
#           el día anterior a la ejecución del código
#
# ? Returns:
#     - Caso error:
#           Ocurre error al obtener los nuevos productos
#           La función insertProducts retorna mensaje de error
#           Ocurre una excepción en la ejecución del código
#     - Caso succes:
#           La función insertProducts retorna mensaje success y envía mensaje con la cantidad de productos actualizados
# --------------------------------------------------------------------------------------------------
def createNewProductsFromOdoo(request):
    try:     
        #Traer los productos que existen de odoo        
        productsOdoo = ctrProducto.get_newProducts()
        if productsOdoo['status'] == "success":

            response = insertProducts(productsOdoo['products'])

            if response['status'] == "success":
                totalRows = response['message']
                return JsonResponse({
                    'status'  : 'success',
                    'message' : f'Se han agregado correctamente {totalRows} nuevos productos de {len(productsOdoo["products"])}'
                })

            return JsonResponse({
                'status'  : 'error',
                'message' : response['message']
            })

        return JsonResponse({
            'status'  : 'error',
            'message' : productsOdoo['message']
        })
    
    except Exception as e:
        return JsonResponse({
            'status'  : 'error',
            'message' : f'Ha ocurrido un error al tratar de insertar los datos: {str(e)}'
        })
        
        
        
        
        
        
# --------------------------------------------------------------------------------------------------
# * Función: updateProducts
# * Descripción: Actualiza los productos registrados de PostgreSQL conforme a los datos de Odoo
#
# ! Parámetros:
#     - request. Como se utiliza para URLS, recibe la información de la consulta
#
# ? Condiciones de la actualización
#     - Siempre actualizará todos los productos registrados en Odoo y que existan en la base de datos PostgreSQL, 
#       esto debido a que no hay una forma clara de obtener la información necesaria de Odoo de los campos 
#       actualizados y qué productos han sido actualizados y cuáles no
#       !Nota: Está función puede actualizarse y optimizarse resolviendo esta problemática.
#     - Debe de cumplir con la lógica y las condiciones de la función insertProducts
#     - La función modificará todos los campos del producto en cuestión a excepción del ID
#
# ? Returns:
#     - Caso error:
#           La función insertProducts retorna mensaje de error
#           Ocurre una excepción en la ejecución del código
#     - Caso success:
#           La función insertProducts retorna mensaje success y envía mensaje con la cantidad de productos actualizados
# --------------------------------------------------------------------------------------------------
def updateProducts(request):
    try:
        # Productos de Odoo
        productsOdoo = ctrProducto.get_allProducts()

        if productsOdoo['status'] == 'success':
            updatedProducts=0
            
            for product in productsOdoo['products']:
                try:
                    #Busca el ID del producto en Postgres
                    productoObj = Productos.objects.get(idProductoTmp=product['id'])
                    
                    sku = product['default_code'] if product['default_code'] else ""
                    categoria = product['categ_id'][1] if product['categ_id'] else ""
                    rutas = len(product['route_ids'])

                    if product['active']==False:
                        tipo = "DESCONTINUADO"
                    else:
                        if "MAQUILAS" in categoria or "MT" in sku: 
                            tipo = "MAQUILAS"
                        elif "PC" in sku:
                            tipo = "PRODUCTO COMERCIAL"
                        elif "PT" in sku and rutas > 0 and product['sale_ok'] == True and product['active'] == True:
                            tipo = "RESURTIBLE"
                        elif "PT" in sku and (rutas == 0 or product['sale_ok'] == False or product['active'] == False):
                            tipo = "NO RESURTIBLE"
                        else:
                            tipo = "OTROS"

                    # Asigna los nuevos valores de Odoo a los productos de PostgreSQL
                    productoObj.nombre           = product['name']
                    productoObj.sku              = sku
                    productoObj.marca            = product['product_brand_id'][1] if product['product_brand_id'] else ''
                    productoObj.existenciaActual = product['qty_available']
                    productoObj.categoria        = categoria
                    productoObj.tipo             = tipo

                    productoObj.save()
                    updatedProducts+=1
                except:
                    pass
                    
            return JsonResponse({
                'status'  : 'success',
                'message' : f'Se han actualizado correctamente {updatedProducts} productos de {len(productsOdoo["products"])}'
            })

        return JsonResponse({
            'status'  : 'error',
            'message' : f"Error en realizar la consulta a Odoo: {productsOdoo['message']}"
        })
    except Exception as e:
        return JsonResponse({
            'status'  : 'error',
            'message' : f'Ha ocurrido un error al tratar de insertar los datos: {str(e)}'
        })