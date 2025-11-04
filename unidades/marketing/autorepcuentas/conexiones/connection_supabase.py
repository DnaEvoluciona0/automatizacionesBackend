#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CONEXIÓN A SUPABASE - AutoRepCuentas
Módulo de conexión centralizado para Supabase (adaptado para Django)
"""

import os
import sys
import json
from supabase import create_client, Client


class SupabaseAPI:
    """Clase para manejar la conexión con Supabase"""

    def __init__(self):
        """Inicializa la conexión con Supabase"""
        self.config = None
        self.supabase: Client = None

        # Cargar configuración y establecer conexión
        self._load_config()
        self._connect()

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

    def _connect(self):
        """Establece la conexión con Supabase"""
        try:
            supabase_config = self.config.get('supabase', {})
            url = supabase_config.get('url')
            key = supabase_config.get('service_role_key')

            if not url or not key:
                print("❌ Error: Configuración de Supabase incompleta en config.json")
                sys.exit(1)

            self.supabase = create_client(url, key)

        except Exception as e:
            print(f"❌ Error inicializando Supabase: {e}")
            sys.exit(1)

    def get_client(self):
        """Retorna el cliente de Supabase"""
        return self.supabase

    def test_connection(self):
        """Prueba la conexión con Supabase"""
        try:
            self.supabase.table('campaigns').select('campaign_id').limit(1).execute()
            print("✅ Conexión con Supabase verificada")
            return True
        except Exception as e:
            print(f"❌ Error de conexión con Supabase: {e}")
            return False
