from django.db import models
from unidades.produccionLogistica.maxMin.models import Insumos, Productos

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
    idCliente = models.ForeignKey(Clientes, related_name="ventasCliente", on_delete=models.CASCADE)
    paisVenta = models.CharField(max_length=100)
    estadoVenta = models.CharField(max_length=100)
    ciudadVenta = models.CharField(max_length=200)
    unidad = models.CharField(max_length=20)
    vendedor = models.CharField(max_length=200)
    total = models.DecimalField(decimal_places=2, max_digits=20)
    
    class Meta:
        db_table = '"administracion"."ventas"'

#? Tabla de ventasPVA en el esquema de produccionLogistica
class VentasPVA(models.Model):
    fecha = models.DateTimeField()
    idProducto = models.ForeignKey(Productos, related_name="ventasPVProducto", on_delete=models.CASCADE, null=True)
    idInsumo = models.ForeignKey(Insumos, related_name="ventasPVInsumos", on_delete=models.CASCADE, null=True)
    cantidad = models.BigIntegerField()
    
    class Meta:
        db_table = '"produccionlogistica"."ventaspva"'

#? Tabla de ventasPVH en el esquema de administracion
class VentasPVH(models.Model):
    idVenta = models.ForeignKey(Ventas, related_name="ventasPVVenta", on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    sku = models.CharField(max_length=20)
    marca = models.CharField(max_length=50)
    categoria = models.CharField(max_length=100, default="")
    cantidad = models.BigIntegerField()
    precioUnitario = models.DecimalField(decimal_places=2, max_digits=20)
    subtotal = models.DecimalField(decimal_places=2, max_digits=20)
    
    class Meta:
        db_table = '"administracion"."ventaspvh"'

#? Tabla de ventasPVA en el esquema de produccionLogistica
class Caducidades(models.Model):
    fechaCaducidad = models.DateField()
    cantidad = models.IntegerField()
    productoId = models.ForeignKey(Productos, related_name="productoCaducidad", on_delete=models.CASCADE)
    
    class Meta:
        db_table = '"produccionlogistica"."caducidades"'