#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API VIEWS - AutoRepCuentas
Views de Django para endpoints HTTP de Meta Ads
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from ..controllers import accounts_controller, campaigns_controller, adsets_controller, ads_controller
from ..conexiones.connection_meta_api import MetaAPI


# =====================================
# ACCOUNTS ENDPOINTS
# =====================================

@require_http_methods(["GET"])
def sync_accounts(request):
    """
    Sincroniza todas las cuentas del config.json con Supabase

    GET /auto/marketing/accounts/sync/
    """
    try:
        result = accounts_controller.sync_accounts_to_supabase()
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error en sync_accounts: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
def list_accounts(request):
    """
    Lista todas las cuentas configuradas

    GET /auto/marketing/accounts/list/
    """
    try:
        result = accounts_controller.get_all_accounts()
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error en list_accounts: {str(e)}'
        }, status=500)


# =====================================
# CAMPAIGNS ENDPOINTS
# =====================================

@require_http_methods(["GET"])
def extract_campaigns(request):
    """
    Extrae campañas de Meta API para una cuenta específica

    GET /auto/marketing/campaigns/extract/?account_key=1

    Parámetros:
        - account_key: Número de cuenta del config.json (requerido)
    """
    try:
        account_key = request.GET.get('account_key')

        if not account_key:
            return JsonResponse({
                'status': 'error',
                'message': 'Parámetro account_key es requerido'
            }, status=400)

        # Obtener datos de la cuenta
        meta_api = MetaAPI()
        account_data = meta_api.get_account_config(account_key)

        if not account_data:
            return JsonResponse({
                'status': 'error',
                'message': f'Cuenta {account_key} no encontrada'
            }, status=404)

        # Extraer campañas
        result = campaigns_controller.get_all_campaigns(account_data)
        return JsonResponse(result)

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error en extract_campaigns: {str(e)}'
        }, status=500)


@require_http_methods(["POST"])
def sync_campaigns(request):
    """
    Sincroniza campañas e insights con Supabase

    POST /auto/marketing/campaigns/sync/?account_key=1

    Parámetros:
        - account_key: Número de cuenta (requerido)

    Proceso:
        1. Extrae campañas de Meta API
        2. Extrae insights de las campañas
        3. Sincroniza todo con Supabase
    """
    try:
        account_key = request.GET.get('account_key')

        if not account_key:
            return JsonResponse({
                'status': 'error',
                'message': 'Parámetro account_key es requerido'
            }, status=400)

        # Obtener datos de la cuenta
        meta_api = MetaAPI()
        account_data = meta_api.get_account_config(account_key)

        if not account_data:
            return JsonResponse({
                'status': 'error',
                'message': f'Cuenta {account_key} no encontrada'
            }, status=404)

        # 1. Extraer campañas
        campaigns_result = campaigns_controller.get_all_campaigns(account_data)
        if campaigns_result['status'] != 'success':
            return JsonResponse(campaigns_result, status=500)

        campaigns_data = campaigns_result['campaigns']

        # 2. Extraer insights
        insights_result = campaigns_controller.get_campaigns_insights(account_data, campaigns_data)
        if insights_result['status'] != 'success':
            return JsonResponse(insights_result, status=500)

        insights_data = insights_result['insights']

        # 3. Sincronizar con Supabase
        sync_result = campaigns_controller.sync_campaigns_to_supabase(
            campaigns_data, insights_data, account_data
        )

        return JsonResponse(sync_result)

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error en sync_campaigns: {str(e)}'
        }, status=500)


# =====================================
# ADSETS ENDPOINTS
# =====================================

@require_http_methods(["GET"])
def extract_adsets(request):
    """
    Extrae adsets de Meta API para una cuenta específica

    GET /auto/marketing/adsets/extract/?account_key=1
    """
    try:
        account_key = request.GET.get('account_key')

        if not account_key:
            return JsonResponse({
                'status': 'error',
                'message': 'Parámetro account_key es requerido'
            }, status=400)

        meta_api = MetaAPI()
        account_data = meta_api.get_account_config(account_key)

        if not account_data:
            return JsonResponse({
                'status': 'error',
                'message': f'Cuenta {account_key} no encontrada'
            }, status=404)

        result = adsets_controller.get_all_adsets(account_data)
        return JsonResponse(result)

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error en extract_adsets: {str(e)}'
        }, status=500)


