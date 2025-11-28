from django.http import JsonResponse

from django.db.models import Count, Sum, F
from django.db.models.functions import TruncMonth
from dateutil.relativedelta import relativedelta
import math
from datetime import datetime

from unidades.produccionLogistica.maxMin.models import Productos, MaterialPI
from unidades.administracion.reporteVentas.models import Ventas, VentasPVH
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
    insumosCreate = []
    newInsumos = 0
    
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
            
            insumosCreate.append(
                Productos(
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
            )
            
    try:
        Productos.objects.bulk_create(insumosCreate, batch_size=1000)
        newInsumos+=len(insumosCreate)
    except:
        try:
            for insumo in insumosCreate:
                insumo.save()
                newInsumos+=1   
        except Exception as e:
            print("Error en viewsInsumo.insertInsumo | Insumo no se inserto: ", e, insumo)
    
    return ({
        'status'  : 'success',
        'message' : newInsumos
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
        insumosIDs = Productos.objects.all().values_list('idProductoTmp', flat=True)
        #traemos los productos nuevos de odoo
        insumosOdoo = ctrInsumo.get_newInsumos(list(insumosIDs))
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
        insumosIDs = Productos.objects.all().values_list('idProductoTmp', flat=True)
        # Traemos los insumos de odoo
        insumosOdoo = ctrInsumo.get_updateInsumos(list(insumosIDs))
        
        insumosObj = {i.idProductoTmp: i for i in Productos.objects.all()}
        insumosUpdate = []
        updatedInsumos = 0
        
        if insumosOdoo['status'] == 'success':
            
            for insumo in insumosOdoo['products']:
                #Busca el ID del insumo en Postgres
                insumoObj = insumosObj.get(insumo['id'])
                
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

                insumosUpdate.append(insumoObj)
                    
            try:
                Productos.objects.bulk_update(
                    insumosUpdate,
                    ['nombre', 'sku', 'marca', 'maxActual', 'minActual', 'existenciaActual', 'existenciaOC', 'categoria', 'tipo', 'proveedor', 'tiempoEntrega'],
                    batch_size=1000
                )
                updatedInsumos+=len(insumosUpdate)
            except:
                try:
                    for insumo in insumosUpdate:
                        insumo.save()
                        updatedInsumos+=1
                except Exception as e:
                    print("Error en viewsInsumo.updateInsumo | Insumo no se actualizo: ", e, insumo)
            
            return JsonResponse({
                'status'  : 'success',
                'message' : f'Se han actualizado correctamente {updatedInsumos} insumos de {len(insumosOdoo["products"])}'
            })
        return JsonResponse({
            'status'  : 'error',
            'message' : f'Error en realizar la consulta a Odoo: {insumosOdoo["message"]}'
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
def updateMaxMinOdoo(request):
    try:
        thisYear=datetime(datetime.now().year, 1, 1)
        lastYear = datetime(datetime.now().year - 1, 1, 1)
        
        insumosCompartidos = {i['hijo_id']: i for i in MaterialPI.objects.values('hijo_id').annotate(total=Count('hijo_id'), sumaCantidad=Sum(F('cantidad') * F('padre__existenciaActual'))).filter(total__gt=1)}
        
        ventasTotalesLastYear = {p['producto__idProductoTmp']: p for p in VentasPVH.objects.values('producto__idProductoTmp').annotate(cantidad=Sum('cantidad'), mesesVendidos=Count(TruncMonth('venta__fecha'), distinct=True)).exclude(venta__idVenta__startswith='R').filter(venta__fecha__gte=lastYear, venta__fecha__lt=thisYear)}
        ventasTotalesThisYear = {p['producto__idProductoTmp']: p for p in VentasPVH.objects.values('producto__idProductoTmp').annotate(cantidad=Sum('cantidad'), mesesVendidos=Count(TruncMonth('venta__fecha'), distinct=True)).exclude(venta__idVenta__startswith='R').filter(venta__fecha__gte=thisYear)}
        
        materialesHijos = {}
        promVCompartidas={}
        
        for material in MaterialPI.objects.values('padre_id', 'padre__nombre', 'padre__sku', 'padre__existenciaActual', 'padre__marca', 'padre__tipo', 'hijo_id', 'hijo__nombre', 'cantidad', 'hijo__sku', 'hijo__existenciaActual', 'hijo__existenciaOC', 'hijo__marca').order_by('padre__nombre'):
            piezasArmar = round((material["hijo__existenciaActual"] / (material["cantidad"] if material["cantidad"] > 0 else 1)), 2)
            pt = round(insumosCompartidos.get(material["hijo_id"], {}).get("sumaCantidad", 0) or material["padre__existenciaActual"] * material["cantidad"], 2)
            promVData = ventasTotalesLastYear.get(material["padre_id"], {}) or ventasTotalesThisYear.get(material["padre_id"], {})
            promV = round(promVData.get('cantidad', 0)/promVData.get('mesesVendidos', 1), 2)
            
            if insumosCompartidos.get(material["hijo_id"]):
                promVCompartidas[material["hijo_id"]] = promVCompartidas.get(material["hijo_id"], 0)+promV

            
            materialHijo = {
                'id': material["hijo_id"],
                'nombre': material["hijo__nombre"],
                'cantidad': material["cantidad"],
                'sku': material["hijo__sku"],
                'existenciaActual': material["hijo__existenciaActual"],
                'piezasArmar': piezasArmar,
                'existenciasPT': pt,
                'existenciaOC': material["hijo__existenciaOC"],
                'totalPiezas': material["hijo__existenciaActual"] + pt + material["hijo__existenciaOC"],
                'promedioVentas': promV,
                'min': 0,
                'max': 0,
                'sugerido': 0,
                'total': 0,
                'mesesInventario':0,
                'marca': material["hijo__marca"]
            }
            
            if materialesHijos.get(material["padre_id"]):
                materialesHijos[material["padre_id"]]["materiales"].append(materialHijo)                
                materialesHijos[material["padre_id"]]["piezasArmar"] = min(materialesHijos[material["padre_id"]]["piezasArmar"], piezasArmar)
    
            else:
                materialesHijos[material["padre_id"]]={
                    'id': material["padre_id"],
                    'nombre': material["padre__nombre"],
                    'sku': material["padre__sku"],
                    'existenciaActual': material["padre__existenciaActual"],
                    'piezasArmar': piezasArmar,
                    'existenciasPT': material["padre__existenciaActual"],
                    'totalPiezas': material["padre__existenciaActual"],
                    'promedioVentas': promV,
                    'mesesInventario': 0,
                    'marca': material["padre__marca"],
                    'tipo': material['padre__tipo'],
                    'materiales': [materialHijo]
                }
                
        for padre in materialesHijos.values():
            padre["existenciasPT"] = padre["piezasArmar"] + padre["existenciaActual"]
            padre["totalPiezas"] = padre["existenciaActual"] + padre["existenciasPT"]
            padre["mesesInventario"] = round(padre["totalPiezas"]/padre['promedioVentas'] if padre['promedioVentas'] > 0 else 0, 2)
            for hijo in padre["materiales"]:
                if promVCompartidas.get(hijo["id"]):
                    hijo["promedioVentas"] = round(hijo["cantidad"]*promVCompartidas[hijo["id"]], 2)
                hijo["min"] = math.ceil(hijo["promedioVentas"]*3)
                hijo["max"] = math.ceil(hijo["promedioVentas"]*6)
                hijo["sugerido"] = math.ceil(hijo["max"]-hijo["totalPiezas"] if hijo["totalPiezas"] < hijo["max"] else 0)
                hijo["total"]= hijo["sugerido"] + hijo["totalPiezas"]
                hijo["mesesInventario"] = round(hijo["total"]/hijo['promedioVentas'] if hijo['promedioVentas'] != 0 else 0, 2)

        response = ctrInsumo.update_maxMin()
        if response['status'] == 'success':
        
            return JsonResponse({
                'status'  : 'success',
                'message' : materialesHijos
            })
        return JsonResponse({
            'status'  : 'error',
            'message' : f'{response["message"]}'
        })

    except Exception as e:
        return ({
            'status'  : 'error',
            'message' : f'Ha ocurrido un error al tratar de insertar los datos {str(e)}'
        })