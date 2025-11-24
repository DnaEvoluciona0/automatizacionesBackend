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
def pullMaterialPIOdoo(request):
    try:
        materialPI = ctrMaterialPI.getInsumoByProduct()
        materiales = {m.idProductoTmp: m for m in Productos.objects.all()}
        materialesAssign = []
        assignedMateriales = 0

        if materialPI['status'] == 'success':

            MaterialPI.objects.all().delete()

            for material in materialPI['materiales']:
                    padreId = materiales.get(material['parent_product_tmpl_id'][0])
                    hijoId = materiales.get(material['product_tmpl_id'][0])
                    
                    materialesAssign.append(
                        MaterialPI(
                            idMaterialPI = material['id'],
                            padre = padreId,
                            hijo = hijoId,
                            cantidad = material['product_qty']
                        )
                    )
                    
            try:
                MaterialPI.objects.bulk_create(materialesAssign, batch_size=1000)
                assignedMateriales+=len(materialesAssign)
            except:
                try:
                    for material in materialesAssign:
                        material.save()
                        assignedMateriales+=1
                except Exception as e:
                    print("Error en viewsMaterialPI.pullMaterialPi | Material no se inserto: ", e, material)
                    
            return JsonResponse({
                'status' : 'success',
                'message' : f'Se han cargado {assignedMateriales} materiales de productos de {len(materialPI["materiales"])}'
            })
        return JsonResponse({
            'status'  : 'error',
            'message' : materialPI['materiales']
        })

    except Exception as e:
        return JsonResponse({
            'status'  : 'error',
            'message' : f'Ha ocurrido un error al tratar de insertar los datos: {str(e)}'
        })
    