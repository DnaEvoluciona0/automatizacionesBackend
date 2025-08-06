import xmlrpc.client
from datetime import datetime, timedelta

from conexiones.conectionOdoo import OdooAPI

#?Instancia de conexión a Odoo
conOdoo = OdooAPI()

# --------------------------------------------------------------------------------------------------
# * Función: get_all_products
# * Descripción: Obtiene todos los productos (que no sean insumos) de Odoo
#
# ! Parámetros:
#   - No recibe ningún parámetro
#
# ? Condiciones para saber que productos obtener
#   1. La categoría del producto no debe de contener:
#       - INSUMO
#       - AGENCIA DIGITAL
#   2. El sku (default_code) no debe de contener:
#       - STUDIO
#       - T-S
#       - T-T
#
# ? Return:
#   - Caso success:
#       Retorna un JSON con el status success y una lista (array) de productos. cada producto contiene los siguientes campos:
#       {  id, name, sku, maxActual, minActual, existenciaActual, marca, categoría, rutas, fechaCreacion  }
#   - Caso error: 
#       En caso de haber ocurrido algun error retorna un JSON con status error y el mensaje del error
# --------------------------------------------------------------------------------------------------

def get_all_products():
    #!Determinamos si existe conexión con odoo
    if not conOdoo.models:
        return ({
            'status'  : 'error',
            'message' : 'Error en la conexión con Odoo, no hay conexión Activa'
        })

    #Función try para traer productos a partir de la categoria dada
    try:
        # Obtener todos los productos que cumplan con las condiciones 
        productsOdoo = conOdoo.models.execute_kw(
            conOdoo.db, conOdoo.uid, conOdoo.password,
            'product.product', 'search_read',
            [[  '&',
                #('purchase_ok', '=', 'TRUE'),
                ('categ_id', 'not ilike', 'INSUMO'),
                ('categ_id.parent_id', 'not ilike', 'AGENCIA DIGITAL'),
                ('default_code', 'not ilike', 'STUDIO'),
                ('default_code', 'not ilike', 'T-S'),
                ('default_code', 'not ilike', 'T-T'),
            ]],
            {  'fields' : ['id', 'name', 'default_code', 'qty_available', 'product_brand_id', 'categ_id', 'route_ids', 'product_tmpl_id'] }
        )

        # Obtener reglas de maximos y minimos
        orderpoints = conOdoo.models.execute_kw(
            conOdoo.db, conOdoo.uid, conOdoo.password,
            'stock.warehouse.orderpoint', 'search_read',
            [[]],
            {  'fields' : ['product_id', 'product_min_qty', 'product_max_qty']  }
        )

        # Obtener fechas de creación
        productCreatedDate = conOdoo.models.execute_kw(
            conOdoo.db, conOdoo.uid, conOdoo.password,
            'product.template', 'search_read',
            [[]],
            {  'fields' : ['id', 'create_date']  }
        )

        finalProducts = []

        # Por cada producto encontrado que cumpla las reglas, relaciona los valores con las 
        # reglas de maximos y minimos (orderpoints) y las fechas de creación (productCreatedDate)
        for product in productsOdoo:
            productId    = product['id']
            idtemplate   = product['product_tmpl_id'][0]
            points       = [op for op in orderpoints if op['product_id'][0] == productId]
            createdDates = [pcd for pcd in productCreatedDate if pcd['id'] == idtemplate]

            minQty      = points[0]['product_min_qty']   if points else 0
            maxQty      = points[0]['product_max_qty']   if points else 0
            createdDate = createdDates[0]['create_date'] if createdDates else ''
            
            finalProducts.append({
                'id'               : productId,
                'name'             : product['name'],
                'sku'              : product['default_code'],
                'existenciaActual' : product['qty_available'],
                'minActual'        : minQty, 
                'maxActual'        : maxQty,
                'marca'            : product['product_brand_id'],
                'categoria'        : product['categ_id'],
                'routes'           : product['route_ids'],
                'fechaCreacion'    : createdDate
            }) 

        # Retorna todos los productos encontrados
        return ({
            'status'   : 'success',
            'products' : finalProducts
        })

    except xmlrpc.client.Fault as e:
        return ({
            'status'       : 'error',
            'message'      : f'Error al ejecutar la consulta a Odoo: {str(e)}',
            'fault_code'   : e.faultCode,
            'fault_string' : e.faultString,
        })


