from django.db import models
from unidades.produccionLogistica.maxMin.models import Productos

#? Tabla de clientes en el esquema de administracion
class Clientes(models.Model):
    idCliente=models.BigIntegerField(primary_key=True)
    nombre = models.CharField(max_length=200)
    pais = models.CharField(max_length=100)
    estado = models.CharField(max_length=100)
    ciudad = models.CharField(max_length=200)
    tipoCliente=models.CharField(max_length=20, default="Cliente Nuevo")
    numTransacciones=models.BigIntegerField(default=0)
    
    class Meta:
        db_table = '"administracion"."clientes"'

#? Tabla de ventas en el esquema de administracion
class Ventas(models.Model):
    idVenta = models.CharField(max_length=20, primary_key=True)
    fecha = models.DateTimeField()
    cliente = models.ForeignKey(Clientes, related_name="ventasCliente", on_delete=models.CASCADE)
    tipoCliente=models.CharField(max_length=20, default="Cliente Nuevo")
    paisVenta = models.CharField(max_length=100)
    estadoVenta = models.CharField(max_length=100)
    ciudadVenta = models.CharField(max_length=200)
    unidad = models.CharField(max_length=20)
    vendedor = models.CharField(max_length=200)
    total = models.DecimalField(decimal_places=2, max_digits=20)
    
    class Meta:
        db_table = '"administracion"."ventas"'

#? Tabla de ventasPVH en el esquema de administracion
class VentasPVH(models.Model):
    idPVH = models.BigAutoField(primary_key=True)
    venta = models.ForeignKey(Ventas, related_name="ventasPVHVenta", on_delete=models.CASCADE)
    producto = models.ForeignKey(Productos, related_name="ventasPVHProducto", on_delete=models.CASCADE, null=True)
    cantidad = models.BigIntegerField()
    precioUnitario = models.DecimalField(decimal_places=2, max_digits=20)
    subtotal = models.DecimalField(decimal_places=2, max_digits=20)
    
    class Meta:
        db_table = '"administracion"."ventaspvh"'

#? Tabla de ventasPVA en el esquema de produccionLogistica
class Caducidades(models.Model):
    fechaCaducidad = models.DateField()
    cantidad = models.IntegerField()
    producto = models.ForeignKey(Productos, related_name="productoCaducidad", on_delete=models.CASCADE)
    
    class Meta:
        db_table = '"produccionlogistica"."caducidades"'