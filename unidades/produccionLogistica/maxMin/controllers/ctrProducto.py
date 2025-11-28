import xmlrpc.client
from conexiones.conectionOdoo import OdooAPI
import pandas as pd

#?Instancia de conexión a Odoo
conOdoo = OdooAPI()

#?Obtiene un archivo mendiante la url y lo abre en la pestaña necesaria para su posterior lectura
archivo = 'static/ContpaqBD.xlsx'
dfProducto = pd.read_excel(archivo, sheet_name='Productos')

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
        
        productNoID=[]
        productos={}
        
        for product in productsOdoo:
            productos[product['id']]=product
            if product['active'] == False:
                productNoID.append(product['id'])
        
        variantIDs = conOdoo.models.execute_kw(
            conOdoo.db, conOdoo.uid, conOdoo.password,
            'product.product', 'search_read',
            [[
                ('active', '=', False), 
                ('product_tmpl_id', 'in', productNoID)
            ]],
            { 'fields': ['id', 'product_tmpl_id']}
        )
        
        variants={}
        for variant in variantIDs:
            variants[variant['product_tmpl_id'][0]]=variant['id']
        
        for product in productsOdoo:
            if not product.get('product_variant_id') and variants[product['id']]:
                product['product_variant_id'] = [variants[product['id']], '']
            

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
def get_newProducts(productosIDs):
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
                ('id', 'not in', productosIDs),
                '|', ('active', '=', True), ('active', '=', False), 
                ('categ_id', 'not ilike', 'INSUMO'), 
                ('categ_id.parent_id', 'not ilike', 'AGENCIA DIGITAL'), 
                ('default_code', 'not ilike', 'STUDIO'), 
                ('default_code', 'not ilike', 'T-S'), 
                ('default_code', 'not ilike', 'T-T')
            ]],
            {  'fields' : ['id', 'name', 'default_code', 'qty_available', 'product_brand_id', 'categ_id', 'route_ids', 'product_variant_id', 'sale_ok', 'create_date', 'active'] }
        )
        
        productNoID=[]
        productos={}
        
        for product in productsOdoo:
            productos[product['id']]=product
            if product['active'] == False:
                productNoID.append(product['id'])
        
        variantIDs = conOdoo.models.execute_kw(
            conOdoo.db, conOdoo.uid, conOdoo.password,
            'product.product', 'search_read',
            [[
                ('active', '=', False), 
                ('product_tmpl_id', 'in', productNoID)
            ]],
            { 'fields': ['id', 'product_tmpl_id']}
        )
        
        variants={}
        for variant in variantIDs:
            variants[variant['product_tmpl_id'][0]]=variant['id']
        
        for product in productsOdoo:
            if not product.get('product_variant_id') and variants[product['id']]:
                product['product_variant_id'] = [variants[product['id']], '']

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
# * Función: get_updateProducts
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
def get_updateProducts(productosIDs):
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
                ('id', 'in', productosIDs),
                '|', ('active', '=', True), ('active', '=', False), 
                ('categ_id', 'not ilike', 'INSUMO'), 
                ('categ_id.parent_id', 'not ilike', 'AGENCIA DIGITAL'), 
                ('default_code', 'not ilike', 'STUDIO'), 
                ('default_code', 'not ilike', 'T-S'), 
                ('default_code', 'not ilike', 'T-T')
            ]],
            {  'fields' : ['id', 'name', 'default_code', 'qty_available', 'product_brand_id', 'categ_id', 'route_ids', 'product_variant_id', 'sale_ok', 'create_date', 'active'] }
        )

        productNoID=[]
        productos={}
        
        for product in productsOdoo:
            productos[product['id']]=product
            if product['active'] == False:
                productNoID.append(product['id'])
        
        variantIDs = conOdoo.models.execute_kw(
            conOdoo.db, conOdoo.uid, conOdoo.password,
            'product.product', 'search_read',
            [[
                ('active', '=', False), 
                ('product_tmpl_id', 'in', productNoID)
            ]],
            { 'fields': ['id', 'product_tmpl_id']}
        )
        
        variants={}
        for variant in variantIDs:
            variants[variant['product_tmpl_id'][0]]=variant['id']
        
        for product in productsOdoo:
            if not product.get('product_variant_id') and variants[product['id']]:
                product['product_variant_id'] = [variants[product['id']], '']


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
        
def get_allProductsExcel(productosIDs):
    #!Determinamos que haya algna conexión con Odoo
    if not conOdoo.models:
        return ({
            'status'  : 'error',
            'message' : 'Error en la conexión con Odoo, no hay conexión Activa'
        })
    
    #función try para obtener las facturas
    try:
        #Obtenemos los ids de clientes unicos
        productosTmp = dfProducto['id_odooTmp'].unique().tolist()
        
        productsOdoo = conOdoo.models.execute_kw(
            conOdoo.db, conOdoo.uid, conOdoo.password,
            'product.template', 'search_read',
            [[
                ('id', 'in', productosTmp),
                '|', ('active', '=', True), ('active', '=', False), 
                ('categ_id', 'not ilike', 'INSUMO'), 
                ('categ_id.parent_id', 'not ilike', 'AGENCIA DIGITAL'), 
                ('default_code', 'not ilike', 'STUDIO'), 
                ('default_code', 'not ilike', 'T-S'), 
                ('default_code', 'not ilike', 'T-T')
            ]],
            {  'fields' : ['id', 'name', 'default_code', 'qty_available', 'product_brand_id', 'categ_id', 'route_ids', 'product_variant_id', 'sale_ok', 'create_date', 'active'] }
        )
        
        productNoID=[]
        productos={}
        
        for product in productsOdoo:
            productos[product['id']]=product
            if product['active'] == False:
                productNoID.append(product['id'])
        
        variantIDs = conOdoo.models.execute_kw(
            conOdoo.db, conOdoo.uid, conOdoo.password,
            'product.product', 'search_read',
            [[
                ('active', '=', False), 
                ('product_tmpl_id', 'in', productNoID)
            ]],
            { 'fields': ['id', 'product_tmpl_id']}
        )
        
        variants={}
        for variant in variantIDs:
            variants[variant['product_tmpl_id'][0]]=variant['id']
        
        for product in productsOdoo:
            if not product.get('product_variant_id') and variants[product['id']]:
                product['product_variant_id'] = [variants[product['id']], '']
        
        
        productos={}
        
        skusEncontrados = [prod['default_code'] for prod in productsOdoo if prod.get('default_code')]
        
        for index, producto in dfProducto.iterrows():
            if producto['sku'] not in skusEncontrados:
                productsOdoo.append(
                    {
                        'id': producto['id_odooTmp'],
                        'product_variant_id': [producto['id_odoo'], ''],
                        'name': producto['nombre'],
                        'default_code': producto['sku'],
                        'qty_available': 0,
                        'product_brand_id': [0, producto['marca']],
                        'categ_id': [0, producto['categoria']],
                        'route_ids': [],
                        'sale_ok': False,
                        'create_date': '2023-01-01 00:00:00.000 -0600',
                        'active': False
                    }
                )
        
        #Retorna todos los productos
        return ({
            'status'  : 'success',
            'products' : productsOdoo
        })
        
    except xmlrpc.client.Fault as e:
        return ({
            'status'       : 'error',
            'message'      : f'Error al ejecutar la consulta a Odoo: {str(e)}',
            'fault_code'   : e.faultCode,
            'fault_string' : e.faultString,
        })