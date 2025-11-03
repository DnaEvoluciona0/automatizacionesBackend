import xmlrpc.client
from datetime import datetime, timedelta

from conexiones.conectionOdoo import OdooAPI

#?Instancia de conexión a Odoo
conOdoo = OdooAPI()

# --------------------------------------------------------------------------------------------------
# * Función: get_allProducts
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

def get_allProducts():
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
            'product.template', 'search_read',
            [[
                '|', ('active', '=', True), ('active', '=', False), 
                ('categ_id', 'not ilike', 'INSUMO'), 
                ('categ_id.parent_id', 'not ilike', 'AGENCIA DIGITAL'), 
                ('default_code', 'not ilike', 'STUDIO'), 
                ('default_code', 'not ilike', 'T-S'), 
                ('default_code', 'not ilike', 'T-T')
            ]],
            {  'fields' : ['id', 'name', 'default_code', 'qty_available', 'product_brand_id', 'categ_id', 'route_ids', 'product_variant_id', 'sale_ok', 'create_date', 'active'] }
        )

        # Retorna todos los productos encontrados
        return ({
            'status'   : 'success',
            'products' : productsOdoo
        })

    except xmlrpc.client.Fault as e:
        return ({
            'status'       : 'error',
            'message'      : f'Error al ejecutar la consulta a Odoo: {str(e)}',
            'fault_code'   : e.faultCode,
            'fault_string' : e.faultString,
        })


# --------------------------------------------------------------------------------------------------
# * Función: get_newProducts
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
def get_newProducts():
    lastDay = (datetime.today() - timedelta(days=1) + timedelta(hours=6)).strftime("%Y-%m-%d 00:00:00")
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
            'product.template', 'search_read',
            [[
                ('create_date', '>=', lastDay),
                '|', ('active', '=', True), ('active', '=', False), 
                ('categ_id', 'not ilike', 'INSUMO'), 
                ('categ_id.parent_id', 'not ilike', 'AGENCIA DIGITAL'), 
                ('default_code', 'not ilike', 'STUDIO'), 
                ('default_code', 'not ilike', 'T-S'), 
                ('default_code', 'not ilike', 'T-T')
            ]],
            {  'fields' : ['id', 'name', 'default_code', 'qty_available', 'product_brand_id', 'categ_id', 'route_ids', 'product_variant_id', 'sale_ok', 'create_date', 'active'] }
        )

        # Retorna todos los productos encontrados
        return ({
            'status'   : 'success',
            'products' : productsOdoo
        })

    except xmlrpc.client.Fault as e:
        return ({
            'status'       : 'error',
            'message'      : f'Error al ejecutar la consulta a Odoo: {str(e)}',
            'fault_code'   : e.faultCode,
            'fault_string' : e.faultString,
        })