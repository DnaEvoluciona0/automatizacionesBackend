#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CAMPAIGNS VIEW - LEO MASTER
Vista para presentación de campañas y menús
"""

import os
import sys
import json
from datetime import datetime

# Agregar el directorio raíz al path para imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from conexiones.connection_meta_api import MetaAPI
from controllers import campaigns_controller


def show_header():
    """Muestra el encabezado de la aplicación"""
    print("="*80)
    print("🚀 HTTP EXTRACTOR - META ADS CAMPAIGNS")
    print("="*80)


def show_main_menu():
    """Muestra el menú principal de opciones"""
    print("\n📋 MENÚ PRINCIPAL:")
    print("-" * 40)
    print("[1] Extraer campañas e Insights individual")
    print("-" * 40)

    while True:
        selection = input("\n👉 Selecciona una opción: ").strip()
        if selection == "1":
            return "extract_campaigns"
        print("❌ Opción inválida. Intenta de nuevo.")


def select_account():
    """Permite al usuario seleccionar una cuenta"""
    print("\n📋 CUENTAS DISPONIBLES:")
    print("-" * 40)

    meta_api = MetaAPI()
    accounts = meta_api.get_all_accounts()

    for key, account in accounts.items():
        print(f"[{key}] {account['nombre']} - {account.get('marcas', 'N/A')}")

    print("-" * 40)
    while True:
        selection = input("\n👉 Selecciona el número de cuenta: ").strip()
        if selection in accounts:
            return selection, accounts[selection]
        print("❌ Selección inválida. Intenta de nuevo.")


def test_api_connection(account_data):
    """Prueba y muestra el resultado de la conexión API"""
    print(f"\n🔗 Probando conexión API para: {account_data['nombre']}")

    meta_api = MetaAPI()
    success, message = meta_api.test_api_connection(account_data)

    if success:
        print(f"✅ API conectada exitosamente - {message}")
        return True
    else:
        print(f"❌ ERROR DE API: {message}")
        print(f"💡 POSIBLE SOLUCIÓN:")
        print("   - Verifica que el access_token sea válido")
        print("   - Genera un nuevo access_token si es necesario")
        sys.exit(1)


def show_extraction_progress(phase, message):
    """Muestra el progreso de la extracción"""
    symbols = {
        'info': '📊',
        'success': '✅',
        'error': '❌',
        'warning': '⚠️',
        'processing': '🔄'
    }
    symbol = symbols.get(phase, '📝')
    print(f"{symbol} {message}")


def save_to_json(data, account_name, data_type):
    """Guarda datos en archivo JSON"""
    output_dir = os.path.join(os.path.dirname(__file__), "..", "JSON")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{data_type}_{account_name.replace(' ', '_')}_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    show_extraction_progress('success', f"{data_type.capitalize()} guardados en: {filename}")
    return filepath


def show_results_summary(campaigns_count, insights_count, sync_result):
    """Muestra el resumen de resultados"""
    print("\n" + "="*80)
    print("✅ EXTRACCIÓN COMPLETADA")
    print("="*80)
    print(f"\n📊 Resumen:")
    print(f"   - Campañas extraídas: {campaigns_count}")
    print(f"   - Insights obtenidos: {insights_count}")

    if sync_result and sync_result.get('status') == 'success':
        print(f"\n🔄 Sincronización con Supabase:")
        print(f"   ✅ Insertados: {sync_result.get('inserted', 0)}")
        print(f"   🔄 Actualizados: {sync_result.get('updated', 0)}")
        print(f"   ❌ Errores: {sync_result.get('errors', 0)}")


def run_extraction_process(account_number=None):
    """Ejecuta el proceso completo de extracción"""
    show_header()

    # Seleccionar cuenta
    if account_number:
        meta_api = MetaAPI()
        accounts = meta_api.get_all_accounts()
        if account_number not in accounts:
            print(f"❌ Cuenta {account_number} no encontrada")
            return
        account_key = account_number
        account_data = accounts[account_number]
        print(f"\n✅ Cuenta seleccionada: [{account_key}] {account_data['nombre']}")
    else:
        account_key, account_data = select_account()

    # Probar conexión API
    test_api_connection(account_data)

    # Extraer campañas
    print("\n" + "="*80)
    print("EXTRAYENDO CAMPAÑAS")
    print("="*80)

    show_extraction_progress('processing', 'Obteniendo campañas de Meta API...')
    campaigns_result = campaigns_controller.get_all_campaigns(account_data)

    if campaigns_result['status'] != 'success':
        print(f"❌ Error: {campaigns_result['message']}")
        return

    campaigns_data = campaigns_result['campaigns']
    show_extraction_progress('success', f"{campaigns_result['count']} campañas obtenidas")

    # Guardar campañas en JSON
    save_to_json(campaigns_data, account_data['nombre'], 'campaigns')

    # Extraer insights
    if campaigns_data:
        print("\n" + "="*80)
        print("EXTRAYENDO INSIGHTS")
        print("="*80)

        show_extraction_progress('processing', 'Obteniendo insights de campañas...')
        insights_result = campaigns_controller.get_campaigns_insights(account_data, campaigns_data)

        if insights_result['status'] != 'success':
            print(f"❌ Error: {insights_result['message']}")
            return

        insights_data = insights_result['insights']
        show_extraction_progress('success', f"{insights_result['count']} insights obtenidos")

        # Guardar insights en JSON
        save_to_json(insights_data, account_data['nombre'], 'insights_campaigns')

        # Sincronizar con Supabase
        if campaigns_data and insights_data:
            print("\n" + "="*80)
            print("SINCRONIZANDO CON SUPABASE")
            print("="*80)

            show_extraction_progress('processing', 'Sincronizando datos con base de datos...')
            sync_result = campaigns_controller.sync_campaigns_to_supabase(
                campaigns_data, insights_data, account_data
            )

            if sync_result['status'] == 'success':
                show_extraction_progress('success', 'Sincronización completada')
            else:
                show_extraction_progress('error', f"Error en sincronización: {sync_result['message']}")

            # Mostrar resumen final
            show_results_summary(
                len(campaigns_data),
                len(insights_data),
                sync_result
            )
    else:
        print("⚠️ No se encontraron campañas para extraer insights")


if __name__ == "__main__":
    import sys
    # Si se pasa un argumento, usarlo como número de cuenta
    if len(sys.argv) > 1:
        run_extraction_process(account_number=sys.argv[1])
    else:
        run_extraction_process()
