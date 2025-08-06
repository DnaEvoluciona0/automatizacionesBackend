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
from unidades.produccionLogistica.maxMin.views.viewProducto import pullProductsOdoo, getProductsPSQL, updateProducts, createNewProductsFromOdoo
from unidades.produccionLogistica.maxMin.views.viewInsumo import pullInsumosOdoo, getInsumosPSQL, updateInsumosOdoo, createNewInsumosFromOdoo
from unidades.produccionLogistica.maxMin.views.viewsMaterialPI import getMaterialsPIPSQL, pullMaterialPi
from unidades.administracion.reporteVentas.views.viewsClientes import *
from unidades.administracion.reporteVentas.views.viewsVentas import *
from unidades.administracion.reporteVentas.views.viewsCaducidades import *

urlpatterns = [
    path('admin/', admin.site.urls),

    #!Rutas Actualizar Max y Min Insumos
    path('auto/updatemaxmin/', updateMinMax),

    #!Rutas de productos
    path('auto/pullProductsOdoo/', pullProductsOdoo),
    path('auto/updateProducts/', updateProducts),
    path('auto/createProductsOdoo/', createNewProductsFromOdoo),

    #!Rutas de Insumos
    path('auto/pullInsumosOdoo/', pullInsumosOdoo),
    path('auto/updateInsumosOdoo/', updateInsumosOdoo),
    path('auto/createInsumosOdoo/', createNewInsumosFromOdoo),

    #!Rutas para MaterialesPI
    path('auto/pullMaterialPIOdoo/', pullMaterialPi),
    
    #!Rutas para Clientes
    path('auto/pullClientesOdoo/', pullClientesOdoo),
    path('auto/pullClientesExcel/', createClientesExcel),
    path('auto/createClientesOdoo/', createClientesOdoo),
    path('auto/updateClientesOdoo/', updateClientesOdoo),
    
    #!Rutas para Ventas
    path('auto/pullVentasOdoo/', pullVentasOdoo),
    path('auto/pullVentasExcel/', createSalesExcel),
    path('auto/createVentasOdoo/', createVentasOdoo),
    
    #!Rutas para BajaRotación
    path('auto/pullCaducidadesOdoo/', pullCaducidadesOdoo),
    path('auto/createCaducidadesOdoo/', createCaducidadesOdoo),
    path('auto/updateCaducidadesOdoo/', updateCaducidadesOdoo)
    
]
