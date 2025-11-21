"""
Management Command: listar_cuentas
Lista las cuentas disponibles desde config.json para los scripts .bat

Uso:
    python manage.py listar_cuentas --formato list
    python manage.py listar_cuentas --formato info
    python manage.py listar_cuentas --formato account_id --numero 1
"""

import os
import json
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Lista las cuentas disponibles desde config.json'

    def add_arguments(self, parser):
        parser.add_argument(
            '--formato',
            type=str,
            choices=['list', 'info', 'account_id'],
            default='info',
            help='Formato de salida: list (números), info (detalles) o account_id (obtener account_id)'
        )
        parser.add_argument(
            '--numero',
            type=str,
            help='Número de cuenta (usado con --formato account_id)'
        )

    def handle(self, *args, **options):
        formato = options['formato']
        numero = options.get('numero')

        try:
            # Leer config.json
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'config.json'
            )

            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            accounts = config.get('accounts', {})

            if not accounts:
                if formato != 'list':
                    self.stdout.write('No hay cuentas disponibles')
                return

            # Formato según opción
            if formato == 'list':
                # Solo números de cuenta (para validación en .bat)
                for numero_cuenta in accounts.keys():
                    self.stdout.write(numero_cuenta)

            elif formato == 'account_id':
                # Obtener account_id específico
                if not numero:
                    self.stderr.write('Error: Se requiere --numero con --formato account_id')
                    return

                if numero in accounts:
                    self.stdout.write(accounts[numero]['account_id'])
                else:
                    self.stderr.write(f'Error: Cuenta {numero} no encontrada')

            else:
                # Información detallada (para mostrar menú)
                for numero_cuenta, datos in sorted(accounts.items(), key=lambda x: int(x[0])):
                    multimarca = datos.get('multimarca', 'No')
                    # Formato: numero|nombre|account_id|marcas|multimarca
                    self.stdout.write(
                        f"{numero_cuenta}|{datos['nombre']}|{datos['account_id']}|{datos.get('marcas', 'N/A')}|{multimarca}"
                    )

        except FileNotFoundError:
            self.stderr.write(f"Error: No se encontró config.json en {config_path}")
        except json.JSONDecodeError:
            self.stderr.write("Error: config.json tiene formato inválido")
        except Exception as e:
            self.stderr.write(f"Error: {str(e)}")
