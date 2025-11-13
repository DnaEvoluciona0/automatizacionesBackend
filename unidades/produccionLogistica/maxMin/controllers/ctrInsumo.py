import xmlrpc.client
from datetime import datetime, timedelta

from conexiones.conectionOdoo import OdooAPI

#? Instania de coneción a Odoo
conOdoo = OdooAPI()

# --------------------------------------------------------------------------------------------------
# * Función: get_allInsumos
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
def get_allInsumos():
    #!Determinamos si existe conexión con odoo
    if not conOdoo.models:
        return ({
            'status'  : 'error',
            'message' : 'Error en la conexión con Odoo, no hay conexión Activa'
        })

    #funcion try para arrojar los insumos de odoo
    try:
        # Obtener todos los insumos que cumplan con las condiciones 
        insumosOdoo = conOdoo.models.execute_kw(
            conOdoo.db, conOdoo.uid, conOdoo.password,
            'product.template', 'search_read', 
            [[
                '|', ('active', '=', True), ('active', '=', False), 
                ('categ_id', 'ilike', 'INSUMO'), 
                ('categ_id.parent_id', 'not ilike', 'AGENCIA DIGITAL'), 
                ('default_code', 'not ilike', 'STUDIO'), 
                ('default_code', 'not ilike', 'T-S'), 
                ('default_code', 'not ilike', 'T-T')
            ]],
            {  'fields' : ['id', 'name', 'default_code', 'qty_available', 'product_brand_id', 'categ_id', 'route_ids', 'product_variant_id', 'purchase_ok', 'create_date', 'active'] }
        )
        
        insumosNoID = [insumo['id'] for insumo in insumosOdoo if not insumo['active']]             
        
        variants = {}
        if insumosNoID:
            variantIDs = conOdoo.models.execute_kw(
                conOdoo.db, conOdoo.uid, conOdoo.password,
                'product.product', 'search_read',
                [[
                    ('active', '=', False), 
                    ('product_tmpl_id', 'in', insumosNoID)
                ]],
                {'fields': ['id', 'product_tmpl_id']}
            )
            variants = {v['product_tmpl_id'][0]: v['id'] for v in variantIDs}
            
            # Asignar variants faltantes
            for insumo in insumosOdoo:
                if not insumo.get('product_variant_id') and insumo['id'] in variants:
                    insumo['product_variant_id'] = [variants[insumo['id']], '']
                
        idsT = [insumo['id'] for insumo in insumosOdoo]
            
        # Obtener reglas de maximos y minimos
        orderpointsOdoo = conOdoo.models.execute_kw(
            conOdoo.db, conOdoo.uid, conOdoo.password, 
            'stock.warehouse.orderpoint', 'search_read', 
            [[('product_tmpl_id', 'in', idsT)]],
            {  'fields' : ['product_tmpl_id', 'product_min_qty', 'product_max_qty']  }
        )
        orderpoints = {op['product_tmpl_id'][0]: op for op in orderpointsOdoo}
            
        # Obtener reglas de proveedores
        providersOdoo = conOdoo.models.execute_kw(
            conOdoo.db, conOdoo.uid, conOdoo.password,
            'product.supplierinfo', 'search_read', 
            [[('product_tmpl_id', 'in', idsT)]],
            {  'fields' : ['product_tmpl_id', 'partner_id', 'delay'] }
        )
        providers = {prov['product_tmpl_id'][0]: prov for prov in providersOdoo}
        
        existenciasOCOdoo = conOdoo.models.execute_kw(
            conOdoo.db, conOdoo.uid, conOdoo.password,
            'purchase.order.line', 'search_read',
            [[
                ('display_type', 'not in', ['line_note', 'line_section']),
                ('state', '!=', 'done'),
                ('order_id.state', 'not in', ['draft', 'sent']),
                ('order_id.receipt_status', '!=', 'full'),
                ('order_id.user_id', '=', 46)
            ]],
            {  'fields' : ['product_id', 'product_qty', 'qty_received', 'display_type']}
        )
        existenciasOC = {}
        
        for oc in existenciasOCOdoo:
            number = oc['product_qty'] - oc['qty_received']
            if oc['product_id'][0] not in existenciasOC and number > 0:
                existenciasOC[oc['product_id'][0]] = number
                
            elif oc['product_id'][0] in existenciasOC:
                existenciasOC[oc['product_id'][0]] += number
        
        # Por cada producto encontrado que cumpla las reglas, relaciona los valores con las 
        # reglas de maximos y minimos (orderpoints) y los proveedores (poviders)
        for insumo in insumosOdoo:
            insumo_id = insumo['id']
            variant_id = insumo['product_variant_id'][0] if insumo.get('product_variant_id') else 0
            
            orderpoint = orderpoints.get(insumo_id, {})
            insumo['product_min_qty'] = orderpoint.get('product_min_qty', 0)
            insumo['product_max_qty'] = orderpoint.get('product_max_qty', 0)

            provider = providers.get(insumo_id, {})
            insumo['provider'] = provider.get('partner_id', ['None', 'Sin proveedor'])[1]
            insumo['delay'] = provider.get('delay', 0)
            
            oc = existenciasOC.get(variant_id, 0)
    
            insumo['oc'] = oc if oc > 0 else 0

        return ({
            'status'   : 'success',
            'products' : insumosOdoo
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
def get_newInsumos(insumosIDs):
    #!Determinamos si existe conexión con odoo
    if not conOdoo.models:
        return ({
            'status'  : 'error',
            'message' : 'Error en la conexión con Odoo, no hay conexión Activa'
        })

    #funcion try para arrojar los insumos de odoo
    try:
        # Obtener todos los insumos que cumplan con las condiciones 
        insumosOdoo = conOdoo.models.execute_kw(
            conOdoo.db, conOdoo.uid, conOdoo.password,
            'product.template', 'search_read', 
            [[
                ('id', 'not in', insumosIDs),
                '|', ('active', '=', True), ('active', '=', False), 
                ('categ_id', 'ilike', 'INSUMO'), 
                ('categ_id.parent_id', 'not ilike', 'AGENCIA DIGITAL'), 
                ('default_code', 'not ilike', 'STUDIO'), 
                ('default_code', 'not ilike', 'T-S'), 
                ('default_code', 'not ilike', 'T-T')
            ]],
            {  'fields' : ['id', 'name', 'default_code', 'qty_available', 'product_brand_id', 'categ_id', 'route_ids', 'product_variant_id', 'purchase_ok', 'create_date', 'active'] }
        )
        
        insumosNoID = [insumo['id'] for insumo in insumosOdoo if not insumo['active']]             
        
        variants = {}
        if insumosNoID:
            variantIDs = conOdoo.models.execute_kw(
                conOdoo.db, conOdoo.uid, conOdoo.password,
                'product.product', 'search_read',
                [[
                    ('active', '=', False), 
                    ('product_tmpl_id', 'in', insumosNoID)
                ]],
                {'fields': ['id', 'product_tmpl_id']}
            )
            variants = {v['product_tmpl_id'][0]: v['id'] for v in variantIDs}
            
            # Asignar variants faltantes
            for insumo in insumosOdoo:
                if not insumo.get('product_variant_id') and insumo['id'] in variants:
                    insumo['product_variant_id'] = [variants[insumo['id']], '']
                
        idsT = [insumo['id'] for insumo in insumosOdoo]
            
        # Obtener reglas de maximos y minimos
        orderpointsOdoo = conOdoo.models.execute_kw(
            conOdoo.db, conOdoo.uid, conOdoo.password, 
            'stock.warehouse.orderpoint', 'search_read', 
            [[('product_tmpl_id', 'in', idsT)]],
            {  'fields' : ['product_tmpl_id', 'product_min_qty', 'product_max_qty']  }
        )
        orderpoints = {op['product_tmpl_id'][0]: op for op in orderpointsOdoo}
            
        # Obtener reglas de proveedores
        providersOdoo = conOdoo.models.execute_kw(
            conOdoo.db, conOdoo.uid, conOdoo.password,
            'product.supplierinfo', 'search_read', 
            [[('product_tmpl_id', 'in', idsT)]],
            {  'fields' : ['product_tmpl_id', 'partner_id', 'delay'] }
        )
        providers = {prov['product_tmpl_id'][0]: prov for prov in providersOdoo}
        
        existenciasOCOdoo = conOdoo.models.execute_kw(
            conOdoo.db, conOdoo.uid, conOdoo.password,
            'purchase.order.line', 'search_read',
            [[
                ('display_type', 'not in', ['line_note', 'line_section']),
                ('state', '!=', 'done'),
                ('order_id.state', 'not in', ['draft', 'sent']),
                ('order_id.receipt_status', '!=', 'full'),
                ('order_id.user_id', '=', 46)
            ]],
            {  'fields' : ['product_id', 'product_qty', 'qty_received', 'display_type']}
        )
        existenciasOC = {}
        
        for oc in existenciasOCOdoo:
            number = oc['product_qty'] - oc['qty_received']
            if oc['product_id'][0] not in existenciasOC and number > 0:
                existenciasOC[oc['product_id'][0]] = number
                
            elif oc['product_id'][0] in existenciasOC:
                existenciasOC[oc['product_id'][0]] += number
        
        # Por cada producto encontrado que cumpla las reglas, relaciona los valores con las 
        # reglas de maximos y minimos (orderpoints) y los proveedores (poviders)
        for insumo in insumosOdoo:
            insumo_id = insumo['id']
            variant_id = insumo['product_variant_id'][0] if insumo.get('product_variant_id') else 0
            
            orderpoint = orderpoints.get(insumo_id, {})
            insumo['product_min_qty'] = orderpoint.get('product_min_qty', 0)
            insumo['product_max_qty'] = orderpoint.get('product_max_qty', 0)

            provider = providers.get(insumo_id, {})
            insumo['provider'] = provider.get('partner_id', ['None', 'Sin proveedor'])[1]
            insumo['delay'] = provider.get('delay', 0)
            
            oc = existenciasOC.get(variant_id, 0)
    
            insumo['oc'] = oc if oc > 0 else 0

        return ({
            'status'   : 'success',
            'products' : insumosOdoo
        })

    except xmlrpc.client.Fault as e:
        return ({
            'status'       : 'error',
            'message'      : f'Error al ejecutar la consulta a Odoo: {str(e)}',
            'fault_code'   : e.faultCode,
            'fault_string' : e.faultString,
        })
        
        
        
        

# --------------------------------------------------------------------------------------------------
# * Función: get_updateInsumos
# * Descripción: Obtiene los productos de la base de datos de postgres (que únicamente sean insumos) de Odoo
#
# ! Parámetros:
#   - Recibe la lista de IDs de todos los productos existentes en Postgres
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
def get_updateInsumos(insumosIDs):
    #!Determinamos si existe conexión con odoo
    if not conOdoo.models:
        return ({
            'status'  : 'error',
            'message' : 'Error en la conexión con Odoo, no hay conexión Activa'
        })

    #funcion try para arrojar los insumos de odoo
    try:
        # Obtener todos los insumos que cumplan con las condiciones 
        insumosOdoo = conOdoo.models.execute_kw(
            conOdoo.db, conOdoo.uid, conOdoo.password,
            'product.template', 'search_read', 
            [[
                '|', ('active', '=', True), ('active', '=', False), 
                ('categ_id', 'ilike', 'INSUMO'), 
                ('categ_id.parent_id', 'not ilike', 'AGENCIA DIGITAL'), 
                ('default_code', 'not ilike', 'STUDIO'), 
                ('default_code', 'not ilike', 'T-S'), 
                ('default_code', 'not ilike', 'T-T')
            ]],
            {  'fields' : ['id', 'name', 'default_code', 'qty_available', 'product_brand_id', 'categ_id', 'route_ids', 'product_variant_id', 'purchase_ok', 'create_date', 'active'] }
        )
        
        insumosNoID = [insumo['id'] for insumo in insumosOdoo if not insumo['active']]             
        
        variants = {}
        if insumosNoID:
            variantIDs = conOdoo.models.execute_kw(
                conOdoo.db, conOdoo.uid, conOdoo.password,
                'product.product', 'search_read',
                [[
                    ('active', '=', False), 
                    ('product_tmpl_id', 'in', insumosNoID)
                ]],
                {'fields': ['id', 'product_tmpl_id']}
            )
            variants = {v['product_tmpl_id'][0]: v['id'] for v in variantIDs}
            
            # Asignar variants faltantes
            for insumo in insumosOdoo:
                if not insumo.get('product_variant_id') and insumo['id'] in variants:
                    insumo['product_variant_id'] = [variants[insumo['id']], '']
                
        idsT = [insumo['id'] for insumo in insumosOdoo]
            
        # Obtener reglas de maximos y minimos
        orderpointsOdoo = conOdoo.models.execute_kw(
            conOdoo.db, conOdoo.uid, conOdoo.password, 
            'stock.warehouse.orderpoint', 'search_read', 
            [[('product_tmpl_id', 'in', idsT)]],
            {  'fields' : ['product_tmpl_id', 'product_min_qty', 'product_max_qty']  }
        )
        orderpoints = {op['product_tmpl_id'][0]: op for op in orderpointsOdoo}
            
        # Obtener reglas de proveedores
        providersOdoo = conOdoo.models.execute_kw(
            conOdoo.db, conOdoo.uid, conOdoo.password,
            'product.supplierinfo', 'search_read', 
            [[('product_tmpl_id', 'in', idsT)]],
            {  'fields' : ['product_tmpl_id', 'partner_id', 'delay'] }
        )
        providers = {prov['product_tmpl_id'][0]: prov for prov in providersOdoo}
        
        existenciasOCOdoo = conOdoo.models.execute_kw(
            conOdoo.db, conOdoo.uid, conOdoo.password,
            'purchase.order.line', 'search_read',
            [[
                ('display_type', 'not in', ['line_note', 'line_section']),
                ('state', '!=', 'done'),
                ('order_id.state', 'not in', ['draft', 'sent']),
                ('order_id.receipt_status', '!=', 'full'),
                ('order_id.user_id', '=', 46)
            ]],
            {  'fields' : ['product_id', 'product_qty', 'qty_received', 'display_type']}
        )
        existenciasOC = {}
        
        for oc in existenciasOCOdoo:
            number = oc['product_qty'] - oc['qty_received']
            if oc['product_id'][0] not in existenciasOC and number > 0:
                existenciasOC[oc['product_id'][0]] = number
                
            elif oc['product_id'][0] in existenciasOC:
                existenciasOC[oc['product_id'][0]] += number
        
        # Por cada producto encontrado que cumpla las reglas, relaciona los valores con las 
        # reglas de maximos y minimos (orderpoints) y los proveedores (poviders)
        for insumo in insumosOdoo:
            insumo_id = insumo['id']
            variant_id = insumo['product_variant_id'][0] if insumo.get('product_variant_id') else 0
            
            orderpoint = orderpoints.get(insumo_id, {})
            insumo['product_min_qty'] = orderpoint.get('product_min_qty', 0)
            insumo['product_max_qty'] = orderpoint.get('product_max_qty', 0)

            provider = providers.get(insumo_id, {})
            insumo['provider'] = provider.get('partner_id', ['None', 'Sin proveedor'])[1]
            insumo['delay'] = provider.get('delay', 0)
            
            oc = existenciasOC.get(variant_id, 0)
    
            insumo['oc'] = oc if oc > 0 else 0

        return ({
            'status'   : 'success',
            'products' : insumosOdoo
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