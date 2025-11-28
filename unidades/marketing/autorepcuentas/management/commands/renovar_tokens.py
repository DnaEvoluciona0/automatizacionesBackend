#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Management Command: renovar_tokens
Renueva automaticamente los tokens de Meta Ads proximos a expirar

Uso:
    python manage.py renovar_tokens          # Renueva tokens con menos de 15 dias
    python manage.py renovar_tokens --force  # Renueva todos los tokens validos
    python manage.py renovar_tokens --check  # Solo verifica, no renueva

Programar en Windows Task Scheduler:
    Ejecutar cada Lunes a las 9:00 AM
"""

from django.core.management.base import BaseCommand
from unidades.marketing.autorepcuentas.services.token_service import TokenService


class Command(BaseCommand):
    help = 'Renueva automaticamente los tokens de Meta Ads'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar renovacion de todos los tokens validos',
        )
        parser.add_argument(
            '--check',
            action='store_true',
            help='Solo verificar tokens, no renovar',
        )

    def handle(self, *args, **options):
        self.stdout.write("=" * 70)
        self.stdout.write(self.style.SUCCESS("AUTO TOKEN RENOVATOR - AutoRepCuentas"))
        self.stdout.write("=" * 70)

        token_service = TokenService()

        if options['check']:
            # Solo verificar
            self.stdout.write("\nVerificando estado de tokens...\n")
            resultado = token_service.get_all_tokens_status()

            if resultado['status'] != 'success':
                self.stdout.write(self.style.ERROR(f"Error: {resultado.get('message')}"))
                return

            tokens = resultado['tokens']
            resumen = resultado['resumen']

            for token in tokens:
                status_icon = {
                    'ok': '✅',
                    'permanente': '♾️',
                    'advertencia': '⚠️',
                    'critico': '🔴',
                    'expirado': '❌',
                    'invalido': '❌',
                    'sin_token': '⚪',
                    'sin_credenciales': '⚪',
                }.get(token['status'], '❓')

                self.stdout.write(
                    f"  [{token['account_key']}] {token['nombre']}: "
                    f"{status_icon} {token['status_text']}"
                )

            self.stdout.write("\n" + "-" * 70)
            self.stdout.write(f"Total: {resumen['total']}")
            self.stdout.write(self.style.SUCCESS(f"OK: {resumen['ok']}"))
            self.stdout.write(self.style.WARNING(f"Advertencia: {resumen['advertencia']}"))
            self.stdout.write(self.style.ERROR(f"Critico: {resumen['critico']}"))
            self.stdout.write(self.style.ERROR(f"Expirado/Invalido: {resumen['expirado'] + resumen['invalido']}"))

        else:
            # Renovar tokens
            solo_proximos = not options['force']

            if solo_proximos:
                self.stdout.write("\nRenovando tokens proximos a expirar (< 15 dias)...\n")
            else:
                self.stdout.write("\nRenovando TODOS los tokens validos...\n")

            resultado = token_service.renovar_todos(solo_proximos_a_expirar=solo_proximos)

            if resultado['status'] != 'success':
                self.stdout.write(self.style.ERROR(f"Error: {resultado.get('message')}"))
                return

            stats = resultado['stats']
            detalles = resultado['detalles']

            for detalle in detalles:
                icon = {
                    'ok': '✅',
                    'renovado': '🔄',
                    'saltado': '⚪',
                    'invalido': '❌',
                    'error': '❌',
                }.get(detalle['resultado'], '❓')

                color = {
                    'ok': self.style.SUCCESS,
                    'renovado': self.style.SUCCESS,
                    'saltado': lambda x: x,
                    'invalido': self.style.ERROR,
                    'error': self.style.ERROR,
                }.get(detalle['resultado'], lambda x: x)

                self.stdout.write(
                    f"  [{detalle['account_key']}] {detalle['nombre']}: "
                    f"{icon} {color(detalle['mensaje'])}"
                )

            self.stdout.write("\n" + "=" * 70)
            self.stdout.write("RESUMEN DE RENOVACION")
            self.stdout.write("=" * 70)
            self.stdout.write(f"  Total cuentas: {stats['total']}")
            self.stdout.write(self.style.SUCCESS(f"  OK (no necesitan renovacion): {stats['ok']}"))
            self.stdout.write(self.style.SUCCESS(f"  Renovados: {stats['renovados']}"))
            self.stdout.write(f"  Saltados (sin credenciales): {stats['saltados']}")
            self.stdout.write(self.style.ERROR(f"  Tokens invalidos: {stats['invalidos']}"))
            self.stdout.write(self.style.ERROR(f"  Errores: {stats['errores']}"))
            self.stdout.write("=" * 70)

            if stats['invalidos'] > 0 or stats['saltados'] > 0:
                self.stdout.write("\n" + self.style.WARNING("NOTA:"))
                self.stdout.write("  Para cuentas con tokens invalidos o sin token:")
                self.stdout.write("  1. Ve a https://developers.facebook.com/tools/explorer/")
                self.stdout.write("  2. Selecciona tu app y genera un nuevo token")
                self.stdout.write("  3. Copia el token a config.json")
                self.stdout.write("  4. Ejecuta este comando de nuevo")
