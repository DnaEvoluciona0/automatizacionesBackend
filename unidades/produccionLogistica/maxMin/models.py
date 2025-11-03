from django.db import models
from datetime import datetime

#? Tabla de productos en el eschema de produccionLogistica
class Productos(models.Model):
    idProductoTmp=models.BigIntegerField(primary_key=True)
    idProducto=models.BigIntegerField(default=0)
    nombre = models.CharField(max_length=200)
    sku = models.CharField(max_length=100)
    marca = models.CharField(max_length=150, default='')
    maxActual = models.IntegerField(default=0)
    minActual = models.IntegerField(default=0)
    existenciaActual =  models.IntegerField(default=0)
    existenciaOC = models.IntegerField(default=0)
    categoria = models.CharField(max_length=150, default='')
    tipo = models.CharField(max_length=100, default='')
    fechaCreacion = models.DateTimeField(default=datetime.now)
    proveedor = models.CharField(max_length=200, default='')
    tiempoEntrega = models.IntegerField(default=0)
    
    class Meta:
        db_table = '"produccionlogistica"."productos"'
    
    
#? Tabla de los insumos que ocupa cada producto en el eschema de produccionLogistica
class MaterialPI(models.Model):
    idPadre = models.ForeignKey(Productos, related_name="padreProducto", on_delete=models.CASCADE, null=True)
    idHijo = models.ForeignKey(Productos, related_name="MaterialProducto", on_delete=models.CASCADE, null=True)
    cantidad = models.FloatField()

    class Meta:
        db_table = '"produccionlogistica"."materialpi"'
