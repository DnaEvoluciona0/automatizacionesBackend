from django.http import JsonResponse

from unidades.produccionLogistica.maxMin.models import Productos
from unidades.produccionLogistica.maxMin.controllers.ctrProducto import get_all_products, get_newproducts

#? Consultas a Base de datos PostgreSQL
#* Controlador para traer todos los productos de la base de datos
def getProductsPSQL(request):
    productsPSQL = Productos.objects.all().values(  'id', 'nombre', 'sku', 'marca', 
                   'existenciaActual', 'maxActual', 'minActual'  ) 
    return JsonResponse(list(productsPSQL), safe=False)




# --------------------------------------------------------------------------------------------------
# * Función: insertProducts
# * Descripción: Inserta productos en la base de datos PostgreSQL.
#
# ! Parámetros:
#     - Recibe una lista (array) de productos. Cada producto debe contener los siguientes campos:
#       { id, name, sku, maxActual, minActual, existenciaActual, marca, categoría, rutas, fechaCreacion }
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
    productsPSQL = Productos.objects.all().values_list('sku', flat=True)

    #añadir los productos a la base de datos de PostgreSQL
    new_products = []
    for product in products['products']:
        
        sku = product.get('sku', '').strip() if product['sku'] else ""
        marca = product.get('marca')
        categoria = product.get('categoria')
        rutas = len(product.get('routes'))

        if "MAQUILAS" in categoria[1] or "MT" in sku: 
            tipo = "MAQUILAS"
        elif "PC" in sku:
            tipo = "PRODUCTO COMERCIAL"
        elif "PT" in sku and rutas > 0:
            tipo = "INTERNO RESURTIBLE"
        elif "PT" in sku and rutas == 0:
            tipo = "INTERNO NO RESURTIBLE"
        else:
            tipo = "OTROS"
            
        if sku not in productsPSQL:
            new_products.append({
                'id' : product.get('id')
            })
            createProduct = Productos.objects.create(
                id = product.get('id'),
                sku = sku,
                nombre = product.get('name'),
                maxActual = product.get('maxActual'),
                minActual = product.get('minActual'),
                existenciaActual =  product.get('existenciaActual'),
                marca = marca[1] if marca else "",
                categoria = categoria[1],
                tipoProducto = tipo,
                fechaCreacion = product.get('fechaCreacion')
            )

    return ({
        'status'  : 'success',
        'message' : len(new_products)
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
        productsOdoo = get_all_products()
        #Realiza inserción de los datos

        if productsOdoo['status'] == 'success':
            response = insertProducts(productsOdoo)

            if response['status'] == "success":
                totalRows = response['message']
                return JsonResponse({
                    'status'  : 'success',
                    'message' : f'Se han agregado correctamente {totalRows} Productos nuevos'
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
        productsOdoo = get_all_products()

        if productsOdoo['status'] == 'success':
            # Diccionario de productos Odoo con su SKU como index
            odoo_dict = {p['sku']: p for p in productsOdoo['products']}
            #Productos almacenados en la base de datos PostgreSQL
            productsPSQL = list(Productos.objects.all())

            # Variable que almacena las actualizaciones de los productos
            updatedProducts = []
            for product in productsPSQL:
                odooProduct = odoo_dict.get(product.sku)

                if odooProduct:
                    sku = odooProduct.get('sku', '')
                    categoria = odooProduct.get('categoria', '')[1] if isinstance(odooProduct.get('categoria'), (list, tuple)) else ''
                    rutas = len(odooProduct.get('routes'))

                    if "MAQUILAS" in categoria or "MT" in sku: 
                        tipo = "MAQUILAS"
                    elif "PC" in sku:
                        tipo = "PRODUCTO COMERCIAL"
                    elif "PT" in sku and rutas > 0:
                        tipo = "INTERNO RESURTIBLE"
                    elif "PT" in sku and rutas == 0:
                        tipo = "INTERNO NO RESURTIBLE"
                    else:
                        tipo = "OTROS"

                    # Asigna los nuevos valores de Odoo a los productos de PostgreSQL
                    product.nombre           = odooProduct.get('name', '')
                    product.sku              = sku
                    product.marca            = odooProduct.get('marca', '')[1] if isinstance(odooProduct.get('marca'), (list, tuple)) else ''
                    product.maxActual        = odooProduct.get('maxActual', 0)
                    product.minActual        = odooProduct.get('minActual', 0)
                    product.existenciaActual = odooProduct.get('existenciaActual', 0)
                    product.categoria        = categoria
                    product.tipoProducto     = tipo
                    product.fechaCreacion    = odooProduct.get('fechaCreacion', '')

                    updatedProducts.append(product)
            
            # Actualiza la lista de productos con sus nuevos valores
            Productos.objects.bulk_update(updatedProducts, ['nombre', 'sku', 'marca', 'maxActual', 'minActual', 'existenciaActual', 'categoria', 'tipoProducto', 'fechaCreacion'])
            return JsonResponse({
                'status'  : 'success',
                'message' : f'Se han actualizado {len(updatedProducts)} correctamente'
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





# --------------------------------------------------------------------------------------------------
# * Función: createNewProductsFromOdoo
# * Descripción: Crea nuevos productos registrados en Odoo a PostgreSQL
#
# ! Parámetros:
#     - request. Como se utiliza para URLS, recibe la información de la consulta
# 
# ? Diferencia con la función pullProductsOdoo
#     - Esta hace llamada a get_newproducts del controlador, solo obteniendo los productos que se han creado 
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
        productsOdoo = get_newproducts()

        if productsOdoo['message'] == "success":

            response = insertProducts(productsOdoo)

            if response['status'] == "success":
                totalRows = response['message']
                return JsonResponse({
                    'status'  : 'success',
                    'message' : f'Se han agregado correctamente {totalRows} Productos nuevos'
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