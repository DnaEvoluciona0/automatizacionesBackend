from django.http import JsonResponse
from unidades.produccionLogistica.maxMin.models import MaterialPI, Productos
from unidades.produccionLogistica.maxMin.controllers import ctrMaterialPI

# Create your views here.

#? Consultas a base de datos PostgreSQL
#* Controlador para traer todos los materialesPI de la base de datos
def getMaterialsPIPSQL(request):
    materialsPIPSQL = MaterialPI.objects.all().values(  'id', 'producto', 'insumo', 'cantidad'  )
    return JsonResponse(list(materialsPIPSQL), safe=False)


# --------------------------------------------------------------------------------------------------
# * Función: pullMaterialPi
# * Descripción: Agrega los datos de materiales Productos * Insumos
#
# ! Parámetros:
#     - request. Como se utiliza para URLS, recibe la información de la consulta
#
# ? Condiciones para insertar un MaterialPI en la base de datos:
#     1. El producto e Insumo deben de existir en sus respectivas tablas
#     2. Siempre que hace la inserción de materiales, borra los datos ya existentes, esto debido a que no se 
#        se ha encontrado una forma de realizar actualizaciones
#       !Nota: Está función puede actualizarse y optimizarse resolviendo esta problemática.
#
# ? Returns
#     - Caso error:
#           
# --------------------------------------------------------------------------------------------------
def pullMaterialPi(request):

    try:
        result = ctrMaterialPI.getInsumoByProduct()

        if result['status'] == 'success':

            MaterialPI.objects.all().delete()

            cantidadPI = 0
            for material in result['materiales']:
                try:
                    padreId = Productos.objects.get(idProductoTmp=material['parent_product_tmpl_id'][0])
                    
                    hijoId = Productos.objects.get(idProductoTmp=material['product_tmpl_id'][0])
                    
                    createMaterialPI = MaterialPI.objects.create(
                        idPadre = padreId,
                        idHijo = hijoId,
                        cantidad = material['product_qty']
                    )
                    cantidadPI+=1
                except:
                    pass
                    
            return JsonResponse({
                'status' : 'success',
                'message' : f'Se han cargado {cantidadPI} materiales de productos de {len(result['materiales'])}'
            })
        return JsonResponse({
            'status'  : 'error',
            'message' : result['materiales']
        })

    except Exception as e:
        return JsonResponse({
            'status'  : 'error',
            'message' : f'Ha ocurrido un error al tratar de insertar los datos: {str(e)}'
        })
    