"""
Management Command: sincronizar_cuentas
Sincroniza las cuentas desde config.json a la tabla accounts de Supabase

Uso:
    python manage.py sincronizar_cuentas
"""

import os
import json
from datetime import datetime
from django.core.management.base import BaseCommand
from autorepcuentas.conexiones.connection_supabase import SupabaseAPI


class Command(BaseCommand):
    help = 'Sincroniza las cuentas desde config.json a Supabase'

    def handle(self, *args, **options):
        self.stdout.write('='*80)
        self.stdout.write(self.style.SUCCESS('🚀 SINCRONIZADOR DE CUENTAS - AutoRepCuentas'))
        self.stdout.write('='*80)

        try:
            # Leer config.json
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'config.json'
            )

            self.stdout.write('📂 Leyendo config.json...')
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            accounts = config.get('accounts', {})

            if not accounts:
                self.stdout.write(self.style.ERROR('❌ No se encontraron cuentas en config.json'))
                return

            self.stdout.write(self.style.SUCCESS(f'✅ Se encontraron {len(accounts)} cuentas'))
            self.stdout.write('')

            # Conectar a Supabase
            self.stdout.write('🔌 Conectando a Supabase...')
            supabase_api = SupabaseAPI()
            supabase = supabase_api.get_client()
            self.stdout.write(self.style.SUCCESS('✅ Conectado a Supabase'))
            self.stdout.write('')

            # Sincronizar cada cuenta
            stats = {
                'insertadas': 0,
                'actualizadas': 0,
                'errores': 0
            }

            self.stdout.write('📊 Iniciando sincronización...')
            self.stdout.write('')

            for numero, datos in sorted(accounts.items(), key=lambda x: int(x[0])):
                account_id = datos['account_id']
                nombre = datos['nombre']

                try:
                    # Preparar datos para insertar
                    account_data = {
                        'account_id': account_id,
                        'account_name': nombre,
                        'account_key': numero,
                        'multimarca': datos.get('multimarca', 'No'),
                        'marcas': datos.get('marcas', ''),
                        'app_id': datos.get('app_id', ''),
                        'has_valid_token': True,
                        'is_active': True,
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }

                    # Verificar si existe
                    existing = supabase.table('accounts').select('account_id').eq(
                        'account_id', account_id
                    ).execute()

                    if not existing.data:
                        # No existe, insertar
                        supabase.table('accounts').insert(account_data).execute()
                        stats['insertadas'] += 1
                        self.stdout.write(
                            f"  ✅ [{numero}] {nombre} - INSERTADO"
                        )
                    else:
                        # Existe, actualizar
                        account_data['updated_at'] = datetime.now().isoformat()
                        supabase.table('accounts').update(account_data).eq(
                            'account_id', account_id
                        ).execute()
                        stats['actualizadas'] += 1
                        self.stdout.write(
                            f"  🔄 [{numero}] {nombre} - ACTUALIZADO"
                        )

                except Exception as e:
                    stats['errores'] += 1
                    self.stdout.write(
                        self.style.ERROR(f"  ❌ [{numero}] {nombre} - ERROR: {str(e)}")
                    )

            # Resumen final
            self.stdout.write('')
            self.stdout.write('='*80)
            self.stdout.write(self.style.SUCCESS('📊 RESUMEN DE SINCRONIZACIÓN'))
            self.stdout.write('='*80)
            self.stdout.write(f'✅ Cuentas insertadas: {stats["insertadas"]}')
            self.stdout.write(f'🔄 Cuentas actualizadas: {stats["actualizadas"]}')
            self.stdout.write(f'❌ Errores: {stats["errores"]}')
            self.stdout.write(f'📊 Total procesado: {len(accounts)}')
            self.stdout.write('='*80)

            if stats['errores'] == 0:
                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS('🎉 ¡Sincronización completada exitosamente!'))
                self.stdout.write('')
                self.stdout.write('📋 Siguiente paso:')
                self.stdout.write('   1. Extrae datos desde Meta API usando tus controllers')
                self.stdout.write('   2. O genera reportes desde datos existentes en Supabase')
                self.stdout.write('')

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'❌ Error: No se encontró config.json'))
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR('❌ Error: config.json tiene formato inválido'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error inesperado: {str(e)}'))
