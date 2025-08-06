from django.http import JsonResponse

from unidades.produccionLogistica.maxMin.models import Insumos
from unidades.produccionLogistica.maxMin.controllers.crtInsumo import get_all_insumos, updateMaxMinOdoo, get_newInsumos


# Create your views here.
#? Consultas a Base de datos PostgreSql
#* Controlador para obtener todos los insumos de la base de datos
def getInsumosPSQL(request):
    insumosPSQL = Insumos.objects.all().values(  'id', 'nombre', 'sku', 'marca', 'existenciaActual', 'maxActual', 'minActual'  )
    return JsonResponse(list(insumosPSQL), safe=False)



# --------------------------------------------------------------------------------------------------
# * Función: insertInputs
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
def insertInputs(inputs):
    #Traemos los insumos dentro de postgreSQL
    insumosPSQL = Insumos.objects.all().values_list('sku', flat=True)

    #Añadimos las insumos a la base de datos PosgreSQL
    new_insumos = []

    for insumo in inputs['products']:
        if insumo['sku']:
            sku = insumo.get('sku', '').strip()
            marca = insumo.get('marca')
            categoria = insumo.get('categoria')

            if sku and sku not in insumosPSQL:
                new_insumos.append({
                    'id' : insumo.get('id')
                })

                provider = len(insumo.get('proveedor'))
                
                if provider > 0:
                    proveedor = insumo.get('proveedor')
                    proveedorFinal = proveedor[0]['partner_id'][1]
                else:
                    proveedorFinal = ""
                
                createInsumo = Insumos.objects.create(
                    id = insumo.get('id'),
                    sku = sku,
                    nombre = insumo.get('name'),
                    maxActual = insumo.get('maxActual'),
                    minActual = insumo.get('minActual'),
                    existenciaActual = insumo.get('existenciaActual'),
                    marca = marca[1],
                    categoria = categoria[1],
                    proveedor = proveedorFinal,
                ) 
    
    return ({
        'status'  : 'success',
        'message' : f'Se han creado {len(new_insumos)} nuevos Insumos'
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
#           La función insertInputs retorna mensaje de error
#           Ocurre una excepción en la ejecución del código
#     - Caso succes:
#           La función insertInputs retorna mensaje success y envía mensaje con la cantidad de productos agregados
# --------------------------------------------------------------------------------------------------
def pullInsumosOdoo(request):
    
    try:
        #Traemos los insumos de Odoo
        insumosOdoo = get_all_insumos()

        if insumosOdoo['status'] == 'success':
            response = insertInputs(insumosOdoo)

            if response['status'] == "success":
                return JsonResponse({
                    'status' : 'success',
                    'message' : response['message']
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
#     - Debe de cumplir con la lógica y las condiciones de la función insertInputs
#     - La función modificará todos los campos del producto en cuestión a excepción del ID
#
# ? Returns:
#     - Caso error:
#           La función insertInputs retorna mensaje de error
#           Ocurre una excepción en la ejecución del código
#     - Caso succes:
#           La función insertInputs retorna mensaje success y envía mensaje con la cantidad de productos actualizados
# --------------------------------------------------------------------------------------------------
def updateInsumosOdoo(request):
    try:
        #? Traemos los insumos de odoo
        insumosOdoo = get_all_insumos()
        
        if insumosOdoo['status'] == 'success':
            odoo_dict = {i['sku']: i for i in insumosOdoo['products']}

            #?Traemos los productos de PostgreSQL
            insumosPSQL = list(Insumos.objects.all())
            
            insumosActualizados = []
            for insumo in insumosPSQL:
                odooInsumo = odoo_dict.get(insumo.sku)
                if odooInsumo:
                    insumo.nombre           = odooInsumo.get('name', '')
                    insumo.sku              = odooInsumo.get('sku', '')
                    insumo.marca            = odooInsumo.get('marca', '')[1] if isinstance(odooInsumo.get('marca'), (list, tuple)) else ''
                    insumo.maxActual        = odooInsumo.get('maxActual', 0)
                    insumo.minActual        = odooInsumo.get('minActual', 0)
                    insumo.existenciaActual = odooInsumo.get('existenciaActual', 0)
                    insumo.categoria        = odooInsumo.get('categoria', '')[1] if isinstance(odooInsumo.get('categoria'), (list, tuple)) else ''
                    insumo.proveedor        = odooInsumo.get('proveedor')[0]['partner_id'][1] if len(odooInsumo.get('proveedor')) > 0 else ''
                    insumo.tiempoEntrega    = odooInsumo.get('proveedor')[0]['delay'] if len(odooInsumo.get('proveedor')) > 0 else 0
                    insumosActualizados.append(insumo)

            Insumos.objects.bulk_update(insumosActualizados, ['nombre', 'sku', 'marca', 'maxActual', 'minActual', 'existenciaActual', 'categoria', 'proveedor', 'tiempoEntrega'])
            return JsonResponse({
                'status'  : 'success',
                'message' : f'Se han actualizado {len(insumosActualizados)} correctamente'
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
# * Función: createNewInsumosFromOdoo
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
#           La función insertInputs retorna mensaje de error
#           Ocurre una excepción en la ejecución del código
#     - Caso succes:
#           La función insertInputs retorna mensaje success y envía mensaje con la cantidad de productos actualizados
# --------------------------------------------------------------------------------------------------
def createNewInsumosFromOdoo(request):
    try:
        #traemos los productos nuevos de odoo
        insumosOdoo = get_newInsumos()
        if insumosOdoo['status'] == 'success':

            response = insertInputs(insumosOdoo)
            
            if response['status'] == "success":
                return JsonResponse({
                    'status' : 'success',
                    'message' : response['message']
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

        response = updateMaxMinOdoo(insumo.id, max, min)
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