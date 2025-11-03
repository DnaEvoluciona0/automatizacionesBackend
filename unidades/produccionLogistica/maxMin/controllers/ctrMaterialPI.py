import xmlrpc.client

from conexiones.conectionOdoo import OdooAPI

#? Instancia de conexión a Odoo
conOdoo = OdooAPI()

# --------------------------------------------------------------------------------------------------
# * Función: getInsumoByProduct
# * Descripción: Obtiene todos las reglas de materiales entre productos e insumos
#
# ! Parámetros:
#   - No recibe ningún parámetro
#
# ? Condiciones para saber que retornar
#   - Esta función solo retornará las reglas de materiales establecidas en Odoo
#   - Esta arrojará el id del producto y el id del insumo que cuenta como material
#
# ? Return:
#   - Caso success:
#       Retorna un JSON con el status success y una lista (array) de productos. cada producto contiene los siguientes campos:
#       Retorna los valores de {  id_prducto, id_insumo, cantidad  }
#   - Caso error: 
#       En caso de haber ocurrido algun error retorna un JSON con status error y el mensaje del error
# --------------------------------------------------------------------------------------------------
def getInsumoByProduct():
    #!Determinamos si existe conexión con odoo
    if not conOdoo.models:
        return ({
            'status'  : 'error',
            'message' : 'Error en la conexión con Odoo, no hay conexión Activa'
        })

    #Función try para traer todos los materiales
    try:
        # Obtener las reglas de materiales en el modelo mrp.bom.line
        mrp_bom_line = conOdoo.models.execute_kw(
            conOdoo.db, conOdoo.uid, conOdoo.password,
            'mrp.bom.line', 'search_read',
            [[]],
            {  'fields' : ['product_tmpl_id', 'parent_product_tmpl_id', 'product_qty'] }
        )

        return ({
            'status'  : 'success',
            'materiales' : mrp_bom_line
        })

    except xmlrpc.client.Fault as e:
        return ({
            'status'       : 'error',
            'message'      : f'Error al ejecutar la consulta a Odoo: {str(e)}',
            'fault_code'   : e.faultCode,
            'fault_string' : e.faultString,
        })