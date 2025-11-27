#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ACCOUNTS CONTROLLER - AutoRepCuentas
Controlador para operaciones con cuentas
Usa Django ORM para PostgreSQL local
"""

import os
import sys
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from ..conexiones.connection_meta_api import MetaAPI
from ..models import Accounts


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
# * Descripción: Sincroniza las cuentas del config.json con PostgreSQL local usando Django ORM
#
# ! Parámetros:
#   - No recibe ningún parámetro
#
# ? Return:
#   - Caso success: { status: 'success', inserted: N, updated: N, unchanged: N, errors: N }
#   - Caso error: { status: 'error', message: '...' }
# --------------------------------------------------------------------------------------------------
def sync_accounts_to_supabase():
    """Sincroniza las cuentas con PostgreSQL local usando Django ORM"""
    try:
        meta_api = MetaAPI()
        accounts = meta_api.get_all_accounts()

        if not accounts:
            return {
                'status': 'error',
                'message': 'No se encontraron cuentas en config.json'
            }

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

                # Verificar si existe usando Django ORM
                try:
                    existing = Accounts.objects.get(account_id=account_id)

                    # Existe, verificar si necesita actualización
                    needs_update = False

                    if existing.account_name != account_name:
                        existing.account_name = account_name
                        needs_update = True

                    if existing.marcas != account_data.get('marcas', ''):
                        existing.marcas = account_data.get('marcas', '')
                        needs_update = True

                    if existing.multimarca != account_data.get('multimarca', 'No'):
                        existing.multimarca = account_data.get('multimarca', 'No')
                        needs_update = True

                    if existing.app_id != account_data.get('app_id', ''):
                        existing.app_id = account_data.get('app_id', '')
                        needs_update = True

                    has_token = bool(account_data.get('access_token'))
                    if existing.has_valid_token != has_token:
                        existing.has_valid_token = has_token
                        needs_update = True

                    if needs_update:
                        existing.updated_at = datetime.now()
                        existing.last_sync_date = datetime.now()
                        existing.save()
                        stats['actualizadas'] += 1
                    else:
                        existing.last_sync_date = datetime.now()
                        existing.save(update_fields=['last_sync_date'])
                        stats['sin_cambios'] += 1

                except Accounts.DoesNotExist:
                    # No existe, crear nuevo
                    Accounts.objects.create(
                        account_id=account_id,
                        account_name=account_name,
                        account_key=account_key,
                        multimarca=account_data.get('multimarca', 'No'),
                        marcas=account_data.get('marcas', ''),
                        app_id=account_data.get('app_id', ''),
                        has_valid_token=bool(account_data.get('access_token')),
                        is_active=True,
                        created_at=datetime.now(),
                        updated_at=datetime.now(),
                        last_sync_date=datetime.now()
                    )
                    stats['insertadas'] += 1

            except Exception as e:
                print(f"Error procesando cuenta {account_key}: {str(e)}")
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
