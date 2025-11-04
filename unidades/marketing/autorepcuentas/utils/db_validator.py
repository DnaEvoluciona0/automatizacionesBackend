#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VALIDADOR DE BASE DE DATOS - AutoRepCuentas
Módulo para validar existencia de campaigns, adsets y ads en Supabase (adaptado para Django)
"""

import os
import json
import sys
from datetime import datetime
from supabase import create_client, Client


class DatabaseValidator:
    """Valida existencia de registros en la base de datos"""

    def __init__(self):
        """Inicializa el validador de BD"""
        self.load_config()
        self.init_supabase_client()
        self._cache = {
            'campaigns': {},
            'adsets': {},
            'ads': {}
        }
        self._cache_timestamp = datetime.now()

    def load_config(self):
        """Carga la configuración desde config.json"""
        # ADAPTACIÓN DJANGO: Buscar config.json en la raíz del proyecto
        # Subir 4 niveles: utils -> autorepcuentas -> marketing -> unidades -> automatizacionesBackend
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        config_path = os.path.join(base_dir, "config.json")

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except Exception as e:
            print(f"❌ Error cargando config.json: {e}")
            print(f"   Ruta esperada: {config_path}")
            sys.exit(1)

    def init_supabase_client(self):
        """Inicializa el cliente de Supabase"""
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

    def clear_cache(self):
        """Limpia el caché de validación"""
        self._cache = {
            'campaigns': {},
            'adsets': {},
            'ads': {}
        }
        self._cache_timestamp = datetime.now()
        print("🗑️ Caché de validación limpiado")

    def is_cache_valid(self, max_age_minutes=30):
        """Verifica si el caché es válido"""
        age = (datetime.now() - self._cache_timestamp).total_seconds() / 60
        return age < max_age_minutes

    def load_campaigns_cache(self, account_id=None):
        """Carga todas las campaigns en caché para validación rápida"""
        try:
            if not self.is_cache_valid():
                print("🔄 Recargando caché de campaigns...")
                self._cache['campaigns'] = {}

            # Si ya está cargado, no recargar
            cache_key = f"account_{account_id}" if account_id else "all"
            if cache_key in self._cache['campaigns']:
                return

            print("📊 Cargando campaigns en caché para validación...")

            query = self.supabase.table('campaigns').select('campaign_id, account_id')
            if account_id:
                query = query.eq('account_id', account_id)

            result = query.execute()

            if result.data:
                campaigns_dict = {}
                for campaign in result.data:
                    campaigns_dict[campaign['campaign_id']] = {
                        'account_id': campaign['account_id'],
                        'exists': True
                    }

                self._cache['campaigns'][cache_key] = campaigns_dict
                print(f"✅ {len(campaigns_dict)} campaigns cargadas en caché")
            else:
                self._cache['campaigns'][cache_key] = {}
                print("⚠️ No se encontraron campaigns en BD")

        except Exception as e:
            print(f"❌ Error cargando caché de campaigns: {e}")
            self._cache['campaigns'][cache_key] = {}

    def load_adsets_cache(self, account_id=None):
        """Carga todos los adsets en caché para validación rápida"""
        try:
            if not self.is_cache_valid():
                print("🔄 Recargando caché de adsets...")
                self._cache['adsets'] = {}

            cache_key = f"account_{account_id}" if account_id else "all"
            if cache_key in self._cache['adsets']:
                return

            print("📊 Cargando adsets en caché para validación...")

            query = self.supabase.table('adsets').select('adset_id, campaign_id, account_id')
            if account_id:
                query = query.eq('account_id', account_id)

            result = query.execute()

            if result.data:
                adsets_dict = {}
                for adset in result.data:
                    adsets_dict[adset['adset_id']] = {
                        'campaign_id': adset['campaign_id'],
                        'account_id': adset.get('account_id'),
                        'exists': True
                    }

                self._cache['adsets'][cache_key] = adsets_dict
                print(f"✅ {len(adsets_dict)} adsets cargados en caché")
            else:
                self._cache['adsets'][cache_key] = {}
                print("⚠️ No se encontraron adsets en BD")

        except Exception as e:
            print(f"❌ Error cargando caché de adsets: {e}")
            self._cache['adsets'][cache_key] = {}

    def campaign_exists(self, campaign_id, account_id=None):
        """
        Verifica si una campaña existe en BD
        Returns: (exists: bool, info: dict)
        """
        try:
            # Cargar caché si es necesario
            cache_key = f"account_{account_id}" if account_id else "all"
            if cache_key not in self._cache['campaigns']:
                self.load_campaigns_cache(account_id)

            campaigns_cache = self._cache['campaigns'].get(cache_key, {})

            if campaign_id in campaigns_cache:
                return True, campaigns_cache[campaign_id]
            else:
                return False, {'reason': 'campaign_not_found'}

        except Exception as e:
            print(f"⚠️ Error validando campaign {campaign_id}: {e}")
            return False, {'reason': f'validation_error: {e}'}

    def adset_exists(self, adset_id, account_id=None):
        """
        Verifica si un adset existe en BD
        Returns: (exists: bool, info: dict)
        """
        try:
            # Cargar caché si es necesario
            cache_key = f"account_{account_id}" if account_id else "all"
            if cache_key not in self._cache['adsets']:
                self.load_adsets_cache(account_id)

            adsets_cache = self._cache['adsets'].get(cache_key, {})

            if adset_id in adsets_cache:
                return True, adsets_cache[adset_id]
            else:
                return False, {'reason': 'adset_not_found'}

        except Exception as e:
            print(f"⚠️ Error validando adset {adset_id}: {e}")
            return False, {'reason': f'validation_error: {e}'}

    def validate_campaign_for_adset(self, campaign_id, account_id=None):
        """
        Valida que existe la campaña antes de insertar un adset
        Returns: (can_insert: bool, message: str)
        """
        exists, info = self.campaign_exists(campaign_id, account_id)

        if exists:
            return True, "Campaign exists - can insert adset"
        else:
            reason = info.get('reason', 'unknown')
            if reason == 'campaign_not_found':
                return False, f"Campaign {campaign_id} not found in database. Run campaigns extraction first."
            else:
                return False, f"Campaign validation failed: {reason}"

    def validate_adset_for_ad(self, adset_id, account_id=None):
        """
        Valida que existe el adset antes de insertar un ad
        Returns: (can_insert: bool, message: str)
        """
        exists, info = self.adset_exists(adset_id, account_id)

        if exists:
            return True, "Adset exists - can insert ad"
        else:
            reason = info.get('reason', 'unknown')
            if reason == 'adset_not_found':
                return False, f"Adset {adset_id} not found in database. Run adsets extraction first."
            else:
                return False, f"Adset validation failed: {reason}"

    def get_validation_stats(self):
        """Retorna estadísticas del caché de validación"""
        stats = {
            'cache_age_minutes': (datetime.now() - self._cache_timestamp).total_seconds() / 60,
            'campaigns_cached': sum(len(cache) for cache in self._cache['campaigns'].values()),
            'adsets_cached': sum(len(cache) for cache in self._cache['adsets'].values()),
            'cache_valid': self.is_cache_valid()
        }
        return stats

    def print_validation_stats(self):
        """Imprime estadísticas del caché"""
        stats = self.get_validation_stats()
        print(f"\n📊 ESTADÍSTICAS DE VALIDACIÓN:")
        print(f"   ⏰ Edad del caché: {stats['cache_age_minutes']:.1f} minutos")
        print(f"   📊 Campaigns en caché: {stats['campaigns_cached']}")
        print(f"   📊 Adsets en caché: {stats['adsets_cached']}")
        print(f"   ✅ Caché válido: {'Sí' if stats['cache_valid'] else 'No'}")


# Funciones de conveniencia
def create_validator():
    """Crea una nueva instancia del validador"""
    return DatabaseValidator()


if __name__ == "__main__":
    # Test del módulo
    print("🧪 Testing DatabaseValidator...")
    validator = DatabaseValidator()
    validator.print_validation_stats()
