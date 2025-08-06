from django.http import JsonResponse
from unidades.produccionLogistica.maxMin.models import MaterialPI, Productos, Insumos
from conexiones.conectionOdoo import OdooAPI
from unidades.produccionLogistica.maxMin.controllers.ctrMatrerialPI import getInsumoByProduct

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
        result = getInsumoByProduct()

        if result['status'] == 'success':

            MaterialPI.objects.all().delete()

            cantidad = 0
            for material in result['message']:
                productSKU = material.get('product')[1].split(']')[0]
                productSKU = productSKU.split('[')[1]
                materialSKU = material.get('material')[1].split(']')[0]
                materialSKU = materialSKU.split('[')[1]

                try: 
                    instanceProduct = Productos.objects.get(sku=f'{productSKU}')
                    
                except Productos.DoesNotExist:
                    continue

                try:
                    instanceInsumo = Insumos.objects.get(sku=f'{materialSKU}')
                except Insumos.DoesNotExist:
                    continue

                tupleMaterial = (Productos.objects.only('id').get(sku=productSKU).id, material.get('material')[0])

                if tupleMaterial:
                    try:
                        if instanceProduct and instanceInsumo:
                            cantidad += 1
                            materialPI = MaterialPI.objects.create(
                                producto = instanceProduct,
                                insumo = instanceInsumo,
                                cantidad = material.get('qty')
                            )
                    except:
                        print(f'Error al insertar el material {materialSKU} en el producto {productSKU}')
                        continue;
            return JsonResponse({
                'status' : 'success',
                'message' : f'Se han cargado {cantidad} materiales de productos.'
            })
        return JsonResponse({
            'status'  : 'error',
            'message' : result['message']
        })

    except Exception as e:
        return JsonResponse({
            'status'  : 'error',
            'message' : f'Ha ocurrido un error al tratar de insertar los datos: {str(e)}'
        })
    