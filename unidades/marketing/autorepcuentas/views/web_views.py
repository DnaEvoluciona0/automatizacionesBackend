#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WEB VIEWS - AutoRepCuentas
Vistas de Django para paginas web del sistema de marketing
"""

import os
import json
from datetime import datetime, timedelta
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.db.models import Sum, Count
from django.db.models.functions import Coalesce

from ..models import Accounts, Campaigns, Adsets, Ads


def get_config():
    """Lee la configuracion desde config.json"""
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'config.json'
    )
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {'accounts': {}}


# =====================================
# DASHBOARD
# =====================================

def dashboard(request):
    """Vista principal del dashboard de marketing"""

    # Obtener estadisticas
    total_cuentas = Accounts.objects.filter(is_active=True).count()
    total_campaigns = Campaigns.objects.values('campaign_id').distinct().count()
    total_adsets = Adsets.objects.values('adset_id').distinct().count()
    total_ads = Ads.objects.values('ad_id').distinct().count()

    # Ultimas cuentas
    ultimas_cuentas = Accounts.objects.filter(is_active=True).order_by('account_key')[:5]

    # Resumen de inversion por cuenta (ultimos 30 dias)
    fecha_inicio = datetime.now() - timedelta(days=30)
    resumen_inversion = Campaigns.objects.filter(
        insights_date_start__gte=fecha_inicio
    ).values('account_name').annotate(
        total_spend=Coalesce(Sum('spend'), 0),
        total_impressions=Coalesce(Sum('impressions'), 0)
    ).order_by('-total_spend')[:5]

    context = {
        'active_page': 'dashboard',
        'fecha_actual': datetime.now().strftime('%d/%m/%Y'),
        'total_cuentas': total_cuentas,
        'total_campaigns': total_campaigns,
        'total_adsets': total_adsets,
        'total_ads': total_ads,
        'ultimas_cuentas': ultimas_cuentas,
        'resumen_inversion': resumen_inversion,
    }

    return render(request, 'autorepcuentas/dashboard.html', context)


# =====================================
# CUENTAS
# =====================================

def cuentas(request):
    """Vista de gestion de cuentas"""

    # Obtener cuentas de la base de datos
    cuentas_list = Accounts.objects.all().order_by('account_key')

    # Estadisticas
    total_cuentas = cuentas_list.count()
    cuentas_activas = cuentas_list.filter(is_active=True).count()
    cuentas_multimarca = cuentas_list.filter(multimarca='Si').count()

    context = {
        'active_page': 'cuentas',
        'cuentas': cuentas_list,
        'total_cuentas': total_cuentas,
        'cuentas_activas': cuentas_activas,
        'cuentas_multimarca': cuentas_multimarca,
    }

    return render(request, 'autorepcuentas/cuentas.html', context)


# =====================================
# EXTRACCION
# =====================================

def extraccion(request):
    """Vista de extraccion de datos"""

    # Obtener cuentas desde config.json
    config = get_config()
    cuentas_config = []

    for key, data in sorted(config.get('accounts', {}).items(), key=lambda x: int(x[0])):
        cuentas_config.append({
            'account_key': key,
            'account_name': data.get('nombre', ''),
            'account_id': data.get('account_id', ''),
            'marcas': data.get('marcas', ''),
        })

    # Verificar si hay cuenta seleccionada
    selected_account = request.GET.get('account_key', '')

    context = {
        'active_page': 'extraccion',
        'cuentas': cuentas_config,
        'selected_account': selected_account,
    }

    return render(request, 'autorepcuentas/extraccion.html', context)


# =====================================
# REPORTES
# =====================================

def reportes(request):
    """Vista de generacion de reportes"""

    # Obtener cuentas de la base de datos
    cuentas_list = Accounts.objects.filter(is_active=True).order_by('account_key')

    # Estadisticas
    total_campaigns = Campaigns.objects.values('campaign_id').distinct().count()
    total_adsets = Adsets.objects.values('adset_id').distinct().count()
    total_ads = Ads.objects.values('ad_id').distinct().count()

    # Inversion total
    total_spend = Campaigns.objects.aggregate(
        total=Coalesce(Sum('spend'), 0)
    )['total']

    # Reportes recientes (placeholder - se puede implementar historial)
    reportes_recientes = []

    context = {
        'active_page': 'reportes',
        'cuentas': cuentas_list,
        'total_campaigns': total_campaigns,
        'total_adsets': total_adsets,
        'total_ads': total_ads,
        'total_spend': total_spend,
        'reportes_recientes': reportes_recientes,
    }

    return render(request, 'autorepcuentas/reportes.html', context)


def generar_reporte_excel(request):
    """
    Genera y descarga un reporte en formato Excel

    GET /marketing/reportes/generar/?tipo=campaigns&account_id=123&fecha_inicio=2025-01-01&fecha_fin=2025-01-31
    """
    import pandas as pd
    from io import BytesIO

    tipo = request.GET.get('tipo', 'campaigns')
    account_id = request.GET.get('account_id')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    if not account_id or not fecha_inicio or not fecha_fin:
        return JsonResponse({
            'status': 'error',
            'message': 'Parametros incompletos'
        }, status=400)

    try:
        # Consultar datos segun tipo
        if tipo == 'campaigns':
            queryset = Campaigns.objects.filter(
                account_id=account_id,
                insights_date_start__gte=fecha_inicio,
                insights_date_start__lte=fecha_fin
            ).values(
                'campaign_id', 'campaign_name', 'account_name',
                'insights_date_start', 'insights_date_stop',
                'spend', 'impressions', 'clicks', 'reach',
                'cpm', 'cpc', 'ctr', 'campaign_status', 'campaign_objective'
            )

        elif tipo == 'adsets':
            queryset = Adsets.objects.filter(
                account_id=account_id,
                insights_date_start__gte=fecha_inicio,
                insights_date_start__lte=fecha_fin
            ).values(
                'adset_id', 'adset_name', 'account_name', 'campaign_id',
                'insights_date_start', 'insights_date_stop',
                'spend', 'impressions', 'clicks', 'reach',
                'cpm', 'cpc', 'ctr', 'adset_status', 'optimization_goal'
            )

        elif tipo == 'ads':
            queryset = Ads.objects.filter(
                account_id=account_id,
                insights_date_start__gte=fecha_inicio,
                insights_date_start__lte=fecha_fin
            ).values(
                'ad_id', 'ad_name', 'account_name', 'campaign_id', 'adset_id',
                'insights_date_start', 'insights_date_stop',
                'spend', 'impressions', 'clicks', 'reach',
                'cpm', 'cpc', 'ctr', 'ad_status'
            )

        elif tipo == 'consolidado':
            # Consolidado: campaigns + adsets + ads
            campaigns = list(Campaigns.objects.filter(
                account_id=account_id,
                insights_date_start__gte=fecha_inicio,
                insights_date_start__lte=fecha_fin
            ).values())

            adsets = list(Adsets.objects.filter(
                account_id=account_id,
                insights_date_start__gte=fecha_inicio,
                insights_date_start__lte=fecha_fin
            ).values())

            ads = list(Ads.objects.filter(
                account_id=account_id,
                insights_date_start__gte=fecha_inicio,
                insights_date_start__lte=fecha_fin
            ).values())

            # Crear Excel con multiples hojas
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Hoja resumen
                resumen_data = {
                    'Concepto': ['Total Campaigns', 'Total AdSets', 'Total Ads',
                                'Inversion Total', 'Total Impresiones', 'Total Clics'],
                    'Valor': [
                        len(set([c['campaign_id'] for c in campaigns])),
                        len(set([a['adset_id'] for a in adsets])),
                        len(set([a['ad_id'] for a in ads])),
                        f"${sum([float(c.get('spend', 0) or 0) for c in campaigns]):,.2f}",
                        sum([int(c.get('impressions', 0) or 0) for c in campaigns]),
                        sum([int(c.get('clicks', 0) or 0) for c in campaigns])
                    ]
                }
                pd.DataFrame(resumen_data).to_excel(writer, sheet_name='Resumen', index=False)

                if campaigns:
                    pd.DataFrame(campaigns).to_excel(writer, sheet_name='Campaigns', index=False)
                if adsets:
                    pd.DataFrame(adsets).to_excel(writer, sheet_name='AdSets', index=False)
                if ads:
                    pd.DataFrame(ads).to_excel(writer, sheet_name='Ads', index=False)

            output.seek(0)

            response = HttpResponse(
                output.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename=reporte_{tipo}_{fecha_inicio}_a_{fecha_fin}.xlsx'
            return response

        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Tipo de reporte no valido'
            }, status=400)

        # Convertir a lista para pandas
        data = list(queryset)

        if not data:
            return JsonResponse({
                'status': 'error',
                'message': 'No se encontraron datos para el rango especificado'
            }, status=404)

        # Crear Excel
        df = pd.DataFrame(data)

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Calcular totales
            total_spend = df['spend'].sum() if 'spend' in df.columns else 0
            total_impressions = df['impressions'].sum() if 'impressions' in df.columns else 0
            total_clicks = df['clicks'].sum() if 'clicks' in df.columns else 0

            # Hoja resumen
            resumen_data = {
                'Concepto': ['Inversion Total', 'Total Registros', 'Impresiones', 'Clics',
                            'Periodo', 'Generado'],
                'Valor': [
                    f"${total_spend:,.2f}",
                    len(df),
                    f"{total_impressions:,}",
                    f"{total_clicks:,}",
                    f"{fecha_inicio} a {fecha_fin}",
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ]
            }
            pd.DataFrame(resumen_data).to_excel(writer, sheet_name='Resumen', index=False)

            # Hoja de datos
            df.to_excel(writer, sheet_name='Datos', index=False)

        output.seek(0)

        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename=reporte_{tipo}_{fecha_inicio}_a_{fecha_fin}.xlsx'
        return response

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
