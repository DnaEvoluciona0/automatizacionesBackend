"""
Management Command: generar_reporte
Genera reportes de marketing en formato Excel desde Supabase

Uso:
    python manage.py generar_reporte --tipo campaigns --account_id 123456789 --fecha_inicio 2025-01-01 --fecha_fin 2025-01-31
"""

from django.core.management.base import BaseCommand, CommandError
from datetime import datetime, timedelta

from autorepcuentas.services.reporte_service import ReporteMarketingService


class Command(BaseCommand):
    help = 'Genera reportes de marketing en formato Excel'

    def add_arguments(self, parser):
        # Argumentos obligatorios
        parser.add_argument(
            '--tipo',
            type=str,
            required=True,
            choices=['campaigns', 'adsets', 'ads', 'consolidado'],
            help='Tipo de reporte a generar (campaigns, adsets, ads, consolidado)'
        )

        parser.add_argument(
            '--account_id',
            type=str,
            required=True,
            help='ID de la cuenta de Meta Ads'
        )

        # Argumentos opcionales para fechas
        parser.add_argument(
            '--fecha_inicio',
            type=str,
            help='Fecha de inicio (YYYY-MM-DD). Si no se proporciona, usa últimos 30 días'
        )

        parser.add_argument(
            '--fecha_fin',
            type=str,
            help='Fecha de fin (YYYY-MM-DD). Si no se proporciona, usa fecha actual'
        )

        # Flag para últimos 30 días
        parser.add_argument(
            '--ultimos30',
            action='store_true',
            help='Genera reporte de últimos 30 días automáticamente'
        )

    def handle(self, *args, **options):
        tipo = options['tipo']
        account_id = options['account_id']
        fecha_inicio = options.get('fecha_inicio')
        fecha_fin = options.get('fecha_fin')
        ultimos30 = options.get('ultimos30', False)

        # Validar y calcular fechas
        if ultimos30 or not fecha_inicio or not fecha_fin:
            fecha_fin = datetime.now().strftime('%Y-%m-%d')
            fecha_inicio = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            self.stdout.write(
                self.style.WARNING(f'📅 Usando últimos 30 días: {fecha_inicio} a {fecha_fin}')
            )

        # Validar formato de fechas
        try:
            datetime.strptime(fecha_inicio, '%Y-%m-%d')
            datetime.strptime(fecha_fin, '%Y-%m-%d')
        except ValueError:
            raise CommandError('Formato de fecha inválido. Use YYYY-MM-DD')

        # Mostrar información
        self.stdout.write('='*80)
        self.stdout.write(self.style.SUCCESS('🚀 GENERADOR DE REPORTES - AutoRepCuentas'))
        self.stdout.write('='*80)
        self.stdout.write(f'📊 Tipo: {tipo}')
        self.stdout.write(f'🏢 Cuenta: {account_id}')
        self.stdout.write(f'📅 Período: {fecha_inicio} a {fecha_fin}')
        self.stdout.write('='*80)

        # Generar reporte
        try:
            service = ReporteMarketingService()

            self.stdout.write(self.style.WARNING('🔄 Consultando datos de Supabase...'))

            success, filepath = service.generar_reporte(
                tipo=tipo,
                account_id=account_id,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin
            )

            if success:
                self.stdout.write('='*80)
                self.stdout.write(self.style.SUCCESS('✅ ¡REPORTE GENERADO EXITOSAMENTE!'))
                self.stdout.write(self.style.SUCCESS(f'📁 Archivo: {filepath}'))
                self.stdout.write('='*80)
            else:
                raise CommandError('❌ Error al generar el reporte. Verifica los logs.')

        except Exception as e:
            raise CommandError(f'❌ Error inesperado: {str(e)}')
