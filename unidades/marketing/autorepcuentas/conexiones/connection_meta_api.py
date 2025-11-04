#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CONEXIÓN A META API - AutoRepCuentas
Módulo de conexión centralizado para Meta Graph API (adaptado para Django)
"""

import os
import sys
import json
import requests


class MetaAPI:
    """Clase para manejar la conexión con Meta Graph API"""

    def __init__(self):
        """Inicializa la configuración de Meta API"""
        self.config = None
        self.api_base_url = "https://graph.facebook.com/v18.0"

        # Cargar configuración
        self._load_config()

    def _load_config(self):
        """Carga la configuración desde config.json"""
        # ADAPTACIÓN DJANGO: Buscar config.json en la raíz del proyecto Django
        # Subir 4 niveles: autorepcuentas -> marketing -> unidades -> automatizacionesBackend
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        config_path = os.path.join(base_dir, "config.json")

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except Exception as e:
            print(f"❌ Error cargando config.json: {e}")
            print(f"   Ruta esperada: {config_path}")
            sys.exit(1)

    def get_account_config(self, account_key):
        """Obtiene la configuración de una cuenta específica"""
        accounts = self.config.get('accounts', {})
        if account_key in accounts:
            return accounts[account_key]
        return None

    def get_all_accounts(self):
        """Obtiene todas las cuentas configuradas"""
        return self.config.get('accounts', {})

    def test_api_connection(self, account_data):
        """Prueba la conexión a la API de Meta"""
        url = f"{self.api_base_url}/me"
        params = {'access_token': account_data['access_token']}

        try:
            response = requests.get(url, params=params, timeout=30)
            data = response.json()

            if response.status_code == 200:
                return True, f"Usuario: {data.get('name', 'N/A')}"
            else:
                error_info = data.get('error', {})
                error_code = error_info.get('code', 'N/A')
                error_message = error_info.get('message', 'Error desconocido')
                return False, f"Error [{error_code}]: {error_message}"

        except Exception as e:
            return False, f"Error de conexión: {e}"

    def get_api_base_url(self):
        """Retorna la URL base de la API"""
        return self.api_base_url
