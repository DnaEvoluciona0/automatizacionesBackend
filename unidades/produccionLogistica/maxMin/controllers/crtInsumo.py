import xmlrpc.client
from datetime import datetime, timedelta

from conexiones.conectionOdoo import OdooAPI

#? Instania de coneción a Odoo
conOdoo = OdooAPI()

# --------------------------------------------------------------------------------------------------
# * Función: get_all_insumos
# * Descripción: Obtiene todos los productos (que únicamente sean insumos) de Odoo
#
# ! Parámetros:
#   - No recibe ningún parámetro
#
# ? Condiciones para saber que productos obtener
#   1. La categoría del producto no debe de contener:
#       - AGENCIA DIGITAL
#   2. La categoría del producto debe de contener:
#       - INSUMO
#   3. El sku (default_code) no debe de contener:
#       - STUDIO
#       - T-S
#       - T-T
#
# ? Return:
#   - Caso success:
#       Retorna un JSON con el status success y una lista (array) de productos. cada producto contiene los siguientes campos:
#       {  id, name, sku, maxActual, minActual, existenciaActual, marca, categoría, rutas, proveedores  }
#   - Caso error: 
#       En caso de haber ocurrido algun error retorna un JSON con status error y el mensaje del error
# --------------------------------------------------------------------------------------------------
def get_all_insumos():
    if not conOdoo.models:
        return ({
            'status'  : 'error',
            'message' : 'Error en la conexión con Odoo, no hay conexión Activa'
        })

    #funcion try para arrojar los insumos de odoo
    try:
        # Obtener todos los productos que cumplan con las condiciones 
        insumosOdoo = conOdoo.models.execute_kw(
            conOdoo.db, conOdoo.uid, conOdoo.password,
            'product.product', 'search_read', 
            [[
                '&',
                ('categ_id', 'ilike', 'INSUMO'),
                ('categ_id.parent_id', 'not ilike', 'AGENCIA DIGITAL'),
                ('default_code', 'not ilike', 'STUDIO'),
                ('default_code', 'not ilike', 'T-S'),
                ('default_code', 'not ilike', 'T-T'),
            ]],
            {  'fields' : ['id', 'name', 'default_code', 'qty_available', 'product_brand_id', 'categ_id', 'route_ids']  }
        )

        # Obtener reglas de maximos y minimos
        orderpoints = conOdoo.models.execute_kw(
            conOdoo.db, conOdoo.uid, conOdoo.password, 
            'stock.warehouse.orderpoint', 'search_read', 
            [[]],
            {  'fields' : ['product_id', 'product_min_qty', 'product_max_qty']  }
        )

        # Obtener reglas de proveedores
        providers = conOdoo.models.execute_kw(
            conOdoo.db, conOdoo.uid, conOdoo.password,
            'product.supplierinfo', 'search_read', 
            [[]],
            {  'fields' : ['product_tmpl_id', 'partner_id', 'delay'] }
        )

        finalInsumos = []

        # Por cada producto encontrado que cumpla las reglas, relaciona los valores con las 
        # reglas de maximos y minimos (orderpoints) y los proveedores (poviders)
        for insumo in insumosOdoo:
            insumoId   = insumo['id']
            insumoName = insumo['name']
            points     = [op for op in orderpoints if op['product_id'][0] == insumoId]
            provider   = [pr for pr in providers   if insumoName in pr['product_tmpl_id'][1]]

            minQty = points[0]['product_min_qty'] if points else 0
            maxQty = points[0]['product_max_qty'] if points else 0

            finalInsumos.append({
                'id'               : insumoId,
                'name'             : insumo['name'],
                'sku'              : insumo['default_code'],
                'existenciaActual' : insumo['qty_available'],
                'minActual'        : minQty,
                'maxActual'        : maxQty,
                'marca'            : insumo['product_brand_id'],
                'categoria'        : insumo['categ_id'],
                'routes'           : insumo['route_ids'],
                'proveedor'        : provider
            })

        return ({
            'status'   : 'success',
            'products' : finalInsumos
        })

    except xmlrpc.client.Fault as e:
        return ({
            'status'       : 'error',
            'message'      : f'Error al ejecutar la consulta a Odoo: {str(e)}',
            'fault_code'   : e.faultCode,
            'fault_string' : e.faultString,
        })


