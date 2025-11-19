from django.http import JsonResponse
from unidades.administracion.reporteVentas.controllers import ctrCaducidades
from unidades.administracion.reporteVentas.models import Productos, Caducidades
from datetime import datetime


# --------------------------------------------------------------------------------------------------
# * Función: insertCaducidades
# * Descripción: Inserta las caducidades en la base de datos PostgreSQL.
#
# ! Parámetros:
#     - Recibe una lista (array) de ID de producto.
#     - Recibe una lista (array) de caducidades que deben tener:
#           { id, name, product_id, product_qty }
#
# ? Condiciones para insertar un producto en la base de datos:
#     1. Que su nombre sea convertible a fecha válida
#
# --------------------------------------------------------------------------------------------------
def insertCaducidades(productos, caducidades):
    caducidadesPSQL = Caducidades.objects.all().values_list('idCaducidad', flat=True)
    
    productosObj = {p.idProducto: p for p in Productos.objects.all()}
    caducidadesCreate = []
    newCaducidad=0
    for caducidad in caducidades:
        
        if caducidad['product_id'][0] in productos and caducidad['id'] not in caducidadesPSQL:
            #Convierte el nombre en una fecha válida
            try:
                fecha = datetime.strptime(caducidad['name'].strip().replace('–', '-').replace('—', '-').replace('‑', '-'), "%d-%m-%Y")
                productoObj = productosObj.get(caducidad['product_id'][0])
                #Inserta la informacion en la tabla Caducidades
                caducidadesCreate.append(
                    Caducidades(
                        idCaducidad = caducidad['id'],
                        fechaCaducidad = fecha,
                        cantidad = caducidad['product_qty'],
                        producto = productoObj
                    )
                )
            except:
                pass
    
    try:
        Caducidades.objects.bulk_create(caducidadesCreate, batch_size=1000)
        newCaducidad+=len(caducidadesCreate)
    except:
        try:
            for caducidades in caducidadesCreate:
                caducidades.save()
                newCaducidad+=1
        except Exception as e:
            print("Error en viewsCaducidades.insertCaducidades | Caducidad con idProducto no se inserto: ", e, caducidad)
            
    return({
        'status': 'success',
        'message': newCaducidad
    })
    
# --------------------------------------------------------------------------------------------------
# * Función: pullCaducidadesOdoo
# * Descripción: Obtiene todos los lotes/caducidades de los productos de Odoo
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
#           La función retorna todas las caducidades que se hayan hecho en Odoo
# --------------------------------------------------------------------------------------------------
def pullCaducidadesOdoo(request):
    try:
        #Obtiene el id de todos los productos que hay en Postgres
        productsPSQL = Productos.objects.all().values_list('idProducto', flat=True)
        
        #Obtiene todas las caducidades que hay en Odoo
        caducidadesOdoo=ctrCaducidades.get_allCaducidades()
        
        if caducidadesOdoo['status'] == 'success':
            #Llama a la funcion insert caducidades y le pasa la lista de ID's y las caducidades de Odoo
            response=insertCaducidades(productsPSQL, caducidadesOdoo['caducidades'])
            
            if response['status'] == 'success':     
                message = response['message']
                return JsonResponse({
                    'status'  : 'success',
                    'message' : f'Se registraron {message} caducidades de {len(caducidadesOdoo['caducidades'])}'
                })
            return JsonResponse({
                    'status'  : 'error',
                    'message' : response['message']
                })
        else:
            return JsonResponse({
                'status'  : 'error',
                'message' : caducidadesOdoo['message']
            })
        
    except Exception as e:
        return JsonResponse({
            'status'  : 'error',
            'message' : f'Ha ocurrido un error al tratar de insertar los datos: {e}'
        })
        

# --------------------------------------------------------------------------------------------------
# * Función: createCaducidadesOdoo
# * Descripción: Obtiene todos los lotes/caducidades de los productos de Odoo que se hayan creado un dia antes
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
#     - Caso success:
#           La función retorna todas las caducidades que se hayan hecho en Odoo
# --------------------------------------------------------------------------------------------------
def createCaducidadesOdoo(request):
    try:
        #Obtiene el id de todos los productos que hay en Postgres
        productsPSQL = Productos.objects.all().values_list('idProducto', flat=True)
        caducidadesIDs = Caducidades.objects.all().values_list('idCaducidad', flat=True)
        
        #Obtiene todas las caducidades que hay en Odoo
        caducidadesOdoo=ctrCaducidades.get_newCaducidades()
        
        if caducidadesOdoo['status'] == 'success':
            #Llama a la funcion insert caducidades y le pasa la lista de ID's y las caducidades de Odoo
            response=insertCaducidades(productsPSQL, caducidadesOdoo['caducidades'])
            
            if response['status'] == 'success':     
                message = response['message']
                return JsonResponse({
                    'status'  : 'success',
                    'message' : f'Se registraron {message} nuevas caducidades de {len(caducidadesOdoo['caducidades'])}'
                })
            return JsonResponse({
                    'status'  : 'error',
                    'message' : response['message']
                })
        else:
            return JsonResponse({
                'status'  : 'error',
                'message' : caducidadesOdoo['message']
            })
        
    except Exception as e:
        return JsonResponse({
            'status'  : 'error',
            'message' : f'Ha ocurrido un error al tratar de insertar los datos: {e}'
        })
        
        
# --------------------------------------------------------------------------------------------------
# * Función: updateCaducidadesOdoo
# * Descripción: Actualiza todas las caducidades de Odoo
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
#           La función retorna todas las caducidades que se hayan actualizado en Odoo
# --------------------------------------------------------------------------------------------------
def updateCaducidadesOdoo(request):
    try:
        caducidadesIDs = Caducidades.objects.all().values_list('idCaducidad', flat=True)
        #Obtiene todas las caducidades que hay en Odoo
        caducidadesOdoo=ctrCaducidades.update_Caducidades()
        
        caducidadesObj = {c.idCaducidad: c for c in Caducidades.objects.all()}
        caducidadesUpdate = []
        updatedCaducidades = 0
        
        if caducidadesOdoo['status'] == 'success':
            
            for caducidad in caducidadesOdoo['caducidades']:
                #Busca la caducidad mediante su id
                caducidadObj = caducidadesObj.get(caducidad['id'])
                #Modifica los campos que necesitamos
                caducidadObj.cantidad = caducidad['product_qty']
                
                caducidadesUpdate.append(caducidadObj)
            
            try:
                Caducidades.objects.bulk_update(
                    caducidadesUpdate,
                    ['cantidad'],
                    batch_size=1000
                )
                updatedCaducidades+=len(caducidadesUpdate)
            except:
                try:
                    for caducidad in caducidadesUpdate:
                        caducidad.save()
                        updatedCaducidades+=1
                except Exception as e:
                    print("Error en viewsCaducidades.updateCaducidadesOdoo | Caducidad no se actualizo: ", e, caducidad)
                
            return JsonResponse({
                'status'  : 'success',
                'message' : f'Se modificaron {updatedCaducidades} de {len(caducidadesOdoo['caducidades'])}'
            })
            
        else:
            return JsonResponse({
                'status'  : 'error',
                'message' : caducidadesOdoo['message']
            })
        
    except Exception as e:
        return JsonResponse({
            'status'  : 'error',
            'message' : f'Ha ocurrido un error al tratar de insertar los datos: {e}'
        })