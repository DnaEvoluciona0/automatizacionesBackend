import xmlrpc.client
from conexiones.conectionOdoo import OdooAPI
from datetime import datetime, timedelta
import pandas as pd

#?Intancia de conexión a Odoo
conn=OdooAPI()

#?Obtiene un archivo mendiante la url y lo abre en la pestaña necesaria para su posterior lectura
archivo = 'static/ContpaqBD.xlsx'
dfVenta = pd.read_excel(archivo, sheet_name='pvh')


# --------------------------------------------------------------------------------------------------
# * Función: get_allSales
# * Descripción: Obtiene todos las Ventas/Facturas y notas de credito de Odoo
#
# ! Parámetros:
#   - No recibe ningún parámetro
#
# ? Condiciones para saber que ventas obtener
#   1. El "status" debe ser:
#       - Posted
#   2. El "move_type" debe ser:
#       - out_invoice
#       - out_refund
#   3. El "branch_id" no debe contener:
#       - STUDIO
#       - TORRE
#   4. El "name" de la venta debe contener
#       - INV/
#       - BONIF/
#       - MUEST/
#
# ? Return:
#   - Caso success:
#       Retorna un JSON con el status success y una lista (array) de ventas. Cada venta contiene los siguientes campos:
#       {  id, nombre, fechaCreacion, cliente, vendedor, direccionEnvio, unidad, totalVenta, tipoFactura, lineaProducto {[idProducto, nombreProducto, cantidad, precioUnitario, precioSubtotal, marca, categoria], ...}, pais, estado, ciudad  }
#   - Caso error: 
#       En caso de haber ocurrido algun error retorna un JSON con status error y el mensaje del error
# --------------------------------------------------------------------------------------------------
def get_allSales():
    #!Determinamos que haya algna conexión con Odoo
    if not conn.models:
        return ({
            'status'  : 'error',
            'message' : 'Error en la conexión con Odoo, no hay conexión Activa'
        })
    
    #función try para obtener las facturas
    try: 
        #Busca en odoo las ventas que complan con las siguientes condiciones dadas
        order_sale = conn.models.execute_kw(
            conn.db, conn.uid, conn.password, 
            'account.move', 'search_read', 
            [[['team_id', 'not ilike', 'STUDIO 105'], ['state', '=', 'posted'], '|', ['move_type', '=', 'out_invoice'], ['move_type', '=', 'out_refund'], ['branch_id', 'not ilike', 'STUDIO'], ['branch_id', 'not ilike', 'TORRE'], '|', '|', ['name', 'ilike', 'INV/'], ['name', 'ilike', 'MUEST/'], ['name', 'ilike', 'BONIF/']]],
            { 'fields' : ['name', 'invoice_date', 'partner_id', 'invoice_user_id', 'partner_shipping_id', 'branch_id', 'amount_total_signed', 'move_type', 'team_id']}
        )
                
        #Lista de Ids que se buscaran
        ordersID=[]
        shippingID=[]
        
        #Obtiene los IDS de la orden y de la dirección para guardarlos en un a lista
        for order in order_sale:
            ordersID.append(order['id'])
            if order['partner_shipping_id']:
                shippingID.append(order['partner_shipping_id'][0])
        
        #Hace una unica busqueda donde encuentra todas las lineas de productos que coincidan con el id de la lista de facturas
        products_data={}
        all_product_line = conn.models.execute_kw(
            conn.db, conn.uid, conn.password, 
            'account.move.line', 'search_read', 
            [[['move_id', 'in', ordersID], '|', '|', ['account_type', '=', 'income'], ['account_type', '=', 'expense'], ['account_type', '=', False]]],
            { 'fields' :['name', 'product_id', 'quantity', 'price_unit', 'price_subtotal', 'x_studio_marca', 'x_studio_related_field_e1jP7', 'move_id', 'account_type']}
        )
        
        #Las guarda todas en un objetos junto con el id de la factura como id principal para encontrarla
        for line in all_product_line:
            #Crea la propiedad sin ningun producto
            if line['move_id'][0] not in products_data:
                products_data[line['move_id'][0]]=[]
            
            #Agrega los productos necesarios a esa misma propiedad
            if line['move_id'][0] in products_data:
                products_data[line['move_id'][0]].append(line)
        
        shipping_data={}
        #Busca en los contactos la información de cada uno
        all_shippings=conn.models.execute_kw(
            conn.db, conn.uid, conn.password, 
            'res.partner', 'search_read', 
            [[['id', 'in', shippingID]]],
            { 'fields' : ['city', 'state_id', 'country_id',]}
        )
        
        #Guarda la informacion del cliente con su id de contacto como propiedad
        for dir in all_shippings:
            shipping_data[dir['id']]=dir
        
        #Para cada orden busca la información en los objetos products_data y shipping_data
        for order in order_sale:
            #Busca el id de orden en la propiedad que sea el mismo id en move_id
            products = products_data[order['id']]
            
            #Agrega una propiedad de productLines con los productos de la venta a la orden
            order['productsLines'] = products
            
            #Busca en shipping_data aquel id de cliente a donde se envia el producto y si contiene algo, guarda la información, y si no lo contiene guarda la información
            direccion = shipping_data[order['partner_shipping_id'][0]] if order['partner_shipping_id'][0] in shipping_data else {'country_id': False, 'state_id':False, 'city': False}
            
            #Agrega las propiedades country_id, state_id y city a la orden, si es False lo guarda como vacio
            order['country_id'] = direccion['country_id'][1] if direccion['country_id'] else ""
            order['state_id'] = direccion['state_id'][1] if direccion['state_id'] else ""
            order['city'] = direccion['city'] if direccion['city'] else ""
        
        #Retorna las ventas con toda la información necesaria
        return ({
            'status'  : 'success',
            'ventas' : order_sale
        })
    
    except xmlrpc.client.Fault as e:
        return ({
            'status'       : 'error',
            'message'      : f'Error al ejecutar la consulta a Odoo: {str(e)}',
            'fault_code'   : e.faultCode,
            'fault_string' : e.faultString,
        })
        
        