# --------------------------------------------------------------------------------------------------
# * Función: get_newInsumos
# * Descripción: Obtiene los productos nuevos (que únicamente sean insumos) de Odoo
#
# ! Parámetros:
#   - No recibe ningún parámetro
#
# ? Condiciones para saber que productos obtener
#   1. La categoría del producto no debe de contener:
#       - AGENCIA DIGITAL
#   2. La categoría del producto debe de contener:
#       - INSUMO
#   3. El sku (default_code) no debe de contener:
#       - STUDIO
#       - T-S
#       - T-T
#   4. La fecha de creación de los productos debe de ser mayor a la fecha del día actual menos un día
#
# ? Return:
#   - Caso success:
#       Retorna un JSON con el status success y una lista (array) de productos. cada producto contiene los siguientes campos:
#       {  id, name, sku, maxActual, minActual, existenciaActual, marca, categoría, rutas, proveedores  }
#   - Caso error: 
#       En caso de haber ocurrido algun error retorna un JSON con status error y el mensaje del error
# --------------------------------------------------------------------------------------------------
def get_newInsumos():
    #Verificamos que haya alguna conexion con odoo
    if not conOdoo.models:
        return({
            'status'  : 'error',
            'message' : 'Error en la conexión con Odoo, no hay conexión Activa'
        })

    try:
        today     = datetime.now()
        yesterday = today - timedelta(days=1)
        dateStart = yesterday.strftime('%Y-%m-%d 00:00:00')
        dateEnd   = today.strftime('%Y-%m-%d 23:59:59')

        # Obtiene todos los ids de los productos creados el día anterior
        insumoTemplateID = conOdoo.models.execute_kw(
            conOdoo.db, conOdoo.uid, conOdoo.password,
            'product.template', 'search',
            [[
                ('create_date', '>=', dateStart),
                ('create_date', '<=', dateEnd)
            ]],

        )
        
        # Obtener todos los productos que cumplan con las condiciones
        insumosOdoo = conOdoo.models.execute_kw(
            conOdoo.db, conOdoo.uid, conOdoo.password,
            'product.product', 'search_read', 
            [[
                '&',
                ('categ_id', 'ilike', 'INSUMO'),
                ('product_tmpl_id', 'in', insumoTemplateID),
                ('categ_id.parent_id', 'not ilike', 'AGENCIA DIGITAL'),
                ('default_code', 'not ilike', 'STUDIO'),
                ('default_code', 'not ilike', 'T-S'),
                ('default_code', 'not ilike', 'T-T'),
            ]],
            {  'fields' : ['id', 'name', 'default_code', 'qty_available', 'product_brand_id', 'categ_id', 'route_ids']  }
        )

        # Obtener reglas de maximos y minimos
        orderpoints = conOdoo.models.execute_kw(
            conOdoo.db, conOdoo.uid, conOdoo.password, 
            'stock.warehouse.orderpoint', 'search_read', 
            [[]],
            {  'fields' : ['product_id', 'product_min_qty', 'product_max_qty']  }
        )

        # Obtener reglas de proveedores
        providers = conOdoo.models.execute_kw(
            conOdoo.db, conOdoo.uid, conOdoo.password,
            'product.supplierinfo', 'search_read', 
            [[]],
            {  'fields' : ['product_tmpl_id', 'partner_id', 'delay'] }
        )

        finalInsumos = []

        # Por cada producto encontrado que cumpla las reglas, relaciona los valores con las 
        # reglas de maximos y minimos (orderpoints) y los proveedores (poviders)
        for insumo in insumosOdoo:
            insumoId   = insumo['id']
            insumoName = insumo['name']
            points     = [op for op in orderpoints if op['product_id'][0] == insumoId]
            provider   = [pr for pr in providers   if insumoName in pr['product_tmpl_id'][1]]

            minQty = points[0]['product_min_qty'] if points else 0
            maxQty = points[0]['product_max_qty'] if points else 0

            finalInsumos.append({
                'id'               : insumoId,
                'name'             : insumo['name'],
                'sku'              : insumo['default_code'],
                'existenciaActual' : insumo['qty_available'],
                'minActual'        : minQty,
                'maxActual'        : maxQty,
                'marca'            : insumo['product_brand_id'],
                'categoria'        : insumo['categ_id'],
                'routes'           : insumo['route_ids'],
                'proveedor'        : provider
            })
        return ({
            'status'   : 'success',
            'products' : finalInsumos
        })
    except xmlrpc.client.Fault as e:
        return ({
            'status'       : 'error',
            'message'      : f'Error al ejecutar la consulta a Odoo: {str(e)}',
            'fault_code'   : e.faultCode,
            'fault_string' : e.faultString,
        })


# --------------------------------------------------------------------------------------------------
# * Función: updateMaxMinOdoo
# * Descripción: Actualiza las reglas de máximos y mínimos del insumo en cuestión
#
# ! Parámetros (deben de ser obligatorios):
#   - idInsimo, es el id del insumo que se va a actualizar.
#   - max, cantidad maxima nueva del producto
#   - min, cantidad minima nueva
#
# ? Return:
#   - Caso success:
#       Retorna un JSON con el status success y un mensaje de satisfacción
#   - Caso error: 
#       En caso de que no exista una regla de max y min asociada al id del producto
#       En caso de una excepción
# --------------------------------------------------------------------------------------------------
def updateMaxMinOdoo(idInsumo, max, min):
    try:
        #Obtiene la regla de maximo y minimo asociada al id del producto
        orderPoint = conOdoo.models.execute_kw(
            conOdoo.db, conOdoo.uid, conOdoo.password,
            'stock.warehouse.orderpoint', 'search_read',
            [[  ('product_id', '=', idInsumo)  ]],
            {  'fields' : ['id']  }
        )
        
        # Si existe la regla
        if orderPoint:
            idOrderPoint = orderPoint[0]['id']

            # Actualiza máximo y minimo 
            conOdoo.models.execute_kw(
                conOdoo.db, conOdoo.uid, conOdoo.password,
                'stock.warehouse.orderpoint', 'write', 
                [[  idOrderPoint  ], 
                {
                    'product_min_qty' : int(round(min)),
                    'product_max_qty' : int(round(max))
                }]
            )

            return({
                'status'  : 'success',
                'message' : 'Se ha modificado correctamente el producto'
            })

        return({
            'status'  : 'error',
            'message' : f'No existe Máximo ni Mínimo de este producto {idInsumo}'
        })
    except xmlrpc.client.Fault as e:
        return ({
            'status'       : 'error',
            'message'      : f'Error al ejecutar la consulta a Odoo: {str(e)}',
            'fault_code'   : e.faultCode,
            'fault_string' : e.faultString,
        })