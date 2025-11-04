#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CAMPAIGNS CONTROLLER - LEO MASTER
Controlador para operaciones con campañas de Meta Ads
"""

import os
import sys
import json
import time
import requests
import hashlib
from datetime import datetime, timedelta
from urllib.parse import urlencode

# Agregar el directorio raíz al path para imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from ..conexiones.connection_supabase import SupabaseAPI
from ..conexiones.connection_meta_api import MetaAPI
from ..utils.date_utils import DateManager


# --------------------------------------------------------------------------------------------------
# * Función: get_all_campaigns
# * Descripción: Obtiene todas las campañas de una cuenta de Meta Ads
#
# ! Parámetros:
#   - account_data: dict - Datos de la cuenta (account_id, access_token, nombre)
#
# ? Condiciones:
#   1. account_data debe contener account_id y access_token válidos
#
# ? Return:
#   - Caso success:
#       Retorna un JSON con el status success y una lista de campañas
#       { status: 'success', campaigns: [...], count: N }
#   - Caso error:
#       Retorna un JSON con status error y el mensaje del error
#       { status: 'error', message: '...' }
# --------------------------------------------------------------------------------------------------
def get_all_campaigns(account_data):
    """Obtiene todas las campañas de una cuenta"""
    if not account_data or not account_data.get('account_id') or not account_data.get('access_token'):
        return {
            'status': 'error',
            'message': 'Datos de cuenta incompletos (account_id o access_token faltante)'
        }

    try:
        meta_api = MetaAPI()
        api_base_url = meta_api.get_api_base_url()
        account_id = account_data['account_id']
        access_token = account_data['access_token']

        # Campos optimizados para campañas
        campaign_fields = [
            'id', 'name', 'status', 'objective', 'created_time', 'updated_time',
            'start_time', 'stop_time', 'budget_remaining', 'buying_type',
            'configured_status', 'effective_status', 'account_id', 'bid_strategy',
            'budget_rebalance_flag', 'is_skadnetwork_attribution', 'smart_promotion_type',
            'can_create_brand_lift_study', 'special_ad_category', 'can_use_spend_cap',
            'optimization_goal'
        ]

        # URL para obtener campañas
        url = f"{api_base_url}/act_{account_id}/campaigns"
        params = {
            'access_token': access_token,
            'fields': ','.join(campaign_fields),
            'limit': 500,
            'filtering': '[{"field":"effective_status","operator":"IN","value":["ACTIVE","PAUSED","PENDING_REVIEW","DISAPPROVED","PENDING_BILLING_INFO","CAMPAIGN_PAUSED","ADSET_PAUSED","IN_PROCESS","WITH_ISSUES"]}]'
        }

        campaigns_data = []

        # Manejar paginación
        while url:
            response = requests.get(url, params=params, timeout=30)
            data = response.json()

            if response.status_code != 200:
                error_info = data.get('error', {})
                error_code = error_info.get('code', 'N/A')
                error_message = error_info.get('message', 'Error desconocido')

                return {
                    'status': 'error',
                    'message': f'Error de API [{error_code}]: {error_message}',
                    'error_code': error_code
                }

            # Agregar campañas de esta página
            page_campaigns = data.get('data', [])
            campaigns_data.extend(page_campaigns)

            # Verificar si hay más páginas
            paging = data.get('paging', {})
            url = paging.get('next')
            params = {}  # Los parámetros ya están en la URL next

        return {
            'status': 'success',
            'campaigns': campaigns_data,
            'count': len(campaigns_data)
        }

    except requests.exceptions.RequestException as e:
        return {
            'status': 'error',
            'message': f'Error de conexión con Meta API: {str(e)}'
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error inesperado: {str(e)}'
        }


# --------------------------------------------------------------------------------------------------
# * Función: get_campaigns_insights
# * Descripción: Obtiene insights de campañas usando BATCH API
#
# ! Parámetros:
#   - account_data: dict - Datos de la cuenta
#   - campaigns_data: list - Lista de campañas
#
# ? Condiciones:
#   1. campaigns_data debe contener al menos una campaña válida
#   2. Las campañas deben tener fechas válidas según Meta API
#
# ? Return:
#   - Caso success:
#       { status: 'success', insights: [...], count: N }
#   - Caso error:
#       { status: 'error', message: '...' }
# --------------------------------------------------------------------------------------------------
def get_campaigns_insights(account_data, campaigns_data):
    """Obtiene insights de campañas usando BATCH API"""
    if not campaigns_data:
        return {
            'status': 'error',
            'message': 'No hay campañas para extraer insights'
        }

    try:
        meta_api = MetaAPI()
        api_base_url = meta_api.get_api_base_url()
        access_token = account_data['access_token']

        # Usar sistema de fechas consistente
        date_manager = DateManager()
        date_info = date_manager.get_extraction_dates("campaigns")
        date_end = date_info['date_end']

        # Campos de insights
        insights_fields = [
            'account_id', 'account_name', 'campaign_id', 'campaign_name',
            'date_start', 'date_stop', 'impressions', 'clicks', 'spend',
            'reach', 'frequency', 'cpm', 'cpc', 'ctr', 'inline_link_clicks',
            'inline_link_click_ctr', 'objective', 'buying_type',
            'optimization_goal', 'unique_clicks', 'unique_ctr'
        ]

        # Filtrar campañas válidas
        valid_campaigns = []
        api_limits = date_manager.get_meta_api_date_limits()
        min_allowed_str = api_limits['min_date']

        for campaign_data in campaigns_data:
            start_time = campaign_data.get('start_time', '')
            is_valid, message = date_manager.validate_campaign_date(start_time, date_end)

            if is_valid:
                if start_time:
                    try:
                        campaign_datetime = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                        campaign_date = campaign_datetime.strftime('%Y-%m-%d')

                        # Ajustar si es muy antigua
                        if campaign_date < min_allowed_str:
                            adjusted_start_date = min_allowed_str
                        else:
                            adjusted_start_date = campaign_date

                        valid_campaigns.append({
                            'data': campaign_data,
                            'start_date': adjusted_start_date
                        })
                    except Exception:
                        continue
                else:
                    # Campaña sin fecha, usar rango conservador
                    conservative_start = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                    valid_campaigns.append({
                        'data': campaign_data,
                        'start_date': conservative_start
                    })

        if not valid_campaigns:
            return {
                'status': 'error',
                'message': 'No hay campañas válidas para extraer insights'
            }

        # Procesar en lotes de 50
        insights_data = []
        batch_size = 50

        for i in range(0, len(valid_campaigns), batch_size):
            batch_campaigns = valid_campaigns[i:i+batch_size]

            # Construir requests para el batch
            batch_requests = []
            for campaign_info in batch_campaigns:
                campaign_data = campaign_info['data']
                start_date = campaign_info['start_date']
                campaign_id = campaign_data['id']

                time_range = json.dumps({
                    "since": start_date,
                    "until": date_end
                })

                relative_url = f"{campaign_id}/insights"
                params = {
                    'fields': ','.join(insights_fields),
                    'time_range': time_range,
                    'level': 'campaign',
                    'time_increment': 1,
                    'limit': 5000
                }

                query_string = urlencode(params)
                relative_url_with_params = f"{relative_url}?{query_string}"

                batch_requests.append({
                    "method": "GET",
                    "relative_url": relative_url_with_params
                })

            # Enviar batch request
            batch_url = api_base_url
            batch_data = {
                'access_token': access_token,
                'batch': json.dumps(batch_requests)
            }

            try:
                response = requests.post(batch_url, data=batch_data, timeout=60)

                if response.status_code != 200:
                    continue

                batch_responses = response.json()

                # Procesar respuestas del batch
                for idx, batch_response in enumerate(batch_responses):
                    if batch_response is None:
                        continue

                    if 'error' in batch_response:
                        continue

                    response_code = batch_response.get('code', 200)
                    if response_code != 200:
                        continue

                    # Parsear body de la respuesta
                    try:
                        body_str = batch_response.get('body', '{}')
                        body_data = json.loads(body_str)

                        if 'data' in body_data:
                            campaign_insights = body_data['data']
                            insights_data.extend(campaign_insights)

                    except json.JSONDecodeError:
                        continue

                # Pausa entre lotes
                time.sleep(2)

            except Exception:
                continue

        return {
            'status': 'success',
            'insights': insights_data,
            'count': len(insights_data)
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error extrayendo insights: {str(e)}'
        }


# --------------------------------------------------------------------------------------------------
# * Función: sync_campaigns_to_supabase
# * Descripción: Sincroniza campañas e insights con Supabase
#
# ! Parámetros:
#   - campaigns_data: list - Lista de campañas
#   - insights_data: list - Lista de insights
#   - account_data: dict - Datos de la cuenta
#
# ? Return:
#   - { status: 'success', inserted: N, updated: N, errors: N }
#   - { status: 'error', message: '...' }
# --------------------------------------------------------------------------------------------------
def sync_campaigns_to_supabase(campaigns_data, insights_data, account_data):
    """Sincroniza campañas e insights con Supabase"""
    if not campaigns_data or not insights_data:
        return {
            'status': 'error',
            'message': 'No hay datos para sincronizar'
        }

    try:
        supabase_api = SupabaseAPI()
        supabase = supabase_api.get_client()

        # Combinar campaigns con insights
        campaigns_dict = {camp['id']: camp for camp in campaigns_data}
        combined_records = []

        for insight in insights_data:
            campaign_id = insight.get('campaign_id')
            campaign_data = campaigns_dict.get(campaign_id, {})

            combined_record = {
                'account_id': insight.get('account_id'),
                'account_name': insight.get('account_name'),
                'campaign_id': campaign_id,
                'campaign_name': insight.get('campaign_name') or campaign_data.get('name'),
                'campaign_status': campaign_data.get('status'),
                'campaign_objective': insight.get('objective') or campaign_data.get('objective'),
                'campaign_created_time': campaign_data.get('created_time'),
                'campaign_updated_time': campaign_data.get('updated_time'),
                'campaign_start_time': campaign_data.get('start_time'),
                'campaign_stop_time': campaign_data.get('stop_time'),
                'buying_type': insight.get('buying_type') or campaign_data.get('buying_type'),
                'bid_strategy': campaign_data.get('bid_strategy'),
                'budget_remaining': float(campaign_data.get('budget_remaining', 0)) if campaign_data.get('budget_remaining') else 0.0,
                'configured_status': campaign_data.get('configured_status'),
                'effective_status': campaign_data.get('effective_status'),
                'special_ad_category': campaign_data.get('special_ad_category'),
                'can_use_spend_cap': campaign_data.get('can_use_spend_cap'),
                'budget_rebalance_flag': campaign_data.get('budget_rebalance_flag'),
                'is_skadnetwork_attribution': campaign_data.get('is_skadnetwork_attribution'),
                'smart_promotion_type': campaign_data.get('smart_promotion_type'),
                'can_create_brand_lift_study': campaign_data.get('can_create_brand_lift_study'),
                'insights_date_start': insight.get('date_start'),
                'insights_date_stop': insight.get('date_stop'),
                'impressions': int(insight.get('impressions', 0)) if insight.get('impressions') else 0,
                'clicks': int(insight.get('clicks', 0)) if insight.get('clicks') else 0,
                'spend': float(insight.get('spend', 0)) if insight.get('spend') else 0.0,
                'reach': int(insight.get('reach', 0)) if insight.get('reach') else 0,
                'frequency': float(insight.get('frequency', 0)) if insight.get('frequency') else 0.0,
                'cpm': float(insight.get('cpm', 0)) if insight.get('cpm') else 0.0,
                'cpc': float(insight.get('cpc', 0)) if insight.get('cpc') else 0.0,
                'ctr': float(insight.get('ctr', 0)) if insight.get('ctr') else 0.0,
                'inline_link_clicks': int(insight.get('inline_link_clicks', 0)) if insight.get('inline_link_clicks') else 0,
                'inline_link_click_ctr': float(insight.get('inline_link_click_ctr', 0)) if insight.get('inline_link_click_ctr') else 0.0,
                'unique_clicks': int(insight.get('unique_clicks', 0)) if insight.get('unique_clicks') else 0,
                'unique_ctr': float(insight.get('unique_ctr', 0)) if insight.get('unique_ctr') else 0.0,
                'optimization_goal': insight.get('optimization_goal'),
                'extraction_date': datetime.now().isoformat(),
                'data_source': 'LEO_MASTER_CONTROLLER'
            }

            combined_records.append(combined_record)

        # Sincronizar con Supabase
        stats = {'insertados': 0, 'actualizados': 0, 'sin_cambios': 0, 'errores': 0}

        for record in combined_records:
            try:
                campaign_id = record['campaign_id']
                insights_date_start = record['insights_date_start']

                # Verificar si existe con PRIMARY KEY compuesta
                existing = supabase.table('campaigns').select('*').eq(
                    'campaign_id', campaign_id
                ).eq(
                    'insights_date_start', insights_date_start
                ).execute()

                if not existing.data:
                    # No existe, insertar
                    supabase.table('campaigns').insert(record).execute()
                    stats['insertados'] += 1
                else:
                    # Existe, actualizar
                    record['updated_at'] = datetime.now().isoformat()
                    supabase.table('campaigns').update(record).eq(
                        'campaign_id', campaign_id
                    ).eq(
                        'insights_date_start', insights_date_start
                    ).execute()
                    stats['actualizados'] += 1

            except Exception:
                stats['errores'] += 1

        return {
            'status': 'success',
            'inserted': stats['insertados'],
            'updated': stats['actualizados'],
            'errors': stats['errores']
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error sincronizando con Supabase: {str(e)}'
        }