# --------------------------------------------------------------------------------------------------
# * Función: get_newSales
# * Descripción: Obtiene todos las Ventas/Facturas y notas de credito de Odoo desde el día anterior
#
# ! Parámetros:
#   - No recibe ningún parámetro
#
# ? Condiciones para saber que ventas obtener
#   1. El "status" debe ser:
#       - Posted
#   2. El "move_type" debe ser:
#       - out_invoice
#       - out_refund
#   3. El "branch_id" no debe contener:
#       - STUDIO
#       - TORRE
#   4. El "name" de la venta debe contener
#       - INV/
#       - BONIF/
#       - MUEST/
#   5. "create_date" debe ser menor a un dia
#
# ? Return:
#   - Caso success:
#       Retorna un JSON con el status success y una lista (array) de ventas. Cada venta contiene los siguientes campos:
#       {  id, nombre, fechaCreacion, cliente, vendedor, direccionEnvio, unidad, totalVenta, tipoFactura, lineaProducto {[idProducto, nombreProducto, cantidad, precioUnitario, precioSubtotal, marca, categoria], ...}, pais, estado, ciudad  }
#   - Caso error: 
#       En caso de haber ocurrido algun error retorna un JSON con status error y el mensaje del error
# -------------------------------------------------------------------------------------------------- 
def get_newSales():
    #!Determinamos que haya algna conexión con Odoo
    if not conn.models:
        return ({
            'status'  : 'error',
            'message' : 'Error en la conexión con Odoo, no hay conexión Activa'
        })
    
    #función try para obtener las facturas
    try:
        #Obtiene el dia anterior al dia de hoy
        lastDay = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
        #Busca en odoo las ventas que complan con las siguientes condiciones dadas
        order_sale = conn.models.execute_kw(
            conn.db, conn.uid, conn.password, 
            'account.move', 'search_read', 
            [[['create_date', '>=', lastDay], ['state', '=', 'posted'], '|', ['move_type', '=', 'out_invoice'], ['move_type', '=', 'out_refund'], ['branch_id', 'not ilike', 'STUDIO'], ['branch_id', 'not ilike', 'TORRE'], '|', '|', ['name', 'ilike', 'INV/'], ['name', 'ilike', 'MUEST/'], ['name', 'ilike', 'BONIF/']]],
            { 'fields' : ['name', 'invoice_date', 'partner_id', 'invoice_user_id', 'partner_shipping_id', 'branch_id', 'amount_total_signed', 'move_type']}
        )
                
        #Lista de Ids que se buscaran
        ordersID=[]
        shippingID=[]
        
        #Obtiene los IDS de la orden y de la dirección para guardarlos en un a lista
        for order in order_sale:
            ordersID.append(order['id'])
            if order['partner_shipping_id']:
                shippingID.append(order['partner_shipping_id'][0])
        
        #Hace una unica busqueda donde encuentra todas las lineas de productos que coincidan con el id de la lista de facturas
        products_data={}
        all_product_line = conn.models.execute_kw(
            conn.db, conn.uid, conn.password, 
            'account.move.line', 'search_read', 
            [[['move_id', 'in', ordersID], '|', '|', ['account_type', '=', 'income'], ['account_type', '=', 'expense'], ['account_type', '=', False]]],
            { 'fields' :['name', 'product_id', 'quantity', 'price_unit', 'price_subtotal', 'x_studio_marca', 'x_studio_related_field_e1jP7', 'move_id']}
        )
        
        #Las guarda todas en un objetos junto con el id de la factura como id principal para encontrarla
        for line in all_product_line:
            #Crea la propiedad sin ningun producto
            if line['move_id'][0] not in products_data:
                products_data[line['move_id'][0]]=[]
            
            #Agrega los productos necesarios a esa misma propiedad    
            if line['move_id'][0] in products_data:
                products_data[line['move_id'][0]].append(line)
        
        shipping_data={}
        #Busca en los contactos la información de cada uno
        all_shippings=conn.models.execute_kw(
            conn.db, conn.uid, conn.password, 
            'res.partner', 'search_read', 
            [[['id', 'in', shippingID]]],
            { 'fields' : ['city', 'state_id', 'country_id',]}
        )
        
        #Guarda la informacion del cliente con su id de contacto como propiedad
        for dir in all_shippings:
            shipping_data[dir['id']]=dir
        
        #Para cada orden busca la información en los objetos products_data y shipping_data
        for order in order_sale:
            #Busca el id de orden en la propiedad que sea el mismo id en move_id
            products = products_data[order['id']]
            
            #Agrega una propiedad de productLines con los productos de la venta a la orden
            order['productsLines'] = products
            
            #Busca en shipping_data aquel id de cliente a donde se envia el producto y si contiene algo, guarda la información, y si no lo contiene guarda la información
            direccion = shipping_data[order['partner_shipping_id'][0]] if order['partner_shipping_id'][0] in shipping_data else {'country_id': False, 'state_id':False, 'city': False}
            
            #Agrega las propiedades country_id, state_id y city a la orden, si es False lo guarda como vacio
            order['country_id'] = direccion['country_id'][1] if direccion['country_id'] else ""
            order['state_id'] = direccion['state_id'][1] if direccion['state_id'] else ""
            order['city'] = direccion['city'] if direccion['city'] else ""
        
        #Retorna las ventas con toda la información necesaria
        return ({
            'status'  : 'success',
            'ventas' : order_sale
        })
    
    except xmlrpc.client.Fault as e:
        return ({
            'status'       : 'error',
            'message'      : f'Error al ejecutar la consulta a Odoo: {str(e)}',
            'fault_code'   : e.faultCode,
            'fault_string' : e.faultString,
        })


