#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ADS CONTROLLER - AutoRepCuentas
Controlador para operaciones con ads de Meta Ads
Usa Django ORM para PostgreSQL local
"""

import os
import sys
import json
import time
import requests
from datetime import datetime, timedelta
from urllib.parse import urlencode

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from ..conexiones.connection_meta_api import MetaAPI
from ..utils.date_utils import DateManager
from ..models import Ads


# --------------------------------------------------------------------------------------------------
# * Función: get_all_ads
# * Descripción: Obtiene todos los ads de una cuenta de Meta Ads
#
# ! Parámetros:
#   - account_data: dict - Datos de la cuenta
#
# ? Return:
#   - Caso success: { status: 'success', ads: [...], count: N }
#   - Caso error: { status: 'error', message: '...' }
# --------------------------------------------------------------------------------------------------
def get_all_ads(account_data):
    """Obtiene todos los ads de una cuenta"""
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
            ad_fields = [
                'id', 'name', 'status', 'configured_status', 'effective_status',
                'created_time', 'updated_time', 'adset_id', 'campaign_id', 'account_id'
            ]
            page_limit = 500
        else:
            ad_fields = [
                'id', 'name', 'status', 'configured_status', 'effective_status',
                'created_time', 'updated_time', 'adset_id', 'campaign_id', 'account_id',
                'creative', 'tracking_specs', 'conversion_specs', 'bid_amount',
                'last_updated_by_app_id', 'source_ad_id'
            ]
            page_limit = 1000

        url = f"{api_base_url}/act_{account_id}/ads"
        params = {
            'fields': ','.join(ad_fields),
            'limit': page_limit,
            'access_token': access_token
        }

        ads_data = []

        while url:
            response = requests.get(url, params=params, timeout=30)
            data = response.json()

            if response.status_code != 200:
                error_info = data.get('error', {})
                return {
                    'status': 'error',
                    'message': f"Error de API: {error_info.get('message', 'Error desconocido')}"
                }

            page_ads = data.get('data', [])
            ads_data.extend(page_ads)

            paging = data.get('paging', {})
            url = paging.get('next')
            params = {}

        return {
            'status': 'success',
            'ads': ads_data,
            'count': len(ads_data)
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error inesperado: {str(e)}'
        }


# --------------------------------------------------------------------------------------------------
# * Función: get_ads_insights
# * Descripción: Obtiene insights de ads usando BATCH API
#
# ! Parámetros:
#   - account_data: dict - Datos de la cuenta
#   - ads_data: list - Lista de ads
#
# ? Return:
#   - Caso success: { status: 'success', insights: {...}, count: N }
#   - Caso error: { status: 'error', message: '...' }
# --------------------------------------------------------------------------------------------------
def get_ads_insights(account_data, ads_data):
    """Obtiene insights de ads usando BATCH API"""
    if not ads_data:
        return {
            'status': 'error',
            'message': 'No hay ads para extraer insights'
        }

    try:
        meta_api = MetaAPI()
        api_base_url = meta_api.get_api_base_url()
        access_token = account_data['access_token']

        # Usar sistema de fechas consistente
        date_manager = DateManager()
        date_info = date_manager.get_extraction_dates("ads")
        date_end = date_info['date_end']

        # Campos de insights
        insight_fields = [
            'impressions', 'clicks', 'spend', 'reach', 'frequency',
            'cpm', 'cpc', 'ctr', 'inline_link_clicks', 'inline_link_click_ctr',
            'unique_clicks', 'unique_ctr', 'unique_inline_link_clicks',
            'unique_inline_link_click_ctr', 'social_spend',
            'date_start', 'date_stop'
        ]

        # Filtrar ads válidos
        valid_ads = []
        api_limits = date_manager.get_meta_api_date_limits()
        min_allowed_str = api_limits['min_date']

        for ad_data in ads_data:
            created_time = ad_data.get('created_time', '')

            if created_time:
                try:
                    ad_datetime = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
                    ad_date = ad_datetime.strftime('%Y-%m-%d')

                    if ad_date < min_allowed_str:
                        adjusted_start_date = min_allowed_str
                    else:
                        adjusted_start_date = ad_date

                    valid_ads.append({
                        'data': ad_data,
                        'start_date': adjusted_start_date
                    })
                except Exception:
                    # Si hay error con la fecha, usar rango conservador
                    conservative_start = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                    valid_ads.append({
                        'data': ad_data,
                        'start_date': conservative_start
                    })
            else:
                # Ad sin fecha, usar rango conservador
                conservative_start = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                valid_ads.append({
                    'data': ad_data,
                    'start_date': conservative_start
                })

        if not valid_ads:
            return {
                'status': 'error',
                'message': 'No hay ads válidos para extraer insights'
            }

        # Procesar en lotes de 50
        insights_data = {}
        batch_size = 50

        for i in range(0, len(valid_ads), batch_size):
            batch_ads = valid_ads[i:i+batch_size]

            # Construir requests para el batch
            batch_requests = []
            for ad_info in batch_ads:
                ad_data = ad_info['data']
                start_date = ad_info['start_date']
                ad_id = ad_data['id']

                time_range = json.dumps({
                    "since": start_date,
                    "until": date_end
                })

                relative_url = f"{ad_id}/insights"
                params = {
                    'fields': ','.join(insight_fields),
                    'time_range': time_range,
                    'level': 'ad',
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
                        if idx >= len(batch_ads):
                            break

                        ad_info = batch_ads[idx]
                        ad_id = ad_info['data']['id']

                        if batch_response and 'error' not in batch_response:
                            response_code = batch_response.get('code', 200)
                            if response_code == 200:
                                try:
                                    body_str = batch_response.get('body', '{}')
                                    body_data = json.loads(body_str)

                                    if 'data' in body_data:
                                        insights_data[ad_id] = body_data['data']
                                except json.JSONDecodeError:
                                    continue

                time.sleep(2)

            except Exception:
                continue

        total_insights = sum(len(v) if isinstance(v, list) else 0 for v in insights_data.values())

        return {
            'status': 'success',
            'insights': insights_data,
            'count': total_insights
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error extrayendo insights: {str(e)}'
        }


# --------------------------------------------------------------------------------------------------
# * Función: sync_ads_to_supabase
# * Descripción: Sincroniza ads e insights con PostgreSQL usando Django ORM
#
# ! Parámetros:
#   - ads_data: list - Lista de ads
#   - insights_dict: dict - Diccionario de insights por ad_id
#   - account_data: dict - Datos de la cuenta
#
# ? Return:
#   - { status: 'success', inserted: N, updated: N, skipped: N, errors: N }
#   - { status: 'error', message: '...' }
# --------------------------------------------------------------------------------------------------
def sync_ads_to_supabase(ads_data, insights_dict, account_data):
    """Sincroniza ads e insights con PostgreSQL usando Django ORM"""
    if not ads_data or not insights_dict:
        return {
            'status': 'error',
            'message': 'No hay datos para sincronizar'
        }

    try:
        account_id = account_data.get('account_id')
        stats = {'insertados': 0, 'actualizados': 0, 'saltados': 0, 'errores': 0}

        # Combinar ads con insights
        for ad in ads_data:
            ad_id = ad.get('id')
            insights_list = insights_dict.get(ad_id, [])

            if not insights_list:
                stats['saltados'] += 1
                continue

            # Crear un registro por cada día de insights
            for daily_insight in insights_list:
                try:
                    insights_date_start = daily_insight.get('date_start')
                    adset_id = ad.get('adset_id')
                    campaign_id = ad.get('campaign_id')

                    if not ad_id or not insights_date_start:
                        stats['errores'] += 1
                        continue

                    # Preparar datos para el registro
                    record_data = {
                        'account_id': account_id,
                        'account_name': account_data.get('nombre'),
                        'adset_id': adset_id,
                        'campaign_id': campaign_id,
                        'ad_name': ad.get('name'),
                        'ad_status': ad.get('status'),
                        'configured_status': ad.get('configured_status'),
                        'effective_status': ad.get('effective_status'),
                        'bid_amount': float(ad.get('bid_amount', 0)) if ad.get('bid_amount') else 0.0,
                        'last_updated_by_app_id': ad.get('last_updated_by_app_id'),
                        'source_ad_id': ad.get('source_ad_id'),
                        'creative': json.dumps(ad.get('creative', {})) if ad.get('creative') else None,
                        'tracking_specs': json.dumps(ad.get('tracking_specs', [])) if ad.get('tracking_specs') else None,
                        'conversion_specs': json.dumps(ad.get('conversion_specs', [])) if ad.get('conversion_specs') else None,
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
                        'social_spend': float(daily_insight.get('social_spend', 0)) if daily_insight.get('social_spend') else 0.0,
                        'unique_inline_link_clicks': int(daily_insight.get('unique_inline_link_clicks', 0)) if daily_insight.get('unique_inline_link_clicks') else 0,
                        'unique_inline_link_click_ctr': float(daily_insight.get('unique_inline_link_click_ctr', 0)) if daily_insight.get('unique_inline_link_click_ctr') else 0.0,
                        'updated_at': datetime.now()
                    }

                    # Parsear fechas del ad
                    if ad.get('created_time'):
                        try:
                            record_data['ad_created_time'] = datetime.fromisoformat(
                                ad['created_time'].replace('Z', '+00:00')
                            )
                        except:
                            pass

                    if ad.get('updated_time'):
                        try:
                            record_data['ad_updated_time'] = datetime.fromisoformat(
                                ad['updated_time'].replace('Z', '+00:00')
                            )
                        except:
                            pass

                    # Verificar si existe con PRIMARY KEY compuesta usando Django ORM
                    try:
                        existing = Ads.objects.get(
                            ad_id=ad_id,
                            insights_date_start=insights_date_start
                        )
                        # Existe, actualizar
                        for key, value in record_data.items():
                            setattr(existing, key, value)
                        existing.save()
                        stats['actualizados'] += 1

                    except Ads.DoesNotExist:
                        # No existe, crear nuevo
                        Ads.objects.create(
                            ad_id=ad_id,
                            insights_date_start=insights_date_start,
                            **record_data
                        )
                        stats['insertados'] += 1

                except Exception as e:
                    print(f"Error procesando ad {ad_id}: {str(e)}")
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
