#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WEB VIEWS - AutoRepCuentas
Vistas de Django para paginas web del sistema de marketing
"""

import os
import json
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta
from decimal import Decimal
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.db.models import Sum, Count, Value
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

    try:
        # Obtener estadisticas
        total_cuentas = Accounts.objects.filter(is_active=True).count()
        total_campaigns = Campaigns.objects.values('campaign_id').distinct().count()
        total_adsets = Adsets.objects.values('adset_id').distinct().count()
        total_ads = Ads.objects.values('ad_id').distinct().count()

        # Ultimas cuentas - ordenar por account_id si account_key da problemas
        ultimas_cuentas = Accounts.objects.filter(is_active=True).order_by('account_id')[:5]

        # Resumen de inversion por cuenta (ultimos 30 dias)
        fecha_inicio = datetime.now() - timedelta(days=30)
        resumen_inversion = Campaigns.objects.filter(
            insights_date_start__gte=fecha_inicio
        ).values('account_name').annotate(
            total_spend=Coalesce(Sum('spend'), Value(Decimal('0'))),
            total_impressions=Coalesce(Sum('impressions'), Value(0))
        ).order_by('-total_spend')[:5]

    except Exception as e:
        # Si hay error, usar valores por defecto
        total_cuentas = 0
        total_campaigns = 0
        total_adsets = 0
        total_ads = 0
        ultimas_cuentas = []
        resumen_inversion = []
        print(f"Error en dashboard: {str(e)}")

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

    try:
        # Obtener cuentas de la base de datos
        cuentas_list = Accounts.objects.all().order_by('account_id')

        # Estadisticas
        total_cuentas = cuentas_list.count()
        cuentas_activas = cuentas_list.filter(is_active=True).count()
        cuentas_multimarca = cuentas_list.filter(multimarca='Si').count()
    except Exception as e:
        cuentas_list = []
        total_cuentas = 0
        cuentas_activas = 0
        cuentas_multimarca = 0
        print(f"Error en cuentas: {str(e)}")

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

    try:
        # Obtener cuentas de la base de datos
        cuentas_list = Accounts.objects.filter(is_active=True).order_by('account_id')

        # Estadisticas
        total_campaigns = Campaigns.objects.values('campaign_id').distinct().count()
        total_adsets = Adsets.objects.values('adset_id').distinct().count()
        total_ads = Ads.objects.values('ad_id').distinct().count()

        # Inversion total
        total_spend = Campaigns.objects.aggregate(
            total=Coalesce(Sum('spend'), Value(Decimal('0')))
        )['total']

        # Reportes recientes (placeholder - se puede implementar historial)
        reportes_recientes = []

    except Exception as e:
        cuentas_list = []
        total_campaigns = 0
        total_adsets = 0
        total_ads = 0
        total_spend = 0
        reportes_recientes = []
        print(f"Error en reportes: {str(e)}")

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


def format_dataframe_for_excel(df):
    """Formatea las columnas del DataFrame para Excel"""
    df = df.copy()

    # Formatear columnas de fecha a dd/mm/yyyy
    date_columns = ['insights_date_start', 'insights_date_stop']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col]).dt.strftime('%d/%m/%Y')

    # Formatear columnas de moneda con $
    money_columns = ['spend', 'cpm', 'cpc', 'budget_remaining', 'daily_budget',
                     'lifetime_budget', 'bid_amount', 'social_spend']
    for col in money_columns:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: f"${float(x or 0):,.2f}")

    # Formatear CTR como porcentaje
    pct_columns = ['ctr', 'inline_link_click_ctr', 'unique_ctr', 'unique_inline_link_click_ctr']
    for col in pct_columns:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: f"{float(x or 0):.2f}%")

    # Formatear numeros grandes con separador de miles
    number_columns = ['impressions', 'clicks', 'reach', 'inline_link_clicks',
                      'unique_clicks', 'unique_inline_link_clicks']
    for col in number_columns:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: f"{int(x or 0):,}")

    return df


def generar_reporte_excel(request):
    """
    Genera y descarga un reporte en formato Excel

    GET /marketing/reportes/generar/?tipo=campaigns&account_id=123&fecha_inicio=2025-01-01&fecha_fin=2025-01-31
    """
    tipo = request.GET.get('tipo', 'campaigns')
    account_id = request.GET.get('account_id')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    if not account_id or not fecha_inicio or not fecha_fin:
        return JsonResponse({
            'status': 'error',
            'message': 'Parametros incompletos'
        }, status=400)

    # Obtener nombre de la cuenta para el archivo
    try:
        cuenta = Accounts.objects.get(account_id=account_id)
        account_name = cuenta.account_name.replace(' ', '_').replace('/', '-')[:30]
    except Accounts.DoesNotExist:
        account_name = account_id

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
                        f"{sum([int(c.get('impressions', 0) or 0) for c in campaigns]):,}",
                        f"{sum([int(c.get('clicks', 0) or 0) for c in campaigns]):,}"
                    ]
                }
                pd.DataFrame(resumen_data).to_excel(writer, sheet_name='Resumen', index=False)

                if campaigns:
                    df_campaigns = format_dataframe_for_excel(pd.DataFrame(campaigns))
                    df_campaigns.to_excel(writer, sheet_name='Campaigns', index=False)
                if adsets:
                    df_adsets = format_dataframe_for_excel(pd.DataFrame(adsets))
                    df_adsets.to_excel(writer, sheet_name='AdSets', index=False)
                if ads:
                    df_ads = format_dataframe_for_excel(pd.DataFrame(ads))
                    df_ads.to_excel(writer, sheet_name='Ads', index=False)

            output.seek(0)

            response = HttpResponse(
                output.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            filename = f"{account_name}_{tipo}_{fecha_inicio}_a_{fecha_fin}.xlsx"
            response['Content-Disposition'] = f'attachment; filename={filename}'
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

        # Calcular totales antes de formatear
        total_spend = df['spend'].sum() if 'spend' in df.columns else 0
        total_impressions = df['impressions'].sum() if 'impressions' in df.columns else 0
        total_clicks = df['clicks'].sum() if 'clicks' in df.columns else 0

        # Formatear DataFrame
        df_formatted = format_dataframe_for_excel(df)

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
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
                    datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                ]
            }
            pd.DataFrame(resumen_data).to_excel(writer, sheet_name='Resumen', index=False)

            # Hoja de datos formateados
            df_formatted.to_excel(writer, sheet_name='Datos', index=False)

        output.seek(0)

        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        filename = f"{account_name}_{tipo}_{fecha_inicio}_a_{fecha_fin}.xlsx"
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
