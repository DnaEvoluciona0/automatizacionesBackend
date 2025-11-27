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
from unidades.marketing.autorepcuentas.views.api_views import sync_accounts, sync_ads, sync_adsets, sync_campaigns, list_accounts, extract_ads, extract_adsets, extract_campaigns
from unidades.marketing.autorepcuentas.views.web_views import dashboard, cuentas, extraccion, reportes, generar_reporte_excel

urlpatterns = [
    path('admin/', admin.site.urls),

    #!Rutas de productos e insumos
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
    path('auto/pullClientesExcel/', pullClientesExcel),
    path('auto/createClientesOdoo/', createClientesOdoo),
    path('auto/updateClientesOdoo/', updateClientesOdoo),
    
    #!Rutas para Ventas
    path('auto/pullVentasOdoo/', pullVentasOdoo),
    path('auto/pullVentasExcel/', pullVentasExcel), #!
    path('auto/createVentasOdoo/', createVentasOdoo),
    
    #!Rutas Actualizar Max y Min Insumos
    #!path('auto/updatemaxmin/', updateMinMax),

    #! Rutas para Marketing - Meta Ads (AutoRepCuentas)
    #! API Endpoints
    path('auto/marketing/accounts/sync/', sync_accounts),
    path('auto/marketing/accounts/list/', list_accounts),
    path('auto/marketing/campaigns/extract/', extract_campaigns),
    path('auto/marketing/campaigns/sync/', sync_campaigns),
    path('auto/marketing/adsets/extract/', extract_adsets),
    path('auto/marketing/adsets/sync/', sync_adsets),
    path('auto/marketing/ads/extract/', extract_ads),
    path('auto/marketing/ads/sync/', sync_ads),

    #! Web Pages - Marketing Dashboard
    path('marketing/', dashboard, name='marketing_dashboard'),
    path('marketing/cuentas/', cuentas, name='marketing_cuentas'),
    path('marketing/extraccion/', extraccion, name='marketing_extraccion'),
    path('marketing/reportes/', reportes, name='marketing_reportes'),
    path('marketing/reportes/generar/', generar_reporte_excel, name='marketing_generar_reporte'),
]
