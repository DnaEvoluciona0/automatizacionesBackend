#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ADSETS CONTROLLER - AutoRepCuentas
Controlador para operaciones con adsets de Meta Ads
Usa Django ORM para PostgreSQL local
"""

import os
import sys
import json
import time
import requests
from datetime import datetime, timedelta
from urllib.parse import urlencode

# Agregar el directorio raíz al path para imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from ..conexiones.connection_meta_api import MetaAPI
from ..utils.date_utils import DateManager
from ..models import Adsets, Campaigns


# --------------------------------------------------------------------------------------------------
# * Función: get_all_adsets
# * Descripción: Obtiene todos los adsets de una cuenta de Meta Ads
#
# ! Parámetros:
#   - account_data: dict - Datos de la cuenta (account_id, access_token, nombre)
#
# ? Return:
#   - Caso success: { status: 'success', adsets: [...], count: N }
#   - Caso error: { status: 'error', message: '...' }
# --------------------------------------------------------------------------------------------------
def get_all_adsets(account_data):
    """Obtiene todos los adsets de una cuenta"""
    if not account_data or not account_data.get('account_id') or not account_data.get('access_token'):
        return {
            'status': 'error',
            'message': 'Datos de cuenta incompletos'
        }

    try:
        meta_api = MetaAPI()
        api_base_url = meta_api.get_api_base_url()
        account_id = account_data['account_id']
        access_token = account_data['access_token']

        # Configuración especial para cuenta 4
        if account_id == "1027475591362843":
            adset_fields = [
                'id', 'name', 'status', 'configured_status', 'effective_status',
                'created_time', 'updated_time', 'start_time', 'end_time',
                'campaign_id', 'account_id', 'optimization_goal', 'billing_event',
                'daily_budget', 'lifetime_budget'
            ]
            page_limit = 100
        else:
            adset_fields = [
                'id', 'name', 'status', 'configured_status', 'effective_status',
                'created_time', 'updated_time', 'start_time', 'end_time',
                'campaign_id', 'account_id', 'optimization_goal', 'billing_event',
                'bid_amount', 'budget_remaining', 'daily_budget', 'lifetime_budget',
                'targeting', 'attribution_spec', 'bid_strategy', 'destination_type',
                'promoted_object', 'pacing_type', 'is_dynamic_creative'
            ]
            page_limit = 1000

        url = f"{api_base_url}/act_{account_id}/adsets"
        params = {
            'fields': ','.join(adset_fields),
            'limit': page_limit,
            'access_token': access_token
        }

        adsets_data = []

        while url:
            response = requests.get(url, params=params, timeout=30)
            data = response.json()

            if response.status_code != 200:
                error_info = data.get('error', {})
                return {
                    'status': 'error',
                    'message': f"Error de API [{error_info.get('code', 'N/A')}]: {error_info.get('message', 'Error desconocido')}"
                }

            page_adsets = data.get('data', [])
            adsets_data.extend(page_adsets)

            paging = data.get('paging', {})
            url = paging.get('next')
            params = {}

        return {
            'status': 'success',
            'adsets': adsets_data,
            'count': len(adsets_data)
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error inesperado: {str(e)}'
        }


# --------------------------------------------------------------------------------------------------
# * Función: get_adsets_insights
# * Descripción: Obtiene insights de adsets usando BATCH API
#
# ! Parámetros:
#   - account_data: dict - Datos de la cuenta
#   - adsets_data: list - Lista de adsets
#
# ? Return:
#   - Caso success: { status: 'success', insights_dict: {...}, count: N }
#   - Caso error: { status: 'error', message: '...' }
# --------------------------------------------------------------------------------------------------
def get_adsets_insights(account_data, adsets_data):
    """Obtiene insights de adsets usando BATCH API"""
    if not adsets_data:
        return {
            'status': 'error',
            'message': 'No hay adsets para extraer insights'
        }

    try:
        meta_api = MetaAPI()
        api_base_url = meta_api.get_api_base_url()
        access_token = account_data['access_token']

        # Usar sistema de fechas consistente
        date_manager = DateManager()
        date_info = date_manager.get_extraction_dates("adsets")
        date_end = date_info['date_end']

        # Campos de insights
        insight_fields = [
            'impressions', 'clicks', 'spend', 'reach', 'frequency',
            'cpm', 'cpc', 'ctr', 'inline_link_clicks', 'inline_link_click_ctr',
            'unique_clicks', 'unique_ctr', 'date_start', 'date_stop'
        ]

        # Filtrar adsets válidos
        valid_adsets = []
        api_limits = date_manager.get_meta_api_date_limits()
        min_allowed_str = api_limits['min_date']

        for adset_data in adsets_data:
            start_time = adset_data.get('start_time', '')
            is_valid, message = date_manager.validate_campaign_date(start_time, date_end)

            if is_valid and start_time:
                try:
                    adset_datetime = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    adset_date = adset_datetime.strftime('%Y-%m-%d')

                    if adset_date < min_allowed_str:
                        adjusted_start_date = min_allowed_str
                    else:
                        adjusted_start_date = adset_date

                    valid_adsets.append({
                        'data': adset_data,
                        'start_date': adjusted_start_date
                    })
                except Exception:
                    continue

        if not valid_adsets:
            return {
                'status': 'error',
                'message': 'No hay adsets válidos para extraer insights'
            }

        # Procesar en lotes de 50
        insights_data = {}
        batch_size = 50

        for i in range(0, len(valid_adsets), batch_size):
            batch_adsets = valid_adsets[i:i+batch_size]

            # Construir requests para el batch
            batch_requests = []
            for adset_info in batch_adsets:
                adset_data = adset_info['data']
                start_date = adset_info['start_date']
                adset_id = adset_data['id']

                time_range = json.dumps({
                    "since": start_date,
                    "until": date_end
                })

                relative_url = f"{adset_id}/insights"
                params = {
                    'fields': ','.join(insight_fields),
                    'time_range': time_range,
                    'level': 'adset',
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

                if response.status_code == 200:
                    batch_responses = response.json()

                    for idx, batch_response in enumerate(batch_responses):
                        if idx >= len(batch_adsets):
                            break

                        adset_info = batch_adsets[idx]
                        adset_id = adset_info['data']['id']

                        if batch_response and 'error' not in batch_response:
                            response_code = batch_response.get('code', 200)
                            if response_code == 200:
                                try:
                                    body_str = batch_response.get('body', '{}')
                                    body_data = json.loads(body_str)

                                    if 'data' in body_data:
                                        insights_data[adset_id] = body_data['data']
                                except json.JSONDecodeError:
                                    continue

                time.sleep(2)

            except Exception:
                continue

        total_insights = sum(len(v) if isinstance(v, list) else 0 for v in insights_data.values())

        return {
            'status': 'success',
            'insights_dict': insights_data,
            'count': total_insights
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error extrayendo insights: {str(e)}'
        }


# --------------------------------------------------------------------------------------------------
# * Función: sync_adsets_to_supabase
# * Descripción: Sincroniza adsets e insights con PostgreSQL usando Django ORM
#
# ! Parámetros:
#   - adsets_data: list - Lista de adsets
#   - insights_dict: dict - Diccionario de insights por adset_id
#   - account_data: dict - Datos de la cuenta
#
# ? Return:
#   - { status: 'success', inserted: N, updated: N, skipped: N, errors: N }
#   - { status: 'error', message: '...' }
# --------------------------------------------------------------------------------------------------
def sync_adsets_to_supabase(adsets_data, insights_dict, account_data):
    """Sincroniza adsets e insights con PostgreSQL usando Django ORM"""
    if not adsets_data or not insights_dict:
        return {
            'status': 'error',
            'message': 'No hay datos para sincronizar'
        }

    try:
        account_id = account_data.get('account_id')
        stats = {'insertados': 0, 'actualizados': 0, 'saltados': 0, 'errores': 0}

        # Combinar adsets con insights
        for adset in adsets_data:
            adset_id = adset.get('id')
            insights_list = insights_dict.get(adset_id, [])

            if not insights_list:
                stats['saltados'] += 1
                continue

            # Crear un registro por cada día de insights
            for daily_insight in insights_list:
                try:
                    insights_date_start = daily_insight.get('date_start')
                    campaign_id = adset.get('campaign_id')

                    if not adset_id or not insights_date_start:
                        stats['errores'] += 1
                        continue

                    # Preparar datos para el registro
                    record_data = {
                        'account_id': account_id,
                        'account_name': account_data.get('nombre'),
                        'adset_name': adset.get('name'),
                        'adset_status': adset.get('status'),
                        'configured_status': adset.get('configured_status'),
                        'effective_status': adset.get('effective_status'),
                        'campaign_id': campaign_id,
                        'optimization_goal': adset.get('optimization_goal'),
                        'billing_event': adset.get('billing_event'),
                        'bid_amount': float(adset.get('bid_amount', 0)) if adset.get('bid_amount') else 0.0,
                        'budget_remaining': float(adset.get('budget_remaining', 0)) if adset.get('budget_remaining') else 0.0,
                        'daily_budget': float(adset.get('daily_budget', 0)) if adset.get('daily_budget') else 0.0,
                        'lifetime_budget': float(adset.get('lifetime_budget', 0)) if adset.get('lifetime_budget') else 0.0,
                        'bid_strategy': adset.get('bid_strategy'),
                        'destination_type': adset.get('destination_type'),
                        'pacing_type': adset.get('pacing_type'),
                        'is_dynamic_creative': adset.get('is_dynamic_creative', False),
                        'targeting': json.dumps(adset.get('targeting', {})) if adset.get('targeting') else None,
                        'attribution_spec': json.dumps(adset.get('attribution_spec', [])) if adset.get('attribution_spec') else None,
                        'promoted_object': json.dumps(adset.get('promoted_object', {})) if adset.get('promoted_object') else None,
                        'extraction_date': datetime.now(),
                        'data_source': 'AUTOREPCUENTAS_CONTROLLER',
                        'insights_date_stop': daily_insight.get('date_stop'),
                        'impressions': int(daily_insight.get('impressions', 0)) if daily_insight.get('impressions') else 0,
                        'clicks': int(daily_insight.get('clicks', 0)) if daily_insight.get('clicks') else 0,
                        'spend': float(daily_insight.get('spend', 0)) if daily_insight.get('spend') else 0.0,
                        'reach': int(daily_insight.get('reach', 0)) if daily_insight.get('reach') else 0,
                        'frequency': float(daily_insight.get('frequency', 0)) if daily_insight.get('frequency') else 0.0,
                        'cpm': float(daily_insight.get('cpm', 0)) if daily_insight.get('cpm') else 0.0,
                        'cpc': float(daily_insight.get('cpc', 0)) if daily_insight.get('cpc') else 0.0,
                        'ctr': float(daily_insight.get('ctr', 0)) if daily_insight.get('ctr') else 0.0,
                        'inline_link_clicks': int(daily_insight.get('inline_link_clicks', 0)) if daily_insight.get('inline_link_clicks') else 0,
                        'inline_link_click_ctr': float(daily_insight.get('inline_link_click_ctr', 0)) if daily_insight.get('inline_link_click_ctr') else 0.0,
                        'unique_clicks': int(daily_insight.get('unique_clicks', 0)) if daily_insight.get('unique_clicks') else 0,
                        'unique_ctr': float(daily_insight.get('unique_ctr', 0)) if daily_insight.get('unique_ctr') else 0.0,
                        'updated_at': datetime.now()
                    }

                    # Parsear fechas del adset
                    if adset.get('created_time'):
                        try:
                            record_data['adset_created_time'] = datetime.fromisoformat(
                                adset['created_time'].replace('Z', '+00:00')
                            )
                        except:
                            pass

                    if adset.get('updated_time'):
                        try:
                            record_data['adset_updated_time'] = datetime.fromisoformat(
                                adset['updated_time'].replace('Z', '+00:00')
                            )
                        except:
                            pass

                    if adset.get('start_time'):
                        try:
                            record_data['adset_start_time'] = datetime.fromisoformat(
                                adset['start_time'].replace('Z', '+00:00')
                            )
                        except:
                            pass

                    if adset.get('end_time'):
                        try:
                            record_data['adset_end_time'] = datetime.fromisoformat(
                                adset['end_time'].replace('Z', '+00:00')
                            )
                        except:
                            pass

                    # Verificar si existe con PRIMARY KEY compuesta usando Django ORM
                    try:
                        existing = Adsets.objects.get(
                            adset_id=adset_id,
                            insights_date_start=insights_date_start
                        )
                        # Existe, actualizar
                        for key, value in record_data.items():
                            setattr(existing, key, value)
                        existing.save()
                        stats['actualizados'] += 1

                    except Adsets.DoesNotExist:
                        # No existe, crear nuevo
                        Adsets.objects.create(
                            adset_id=adset_id,
                            insights_date_start=insights_date_start,
                            **record_data
                        )
                        stats['insertados'] += 1

                except Exception as e:
                    print(f"Error procesando adset {adset_id}: {str(e)}")
                    stats['errores'] += 1

        return {
            'status': 'success',
            'inserted': stats['insertados'],
            'updated': stats['actualizados'],
            'skipped': stats['saltados'],
            'errors': stats['errores']
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error sincronizando con PostgreSQL: {str(e)}'
        }
