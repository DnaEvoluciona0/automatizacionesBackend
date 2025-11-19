"""
URL configuration for automatizacionesDna project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

#Rutas agregadas
from unidades.produccionLogistica.maxMin.dataMaxMin import updateMinMax
from unidades.produccionLogistica.maxMin.views.viewsProducto import pullProductsOdoo, createProductsOdoo, updateProductsOdoo, pullProductsExcel
from unidades.produccionLogistica.maxMin.views.viewsInsumo import pullInsumosOdoo, updateInsumosOdoo, createInsumosOdoo
from unidades.produccionLogistica.maxMin.views.viewsMaterialPI import pullMaterialPIOdoo
from unidades.administracion.reporteVentas.views.viewsClientes import pullClientesOdoo, pullClientesExcel, createClientesOdoo, updateClientesOdoo
from unidades.administracion.reporteVentas.views.viewsVentas import pullVentasOdoo, pullVentasExcel, createVentasOdoo
from unidades.administracion.reporteVentas.views.viewsCaducidades import pullCaducidadesOdoo, createCaducidadesOdoo, updateCaducidadesOdoo

urlpatterns = [
    path('admin/', admin.site.urls),

    #!Rutas de productos
    path('auto/pullProductsOdoo/', pullProductsOdoo),
    path('auto/pullInsumosOdoo/', pullInsumosOdoo),
    path('auto/pullProductsExcel/', pullProductsExcel),
    path('auto/createProductsOdoo/', createProductsOdoo),
    path('auto/createInsumosOdoo/', createInsumosOdoo),
    path('auto/updateProductsOdoo/', updateProductsOdoo),
    path('auto/updateInsumosOdoo/', updateInsumosOdoo),

    #!Rutas para MaterialesPI
    path('auto/pullMaterialPIOdoo/', pullMaterialPIOdoo),
    
    #!Rutas para BajaRotación
    path('auto/pullCaducidadesOdoo/', pullCaducidadesOdoo), #? En el total son menos 5 por que no cumple el formato de fecha para registrarse
    path('auto/createCaducidadesOdoo/', createCaducidadesOdoo),
    path('auto/updateCaducidadesOdoo/', updateCaducidadesOdoo),
    
    #!Rutas para Clientes
    path('auto/pullClientesOdoo/', pullClientesOdoo),
    path('auto/createClientesOdoo/', createClientesOdoo),
    path('auto/updateClientesOdoo/', updateClientesOdoo),
    path('auto/pullClientesExcel/', pullClientesExcel),
    
    #!Rutas para Ventas
    path('auto/pullVentasOdoo/', pullVentasOdoo),
    path('auto/pullVentasExcel/', pullVentasExcel), #!
    path('auto/createVentasOdoo/', createVentasOdoo),
    path('auto/pullVentasExcel/', pullVentasExcel),
    
    #!Rutas Actualizar Max y Min Insumos
    #!path('auto/updatemaxmin/', updateMinMax),
]