@require_http_methods(["POST"])
def sync_adsets(request):
    """
    Sincroniza adsets e insights con Supabase

    POST /auto/marketing/adsets/sync/?account_key=1
    """
    try:
        account_key = request.GET.get('account_key')

        if not account_key:
            return JsonResponse({
                'status': 'error',
                'message': 'Parámetro account_key es requerido'
            }, status=400)

        meta_api = MetaAPI()
        account_data = meta_api.get_account_config(account_key)

        if not account_data:
            return JsonResponse({
                'status': 'error',
                'message': f'Cuenta {account_key} no encontrada'
            }, status=404)

        # 1. Extraer adsets
        adsets_result = adsets_controller.get_all_adsets(account_data)
        if adsets_result['status'] != 'success':
            return JsonResponse(adsets_result, status=500)

        adsets_data = adsets_result['adsets']

        # 2. Extraer insights
        insights_result = adsets_controller.get_adsets_insights(account_data, adsets_data)
        if insights_result['status'] != 'success':
            return JsonResponse(insights_result, status=500)

        insights_dict = insights_result['insights']

        # 3. Sincronizar con Supabase
        sync_result = adsets_controller.sync_adsets_to_supabase(
            adsets_data, insights_dict, account_data
        )

        return JsonResponse(sync_result)

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error en sync_adsets: {str(e)}'
        }, status=500)


# =====================================
# ADS ENDPOINTS
# =====================================

@require_http_methods(["GET"])
def extract_ads(request):
    """
    Extrae ads de Meta API para una cuenta específica

    GET /auto/marketing/ads/extract/?account_key=1
    """
    try:
        account_key = request.GET.get('account_key')

        if not account_key:
            return JsonResponse({
                'status': 'error',
                'message': 'Parámetro account_key es requerido'
            }, status=400)

        meta_api = MetaAPI()
        account_data = meta_api.get_account_config(account_key)

        if not account_data:
            return JsonResponse({
                'status': 'error',
                'message': f'Cuenta {account_key} no encontrada'
            }, status=404)

        result = ads_controller.get_all_ads(account_data)
        return JsonResponse(result)

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error en extract_ads: {str(e)}'
        }, status=500)


@require_http_methods(["POST"])
def sync_ads(request):
    """
    Sincroniza ads e insights con Supabase

    POST /auto/marketing/ads/sync/?account_key=1
    """
    try:
        account_key = request.GET.get('account_key')

        if not account_key:
            return JsonResponse({
                'status': 'error',
                'message': 'Parámetro account_key es requerido'
            }, status=400)

        meta_api = MetaAPI()
        account_data = meta_api.get_account_config(account_key)

        if not account_data:
            return JsonResponse({
                'status': 'error',
                'message': f'Cuenta {account_key} no encontrada'
            }, status=404)

        # 1. Extraer ads
        ads_result = ads_controller.get_all_ads(account_data)
        if ads_result['status'] != 'success':
            return JsonResponse(ads_result, status=500)

        ads_data = ads_result['ads']

        # 2. Extraer insights
        insights_result = ads_controller.get_ads_insights(account_data, ads_data)
        if insights_result['status'] != 'success':
            return JsonResponse(insights_result, status=500)

        insights_dict = insights_result['insights']

        # 3. Sincronizar con Supabase (si tienes la función en ads_controller)
        # sync_result = ads_controller.sync_ads_to_supabase(ads_data, insights_dict, account_data)

        # Por ahora retornamos los datos extraídos
        return JsonResponse({
            'status': 'success',
            'message': 'Ads e insights extraídos correctamente',
            'ads_count': len(ads_data),
            'insights_count': len(insights_dict)
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error en sync_ads: {str(e)}'
        }, status=500)
