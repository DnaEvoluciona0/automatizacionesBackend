from django.db import models
from datetime import datetime

#? Tabla de productos en el eschema de produccionLogistica
class Productos(models.Model):
    nombre = models.CharField(max_length=200)
    sku = models.CharField(max_length=100)
    marca = models.CharField(max_length=150, default='')
    maxActual = models.IntegerField()
    minActual = models.IntegerField()
    existenciaActual =  models.IntegerField(default=0)
    categoria = models.CharField(max_length=150, default='')
    tipoProducto = models.CharField(max_length=100, default='')
    fechaCreacion = models.DateTimeField(default=datetime.now)
    
    class Meta:
        db_table = '"produccionlogistica"."productos"'
    
#? Tabla de insumos en el eschema de produccionLogistica
class Insumos(models.Model):
    nombre = models.CharField(max_length=200)
    sku = models.CharField(max_length=15)
    marca = models.CharField(max_length=150, default='')
    maxActual = models.IntegerField()
    minActual = models.IntegerField()
    existenciaActual =  models.IntegerField(default=0)
    categoria = models.CharField(max_length=150, default='')
    proveedor = models.CharField(max_length=200, default='')
    tiempoEntrega = models.IntegerField(default=0)
    
    class Meta:
        db_table = '"produccionlogistica"."insumos"'
    
#? Tabla de los insumos que ocupa cada producto en el eschema de produccionLogistica
class MaterialPI(models.Model):
    producto = models.ForeignKey(Productos, on_delete=models.CASCADE)
    insumo = models.ForeignKey(Insumos, on_delete=models.CASCADE)
    cantidad = models.FloatField()

    class Meta:
        unique_together = ('producto', 'insumo')
        db_table = '"produccionlogistica"."materialPI"'