# --------------------------------------------------------------------------------------------------
# * Función: get_newproducts
# * Descripción: Obtiene los productos nuevos (que no sean insumos) de Odoo
#
# ! Parámetros:
#   - No recibe ningún parámetro
#
# ? Condiciones para saber que productos obtener
#   1. La categoría del producto no debe de contener:
#       - INSUMO
#       - AGENCIA DIGITAL
#   2. El sku (default_code) no debe de contener:
#       - STUDIO
#       - T-S
#       - T-T
#   3. La fecha de creación de los productos debe de ser mayor a la fecha del día actual menos un día
#
# ? Return:
#   - Caso success:
#       Retorna un JSON con el status success y una lista (array) de productos. cada producto contiene los siguientes campos:
#       {  id, name, sku, maxActual, minActual, existenciaActual, marca, categoría, rutas, fechaCreacion  }
#   - Caso error: 
#       En caso de haber ocurrido algun error retorna un JSON con status error y el mensaje del error
# --------------------------------------------------------------------------------------------------
def get_newproducts():
    #!Determinamos si existe conexión con odoo
    if not conOdoo.models:
        return ({
            'status'  : 'error',
            'message' : 'Error en la conexión con Odoo, no hay conexión Activa'
        })

    #Función try para traer productos a partir de la categoria dada
    try: 
        today     = datetime.now()
        yesterday = today - timedelta(days=1)
        dateStart = yesterday.strftime('%Y-%m-%d 00:00:00')
        dateEnd   = today.strftime('%Y-%m-%d 00:00:01')

        # Obtiene todos los ids de los productos creados el día anterior
        productTemplateID = conOdoo.models.execute_kw(
            conOdoo.db, conOdoo.uid, conOdoo.password,
            'product.template', 'search',
            [[
                ('create_date', '>=', dateStart),
                ('create_date', '<=', dateEnd)
            ]],
        )

        # Obtener todos los productos que cumplan con las condiciones
        productsOdoo = conOdoo.models.execute_kw(
            conOdoo.db, conOdoo.uid, conOdoo.password,
            'product.product', 'search_read',
            [[  '&',
                ('categ_id', 'not ilike', 'INSUMO'),
                ('product_tmpl_id', 'in', productTemplateID),
                ('categ_id.parent_id', 'not ilike', 'AGENCIA DIGITAL'),
                ('default_code', 'not ilike', 'STUDIO'),
                ('default_code', 'not ilike', 'T-S'),
                ('default_code', 'not ilike', 'T-T'),
            ]],
            {  'fields' : ['id', 'name', 'default_code', 'qty_available', 'product_brand_id', 'categ_id', 'route_ids', 'product_tmpl_id'] }
        )

        # Obtener reglas de maximos y minimos
        orderpoints = conOdoo.models.execute_kw(
            conOdoo.db, conOdoo.uid, conOdoo.password,
            'stock.warehouse.orderpoint', 'search_read',
            [[]],
            {  'fields' : ['product_id', 'product_min_qty', 'product_max_qty']  }
        )

        # Obtener fechas de creación
        productCreatedDate = conOdoo.models.execute_kw(
            conOdoo.db, conOdoo.uid, conOdoo.password,
            'product.template', 'search_read',
            [[]],
            {  'fields' : ['id', 'create_date']  }
        )

        finalProducts = []

        # Por cada producto encontrado que cumpla las reglas, relaciona los valores con las 
        # reglas de maximos y minimos (orderpoints) y las fechas de creación (productCreatedDate)
        for product in productsOdoo:
            productId    = product['id']
            idtemplate   = product['product_tmpl_id'][0]
            points       = [op for op in orderpoints if op['product_id'][0] == productId]
            createdDates = [pcd for pcd in productCreatedDate if pcd['id'] == idtemplate]

            minQty = points[0]['product_min_qty'] if points else 0
            maxQty = points[0]['product_max_qty'] if points else 0
            createdDate = createdDates[0]['create_date'] if createdDates else ''
            
            finalProducts.append({
                'id'               : productId,
                'name'             : product['name'],
                'sku'              : product['default_code'],
                'existenciaActual' : product['qty_available'],
                'minActual'        : minQty, 
                'maxActual'        : maxQty,
                'marca'            : product['product_brand_id'],
                'categoria'        : product['categ_id'],
                'routes'           : product['route_ids'], 
                'fechaCreacion'    : createdDate
            }) 

            # Retorna todos los productos encontrados
        return ({
            'status'   : 'success',
            'products' : finalProducts
        })

    except xmlrpc.client.Fault as e:
        return ({
            'status'       : 'error',
            'message'      : f'Error al ejecutar la consulta a Odoo: {str(e)}',
            'fault_code'   : e.faultCode,
            'fault_string' : e.faultString,
        })