# --------------------------------------------------------------------------------------------------
# * Función: pullVentasExcel
# * Descripción: Obtiene todos las Ventas/Facturas y notas de credito de un excel
#
# ! Parámetros:
#   - No recibe ningún parámetro
#
# ? Condiciones para saber que productos obtener
#   1. Debe estar en la página de ventas:
#       - 
#
# ? Return:
#   - Caso success:
#       Retorna un JSON con el status success y una lista (array) de ventas. Cada venta contiene los siguientes campos:
#       {  id, nombre, fechaCreacion, cliente, vendedor, direccionEnvio, unidad, totalVenta, tipoFactura, lineaProducto {[idProducto, nombreProducto, cantidad, precioUnitario, precioSubtotal, marca, categoria], ...}, pais, estado, ciudad  }
#   - Caso error: 
#       En caso de haber ocurrido algun error retorna un JSON con status error y el mensaje del error
# -------------------------------------------------------------------------------------------------- 
def pullVentasExcel():
    #!Determinamos que haya algna conexión con Odoo
    if not conn.models:
        return ({
            'status'  : 'error',
            'message' : 'Error en la conexión con Odoo, no hay conexión Activa'
        })
    
    #función try para obtener las facturas
    try:
        #Llamamos al excel en la página de ventas
        df = pd.read_excel(archivo, sheet_name='Ventas')
        order_sale=[]
        
        #Obtenemos los ids de clientes unicos
        clients_ids= df['idcliente'].unique().tolist()
        
        #Buscamos la direccion de cada cliente que este en clients_ids
        direccion = conn.models.execute_kw(
            conn.db, conn.uid, conn.password, 
            'res.partner', 'search_read', 
            [[['id', 'in', clients_ids], '|', ['active', '=', True], ['active', '=', False]]],
            { 'fields' : ['city', 'state_id', 'country_id']}
        )
        
        shipping_data = {}
        #Para cada direccion encontrada se guarda como valor y como propiedad le ponemos el id del cliente
        for dir in direccion:
            shipping_data[dir['id']]=dir
        
        #Recorrer cada linea que hay en el excel
        for index, venta in df.iterrows():
            
            #Obtenemos todos los productos del excel en la pagina de pvh que coincidad con el idVenta
            productos=dfVenta[dfVenta['idVenta']==venta['idVenta']]
            productList=[]
            total=0
            
            #Para cada linea de producto obtenido obtenemos sus valores que seran guardados en productList y ademas sumamos sus subtotales para saber el total de la venta
            for indexP, prod in productos.iterrows():
                productList.append({
                    'id': indexP, 
                    'name': '['+prod['SKU']+'] '+prod['nombreProducto'], 
                    'product_id': str(index), 
                    'quantity': prod['Cantidad facturada'], 
                    'price_unit': prod['Precio unitario'], 
                    'price_subtotal': prod['Total'], 
                    'x_studio_marca': prod['Marca'], 
                    'x_studio_related_field_e1jP7': prod['categoria'], 
                    'move_id': prod['idVenta']
                })
                total=total+prod['Total']
            
            #Si el idcliente de nuestra venta en excel se encuentra en shipping_data, agrega los valores encontrados y si no setea los valores necesarios como false
            direccion = shipping_data[venta['idcliente']] if venta['idcliente'] in shipping_data else {'country_id': False, 'state_id':False, 'city': False}
            
            #Si se encontro seteo la direccion añade todos los valores recolectados a order_sale
            if direccion:
                order_sale.append({
                    'id': index,
                    'name': venta["idVenta"],
                    'invoice_date': venta["Fecha"],
                    'partner_id': [venta["idcliente"]],
                    'invoice_user_id': [None, venta["vendedor"]],
                    'partner_shipping_id': venta["idcliente"],
                    'branch_id': [None, venta["unidad"]],
                    'amount_total_signed': total,
                    'move_type': 'out_invoice',
                    'productsLines': productList,
                    'country_id': direccion['country_id'][1] if direccion['country_id'] else "",
                    'state_id': direccion['state_id'][1] if direccion['state_id'] else "",
                    'city': direccion['city'] if direccion['city'] != False else ""
                })
                    
        #Retorna todas las ventas   
        return ({
            'status'  : 'success',
            'ventas' : order_sale
        })
        
    except xmlrpc.client.Fault as e:
        return ({
            'status'       : 'error',
            'message'      : f'Error al ejecutar la consulta a Odoo: {str(e)}',
            'fault_code'   : e.faultCode,
            'fault_string' : e.faultString,
        })