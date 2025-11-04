#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ACCOUNTS CONTROLLER - LEO MASTER
Controlador para operaciones con cuentas
"""

import os
import sys
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from ..conexiones.connection_supabase import SupabaseAPI
from ..conexiones.connection_meta_api import MetaAPI


# --------------------------------------------------------------------------------------------------
# * Función: get_all_accounts
# * Descripción: Obtiene todas las cuentas del config.json
#
# ! Parámetros:
#   - No recibe ningún parámetro
#
# ? Return:
#   - Caso success: { status: 'success', accounts: {...} }
#   - Caso error: { status: 'error', message: '...' }
# --------------------------------------------------------------------------------------------------
def get_all_accounts():
    """Obtiene todas las cuentas del config.json"""
    try:
        meta_api = MetaAPI()
        accounts = meta_api.get_all_accounts()

        return {
            'status': 'success',
            'accounts': accounts
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error obteniendo cuentas: {str(e)}'
        }


# --------------------------------------------------------------------------------------------------
# * Función: sync_accounts_to_supabase
# * Descripción: Sincroniza las cuentas del config.json con Supabase
#
# ! Parámetros:
#   - No recibe ningún parámetro
#
# ? Return:
#   - Caso success: { status: 'success', inserted: N, updated: N, unchanged: N, errors: N }
#   - Caso error: { status: 'error', message: '...' }
# --------------------------------------------------------------------------------------------------
def sync_accounts_to_supabase():
    """Sincroniza las cuentas con Supabase"""
    try:
        meta_api = MetaAPI()
        accounts = meta_api.get_all_accounts()

        if not accounts:
            return {
                'status': 'error',
                'message': 'No se encontraron cuentas en config.json'
            }

        supabase_api = SupabaseAPI()
        supabase = supabase_api.get_client()

        stats = {
            'insertadas': 0,
            'actualizadas': 0,
            'sin_cambios': 0,
            'errores': 0
        }

        for account_key, account_data in accounts.items():
            try:
                account_id = account_data.get('account_id')
                account_name = account_data.get('nombre', 'Sin nombre')

                # Preparar registro para Supabase
                account_record = {
                    'account_id': account_id,
                    'account_name': account_name,
                    'account_key': account_key,
                    'multimarca': account_data.get('multimarca', 'No'),
                    'marcas': account_data.get('marcas', ''),
                    'app_id': account_data.get('app_id', ''),
                    'has_valid_token': bool(account_data.get('access_token')),
                    'last_sync_date': datetime.now().isoformat(),
                    'is_active': True
                }

                # Verificar si existe
                existing = supabase.table('accounts').select('*').eq(
                    'account_id', account_id
                ).execute()

                if not existing.data:
                    # No existe, insertar
                    supabase.table('accounts').insert(account_record).execute()
                    stats['insertadas'] += 1
                else:
                    # Existe, verificar si necesita actualización
                    existing_record = existing.data[0]

                    needs_update = False
                    for field in ['account_name', 'marcas', 'multimarca', 'app_id', 'has_valid_token']:
                        if existing_record.get(field) != account_record.get(field):
                            needs_update = True
                            break

                    if needs_update:
                        # Actualizar
                        account_record['updated_at'] = datetime.now().isoformat()
                        supabase.table('accounts').update(account_record).eq(
                            'account_id', account_id
                        ).execute()
                        stats['actualizadas'] += 1
                    else:
                        # Sin cambios
                        supabase.table('accounts').update({
                            'last_sync_date': datetime.now().isoformat()
                        }).eq('account_id', account_id).execute()
                        stats['sin_cambios'] += 1

            except Exception:
                stats['errores'] += 1
                continue

        return {
            'status': 'success',
            'inserted': stats['insertadas'],
            'updated': stats['actualizadas'],
            'unchanged': stats['sin_cambios'],
            'errors': stats['errores']
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error sincronizando cuentas: {str(e)}'
        }
