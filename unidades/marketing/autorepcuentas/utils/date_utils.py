#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
UTILIDADES DE FECHA - AutoRepCuentas
Módulo común para manejar fechas de manera consistente (adaptado para Django)
"""

import os
import json
from datetime import datetime, timedelta


class DateManager:
    """Maneja fechas de manera consistente para todo el sistema"""

    def __init__(self):
        """Inicializa el manejador de fechas"""
        # ADAPTACIÓN DJANGO: Buscar archivos en la raíz del proyecto
        # Subir 4 niveles: utils -> autorepcuentas -> marketing -> unidades -> automatizacionesBackend
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        self.config_path = os.path.join(base_dir, "config.json")
        self.date_cache_file = os.path.join(base_dir, "date_cache.json")

    def get_extraction_dates(self, script_name=""):
        """
        Obtiene fechas de extracción consistentes
        Para adsets/ads: SIEMPRE usa fecha actual (ignora caché viejo)
        Para campaigns: Usa caché si es del mismo día
        """
        # SOLUCIÓN: Para adsets/ads SIEMPRE generar fechas actuales basadas en start_time
        # Los insights se extraen desde la fecha de creación de cada adset/ad hasta hoy
        if script_name.lower() in ["adsets", "ads"]:
            print(f"🔄 {script_name.upper()}: Usando fechas para insights")
            date_end = datetime.now().strftime('%Y-%m-%d')
            # Fecha mínima: 2025-01-01
            date_start = '2025-01-01'

            dates = {
                'date_start': date_start,
                'date_end': date_end,
                'from_cache': False
            }

            print(f"📅 Rango de extracción: {date_start} hasta {date_end}")
            print(f"💡 Solo datos desde 2025 en adelante")

            return dates

        # Para campaigns: usar lógica original con caché
        try:
            # Intentar cargar fecha del caché
            if os.path.exists(self.date_cache_file):
                with open(self.date_cache_file, 'r', encoding='utf-8') as f:
                    date_cache = json.load(f)

                # Verificar si el caché es reciente (mismo día)
                cache_date = datetime.fromisoformat(date_cache.get('cache_timestamp', ''))
                current_date = datetime.now()

                if cache_date.date() == current_date.date():
                    print(f"📅 CAMPAIGNS: Usando fechas del caché para consistencia:")
                    print(f"   - Fecha final: {date_cache['date_end']}")
                    return {
                        'date_start': date_cache['date_start'],
                        'date_end': date_cache['date_end'],
                        'from_cache': True
                    }

        except Exception as e:
            print(f"⚠️ No se pudo cargar caché de fechas: {e}")

        # Generar nuevas fechas
        date_end = datetime.now().strftime('%Y-%m-%d')

        # Fecha de inicio: 2025-01-01 (solo datos desde 2025)
        date_start = '2025-01-01'

        dates = {
            'date_start': date_start,
            'date_end': date_end,
            'from_cache': False
        }

        # Guardar en caché
        self.save_date_cache(dates)

        print(f"📅 CAMPAIGNS: Nuevas fechas generadas:")
        print(f"   - Desde: {date_start} (solo 2025 en adelante)")
        print(f"   - Hasta: {date_end}")

        return dates

    def save_date_cache(self, dates):
        """Guarda las fechas en caché para consistencia"""
        try:
            cache_data = {
                'date_start': dates['date_start'],
                'date_end': dates['date_end'],
                'cache_timestamp': datetime.now().isoformat(),
                'created_by': 'AutoRepCuentas_DATE_UTILS'
            }

            with open(self.date_cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)

            print(f"💾 Caché de fechas guardado para consistencia")

        except Exception as e:
            print(f"⚠️ Error guardando caché de fechas: {e}")

    def clear_date_cache(self):
        """Limpia el caché de fechas para forzar nuevas fechas"""
        try:
            if os.path.exists(self.date_cache_file):
                os.remove(self.date_cache_file)
                print("🗑️ Caché de fechas eliminado - se generarán nuevas fechas")
                return True
        except Exception as e:
            print(f"⚠️ Error eliminando caché de fechas: {e}")
        return False

    def get_meta_api_date_limits(self):
        """Retorna los límites de fecha que acepta Meta API - DESDE ENERO 2025"""
        today = datetime.now()
        min_date = datetime(2025, 1, 1)  # Inicio 2025

        return {
            'min_date': min_date.strftime('%Y-%m-%d'),
            'max_date': today.strftime('%Y-%m-%d')
        }

    def validate_campaign_date(self, campaign_start_time, date_end):
        """
        Valida si una campaña está en el rango válido de fechas
        """
        try:
            if not campaign_start_time:
                return False, "Sin fecha de inicio"

            # Parsear fecha de campaña - NORMALIZAR A NAIVE
            if 'T' in campaign_start_time:
                campaign_date = datetime.fromisoformat(campaign_start_time.replace('Z', '+00:00'))
                # Convertir a naive (sin timezone)
                campaign_date = campaign_date.replace(tzinfo=None)
            else:
                campaign_date = datetime.strptime(campaign_start_time, '%Y-%m-%d')

            # Parsear fecha final - MANTENER NAIVE
            end_date = datetime.strptime(date_end, '%Y-%m-%d')

            # Verificar límites de Meta API - MANTENER NAIVE
            limits = self.get_meta_api_date_limits()
            min_allowed = datetime.strptime(limits['min_date'], '%Y-%m-%d')

            if campaign_date < min_allowed:
                return False, f"Campaña anterior a 2025 (antes de {limits['min_date']})"

            if campaign_date > end_date:
                return False, f"Campaña creada después de fecha final ({date_end})"

            return True, "Válida"

        except Exception as e:
            return False, f"Error validando fecha: {e}"


# Función de conveniencia para obtener fechas
def get_consistent_dates(script_name=""):
    """Función helper para obtener fechas consistentes"""
    manager = DateManager()
    return manager.get_extraction_dates(script_name)


# Función para limpiar caché de fechas
def clear_dates_cache():
    """Función helper para limpiar caché de fechas"""
    manager = DateManager()
    return manager.clear_date_cache()


if __name__ == "__main__":
    # Test del módulo
    print("🧪 Testing DateManager...")
    manager = DateManager()
    dates = manager.get_extraction_dates("test")
    print(f"Fechas obtenidas: {dates}")
