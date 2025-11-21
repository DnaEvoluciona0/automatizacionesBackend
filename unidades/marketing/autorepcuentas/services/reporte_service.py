#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SERVICIO DE GENERACIÓN DE REPORTES - AutoRepCuentas
Genera reportes Excel de campaigns, adsets y ads desde Supabase
Adaptado para Django
"""

import os
from datetime import datetime
from decimal import Decimal
import pandas as pd
from django.conf import settings

from ..conexiones.connection_supabase import SupabaseAPI


class ReporteMarketingService:
    """Servicio para generar reportes de marketing en formato Excel"""

    def __init__(self):
        """Inicializa el servicio de reportes"""
        # Inicializar cliente Supabase
        self.supabase_api = SupabaseAPI()
        self.supabase = self.supabase_api.get_client()

        # Definir carpeta de reportes
        self.reports_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'REPORTES_EXCEL'
        )

        # Crear carpeta si no existe
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)

    def query_campaigns_by_date_range(self, account_id, start_date, end_date):
        """
        Consulta campaigns por cuenta y rango de fechas
        Agrega insights diarios en métricas consolidadas
        """
        try:
            # Consultar TODOS los insights diarios del rango
            result = self.supabase.table('campaigns').select(
                'campaign_id, campaign_name, account_name, insights_date_start, insights_date_stop, '
                'spend, impressions, clicks, reach, frequency, cpm, cpc, ctr, '
                'campaign_status, campaign_objective, created_at'
            ).eq(
                'account_id', account_id
            ).gte(
                'insights_date_start', start_date
            ).lte(
                'insights_date_start', end_date
            ).execute()

            if not result.data:
                return None

            # Agrupar y sumar métricas por campaign_id usando pandas
            df = pd.DataFrame(result.data)

            # Agrupar por campaign_id y agregar métricas
            grouped = df.groupby('campaign_id').agg({
                'campaign_name': 'first',
                'account_name': 'first',
                'campaign_status': 'first',
                'campaign_objective': 'first',
                'insights_date_start': 'min',  # Primera fecha
                'insights_date_stop': 'max',   # Última fecha
                'spend': 'sum',                # Sumar inversión
                'impressions': 'sum',          # Sumar impresiones
                'clicks': 'sum',               # Sumar clics
                'reach': 'max',                # Máximo alcance (no se suma)
                'cpm': 'mean',                 # Promedio CPM
                'cpc': 'mean',                 # Promedio CPC
                'ctr': 'mean',                 # Promedio CTR
                'created_at': 'first'
            }).reset_index()

            # Convertir de vuelta a diccionario
            aggregated_data = grouped.to_dict('records')

            return aggregated_data

        except Exception as e:
            print(f"❌ Error consultando campaigns: {e}")
            return None

    def query_adsets_by_date_range(self, account_id, start_date, end_date):
        """
        Consulta adsets por cuenta y rango de fechas
        Agrega insights diarios en métricas consolidadas
        """
        try:
            result = self.supabase.table('adsets').select(
                'adset_id, adset_name, account_name, campaign_id, insights_date_start, insights_date_stop, '
                'spend, impressions, clicks, reach, frequency, cpm, cpc, ctr, '
                'adset_status, optimization_goal, daily_budget, lifetime_budget, created_at'
            ).eq(
                'account_id', account_id
            ).gte(
                'insights_date_start', start_date
            ).lte(
                'insights_date_start', end_date
            ).execute()

            if not result.data:
                return None

            # Agrupar y sumar métricas por adset_id
            df = pd.DataFrame(result.data)

            grouped = df.groupby('adset_id').agg({
                'adset_name': 'first',
                'account_name': 'first',
                'campaign_id': 'first',
                'adset_status': 'first',
                'optimization_goal': 'first',
                'daily_budget': 'first',
                'lifetime_budget': 'first',
                'insights_date_start': 'min',
                'insights_date_stop': 'max',
                'spend': 'sum',
                'impressions': 'sum',
                'clicks': 'sum',
                'reach': 'max',
                'cpm': 'mean',
                'cpc': 'mean',
                'ctr': 'mean',
                'created_at': 'first'
            }).reset_index()

            aggregated_data = grouped.to_dict('records')

            return aggregated_data

        except Exception as e:
            print(f"❌ Error consultando adsets: {e}")
            return None

    def query_ads_by_date_range(self, account_id, start_date, end_date):
        """
        Consulta ads por cuenta y rango de fechas
        Agrega insights diarios en métricas consolidadas
        """
        try:
            result = self.supabase.table('ads').select(
                'ad_id, ad_name, account_name, campaign_id, adset_id, insights_date_start, insights_date_stop, '
                'spend, impressions, clicks, reach, cpm, cpc, ctr, '
                'ad_status, created_at'
            ).eq(
                'account_id', account_id
            ).gte(
                'insights_date_start', start_date
            ).lte(
                'insights_date_start', end_date
            ).execute()

            if not result.data:
                return None

            # Agrupar y sumar métricas por ad_id
            df = pd.DataFrame(result.data)

            grouped = df.groupby('ad_id').agg({
                'ad_name': 'first',
                'account_name': 'first',
                'campaign_id': 'first',
                'adset_id': 'first',
                'ad_status': 'first',
                'insights_date_start': 'min',
                'insights_date_stop': 'max',
                'spend': 'sum',
                'impressions': 'sum',
                'clicks': 'sum',
                'reach': 'max',
                'cpm': 'mean',
                'cpc': 'mean',
                'ctr': 'mean',
                'created_at': 'first'
            }).reset_index()

            aggregated_data = grouped.to_dict('records')

            return aggregated_data

        except Exception as e:
            print(f"❌ Error consultando ads: {e}")
            return None

    def query_consolidado_by_date_range(self, account_id, start_date, end_date):
        """Consulta consolidada (campaigns + adsets + ads) por cuenta y rango de fechas"""
        try:
            print(f"📅 Consultando datos consolidados desde {start_date} hasta {end_date}")

            # Consultar campaigns
            campaigns = self.supabase.table('campaigns').select(
                'account_id, account_name, campaign_id, campaign_name, insights_date_start, '
                'insights_date_stop, spend, impressions, clicks, reach, cpm, cpc, ctr, '
                'campaign_status, campaign_objective, created_at'
            ).eq(
                'account_id', account_id
            ).gte(
                'insights_date_start', start_date
            ).lte(
                'insights_date_start', end_date
            ).execute()

            campaigns_data = []
            for item in campaigns.data:
                item['tipo'] = 'Campaign'
                item['id'] = item['campaign_id']
                item['name'] = item['campaign_name']
                item['status'] = item['campaign_status']
                item['objective'] = item['campaign_objective']
                campaigns_data.append(item)

            # Consultar adsets
            adsets = self.supabase.table('adsets').select(
                'account_id, account_name, adset_id, adset_name, insights_date_start, '
                'insights_date_stop, spend, impressions, clicks, reach, cpm, cpc, ctr, '
                'adset_status, optimization_goal, created_at'
            ).eq(
                'account_id', account_id
            ).gte(
                'insights_date_start', start_date
            ).lte(
                'insights_date_start', end_date
            ).execute()

            adsets_data = []
            for item in adsets.data:
                item['tipo'] = 'AdSet'
                item['id'] = item['adset_id']
                item['name'] = item['adset_name']
                item['status'] = item['adset_status']
                item['objective'] = item['optimization_goal']
                adsets_data.append(item)

            # Consultar ads
            ads = self.supabase.table('ads').select(
                'account_id, account_name, ad_id, ad_name, insights_date_start, '
                'insights_date_stop, spend, impressions, clicks, reach, cpm, cpc, ctr, '
                'ad_status, created_at'
            ).eq(
                'account_id', account_id
            ).gte(
                'insights_date_start', start_date
            ).lte(
                'insights_date_start', end_date
            ).execute()

            ads_data = []
            for item in ads.data:
                item['tipo'] = 'Ad'
                item['id'] = item['ad_id']
                item['name'] = item['ad_name']
                item['status'] = item['ad_status']
                item['objective'] = 'N/A'
                ads_data.append(item)

            # Combinar todos los datos
            all_data = campaigns_data + adsets_data + ads_data

            if not all_data:
                return None

            return all_data

        except Exception as e:
            print(f"❌ Error consultando datos consolidados: {e}")
            return None

    def create_excel_report(self, data, filename, report_type, account_info=None, summary_info=None):
        """Crea el reporte en formato Excel"""
        if not data:
            print("❌ No hay datos para generar el reporte")
            return False, None

        # Convertir datos a DataFrame
        df = pd.DataFrame(data)

        # Preparar datos para Excel
        if not df.empty:
            # Formatear columnas de dinero
            if 'spend' in df.columns:
                df['spend'] = pd.to_numeric(df['spend'], errors='coerce').fillna(0)

            # Formatear otras métricas numéricas
            numeric_columns = ['impressions', 'clicks', 'reach']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            # Formatear métricas decimales
            decimal_columns = ['cpm', 'cpc', 'ctr']
            for col in decimal_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # Crear archivo Excel
        filepath = os.path.join(self.reports_dir, filename)

        # Calcular métricas
        if report_type == 'consolidado' and 'tipo' in df.columns:
            df_for_totals = df[df['tipo'] == 'Campaign'].copy()
        else:
            df_for_totals = df

        total_spend = df_for_totals['spend'].sum() if 'spend' in df_for_totals.columns else 0
        total_impressions = df_for_totals['impressions'].sum() if 'impressions' in df_for_totals.columns else 0
        total_clicks = df_for_totals['clicks'].sum() if 'clicks' in df_for_totals.columns else 0
        avg_cpm = df_for_totals['cpm'].mean() if 'cpm' in df_for_totals.columns else 0
        avg_cpc = df_for_totals['cpc'].mean() if 'cpc' in df_for_totals.columns else 0
        avg_ctr = df_for_totals['ctr'].mean() if 'ctr' in df_for_totals.columns else 0

        try:
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # HOJA 1: INVERSIÓN TOTAL
                if summary_info and 'Fecha Inicio' in summary_info and 'Fecha Fin' in summary_info:
                    periodo_reporte = f"{summary_info['Fecha Inicio']} al {summary_info['Fecha Fin']}"
                elif 'insights_date_start' in df.columns and 'insights_date_stop' in df.columns:
                    fecha_min = df['insights_date_start'].min()
                    fecha_max = df['insights_date_stop'].max()
                    periodo_reporte = f"{fecha_min} al {fecha_max}"
                else:
                    periodo_reporte = 'Fechas recientes en BD'

                inversion_data = [
                    ['💰 INVERSIÓN TOTAL', f"${total_spend:,.2f}"],
                    ['📊 Total Elementos', len(df)],
                    ['👁️ Total Impresiones', f"{total_impressions:,}"],
                    ['👆 Total Clics', f"{total_clicks:,}"],
                    ['', ''],
                    ['📅 Período del Reporte', periodo_reporte],
                    ['🏢 Cuenta', summary_info.get('Cuenta', account_info.get('account_id') if account_info else 'N/A') if summary_info or account_info else 'N/A'],
                    ['📈 Tipo de Reporte', report_type.title()],
                    ['', ''],
                    ['🕒 Generado el', datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
                ]

                df_inversion = pd.DataFrame(inversion_data, columns=['Concepto', 'Valor'])
                df_inversion.to_excel(writer, sheet_name='💰 INVERSIÓN TOTAL', index=False)

                # HOJA 2: Datos Detallados
                if report_type == 'campaigns':
                    df_export = df[[
                        'account_name', 'campaign_name', 'insights_date_start', 'insights_date_stop',
                        'spend', 'impressions', 'clicks', 'reach', 'cpm', 'cpc', 'ctr',
                        'campaign_status', 'campaign_objective'
                    ]].copy()

                    df_export.columns = [
                        'Cuenta', 'Campaña', 'Fecha Inicio', 'Fecha Fin',
                        'Inversión ($)', 'Impresiones', 'Clics', 'Alcance', 'CPM', 'CPC', 'CTR',
                        'Estado', 'Objetivo'
                    ]

                elif report_type == 'adsets':
                    cols = ['account_name', 'adset_name', 'insights_date_start', 'insights_date_stop',
                            'spend', 'impressions', 'clicks', 'reach', 'cpm', 'cpc', 'ctr',
                            'adset_status', 'optimization_goal']

                    if 'daily_budget' in df.columns:
                        cols.extend(['daily_budget', 'lifetime_budget'])

                    df_export = df[cols].copy()

                    col_names = ['Cuenta', 'AdSet', 'Fecha Inicio', 'Fecha Fin',
                                'Inversión ($)', 'Impresiones', 'Clics', 'Alcance', 'CPM', 'CPC', 'CTR',
                                'Estado', 'Objetivo']

                    if 'daily_budget' in df.columns:
                        col_names.extend(['Presupuesto Diario', 'Presupuesto Lifetime'])

                    df_export.columns = col_names

                elif report_type == 'ads':
                    df_export = df[[
                        'account_name', 'ad_name', 'insights_date_start', 'insights_date_stop',
                        'spend', 'impressions', 'clicks', 'reach', 'cpm', 'cpc', 'ctr',
                        'ad_status'
                    ]].copy()

                    df_export.columns = [
                        'Cuenta', 'Anuncio', 'Fecha Inicio', 'Fecha Fin',
                        'Inversión ($)', 'Impresiones', 'Clics', 'Alcance', 'CPM', 'CPC', 'CTR',
                        'Estado'
                    ]

                elif report_type == 'consolidado':
                    # Para consolidado, crear hojas separadas
                    df_campaigns = df[df['tipo'] == 'Campaign'].copy()
                    df_adsets = df[df['tipo'] == 'AdSet'].copy()
                    df_ads = df[df['tipo'] == 'Ad'].copy()

                    worksheet = writer.book.create_sheet('Datos Detallados')
                    current_row = 1

                    # Escribir campaigns
                    if not df_campaigns.empty:
                        worksheet.cell(row=current_row, column=1, value='📊 CAMPAIGNS')
                        current_row += 1

                        headers = ['Cuenta', 'Campaña', 'Fecha Inicio', 'Fecha Fin',
                                   'Inversión ($)', 'Impresiones', 'Clics', 'Alcance', 'CPM', 'CPC', 'CTR',
                                   'Estado', 'Objetivo']
                        for col_idx, header in enumerate(headers, start=1):
                            worksheet.cell(row=current_row, column=col_idx, value=header)
                        current_row += 1

                        for _, row_data in df_campaigns[['account_name', 'name', 'insights_date_start', 'insights_date_stop',
                                                          'spend', 'impressions', 'clicks', 'reach', 'cpm', 'cpc', 'ctr',
                                                          'status', 'objective']].iterrows():
                            for col_idx, value in enumerate(row_data, start=1):
                                worksheet.cell(row=current_row, column=col_idx, value=value)
                            current_row += 1
                        current_row += 2

                    # Escribir adsets
                    if not df_adsets.empty:
                        worksheet.cell(row=current_row, column=1, value='📊 ADSETS')
                        current_row += 1

                        headers = ['Cuenta', 'AdSet', 'Fecha Inicio', 'Fecha Fin',
                                   'Inversión ($)', 'Impresiones', 'Clics', 'Alcance', 'CPM', 'CPC', 'CTR',
                                   'Estado', 'Objetivo']
                        for col_idx, header in enumerate(headers, start=1):
                            worksheet.cell(row=current_row, column=col_idx, value=header)
                        current_row += 1

                        for _, row_data in df_adsets[['account_name', 'name', 'insights_date_start', 'insights_date_stop',
                                                       'spend', 'impressions', 'clicks', 'reach', 'cpm', 'cpc', 'ctr',
                                                       'status', 'objective']].iterrows():
                            for col_idx, value in enumerate(row_data, start=1):
                                worksheet.cell(row=current_row, column=col_idx, value=value)
                            current_row += 1
                        current_row += 2

                    # Escribir ads
                    if not df_ads.empty:
                        worksheet.cell(row=current_row, column=1, value='📊 ADS')
                        current_row += 1

                        headers = ['Cuenta', 'Anuncio', 'Fecha Inicio', 'Fecha Fin',
                                   'Inversión ($)', 'Impresiones', 'Clics', 'Alcance', 'CPM', 'CPC', 'CTR',
                                   'Estado', 'Objetivo']
                        for col_idx, header in enumerate(headers, start=1):
                            worksheet.cell(row=current_row, column=col_idx, value=header)
                        current_row += 1

                        for _, row_data in df_ads[['account_name', 'name', 'insights_date_start', 'insights_date_stop',
                                                    'spend', 'impressions', 'clicks', 'reach', 'cpm', 'cpc', 'ctr',
                                                    'status', 'objective']].iterrows():
                            for col_idx, value in enumerate(row_data, start=1):
                                worksheet.cell(row=current_row, column=col_idx, value=value)
                            current_row += 1

                if report_type != 'consolidado':
                    df_export.to_excel(writer, sheet_name='Datos Detallados', index=False)

                # HOJA 3: Resumen
                summary_data = [
                    ['🎯 RESUMEN DEL REPORTE', ''],
                    ['💰 TOTAL GASTADO', f"${total_spend:,.2f}"],
                    ['📊 Total de Elementos', len(df)],
                    ['👁️ Total Impresiones', f"{total_impressions:,}"],
                    ['👆 Total Clics', f"{total_clicks:,}"],
                    ['💵 CPM Promedio', f"${avg_cpm:.2f}"],
                    ['💲 CPC Promedio', f"${avg_cpc:.2f}"],
                    ['📈 CTR Promedio', f"{avg_ctr:.4f}%"],
                    ['', ''],
                    ['📅 Generado el', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
                    ['🤖 Por', 'AutoRepCuentas - Django']
                ]

                df_summary = pd.DataFrame(summary_data, columns=['Concepto', 'Valor'])
                df_summary.to_excel(writer, sheet_name='Resumen', index=False)

            print(f"✅ Reporte Excel generado: {filepath}")
            print(f"📊 Total de registros: {len(df)}")
            print(f"💰 Inversión total: ${total_spend:,.2f}")

            return True, filepath

        except Exception as e:
            print(f"❌ Error generando archivo Excel: {e}")
            return False, None

    def generar_reporte(self, tipo, account_id, fecha_inicio, fecha_fin):
        """
        Genera el reporte según los parámetros especificados

        Args:
            tipo: 'campaigns', 'adsets', 'ads', 'consolidado'
            account_id: ID de la cuenta
            fecha_inicio: Fecha inicio (YYYY-MM-DD)
            fecha_fin: Fecha fin (YYYY-MM-DD)

        Returns:
            tuple: (success: bool, filepath: str or None)
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        print(f"🔄 Generando reporte {tipo} para cuenta {account_id} - {fecha_inicio} a {fecha_fin}")

        # Consultar datos según el tipo
        if tipo == 'campaigns':
            data = self.query_campaigns_by_date_range(account_id, fecha_inicio, fecha_fin)
            filename = f"reporte_campaigns_{account_id}_{fecha_inicio}_a_{fecha_fin}_{timestamp}.xlsx"
        elif tipo == 'adsets':
            data = self.query_adsets_by_date_range(account_id, fecha_inicio, fecha_fin)
            filename = f"reporte_adsets_{account_id}_{fecha_inicio}_a_{fecha_fin}_{timestamp}.xlsx"
        elif tipo == 'ads':
            data = self.query_ads_by_date_range(account_id, fecha_inicio, fecha_fin)
            filename = f"reporte_ads_{account_id}_{fecha_inicio}_a_{fecha_fin}_{timestamp}.xlsx"
        elif tipo == 'consolidado':
            data = self.query_consolidado_by_date_range(account_id, fecha_inicio, fecha_fin)
            filename = f"reporte_consolidado_{account_id}_{fecha_inicio}_a_{fecha_fin}_{timestamp}.xlsx"
        else:
            print(f"❌ Tipo de reporte no válido: {tipo}")
            return False, None

        if data is None or len(data) == 0:
            print("❌ No se encontraron datos para el reporte")
            return False, None

        # Información del resumen
        summary_info = {
            'Tipo de Reporte': f'{tipo.title()}',
            'Cuenta': account_id,
            'Fecha Inicio': fecha_inicio,
            'Fecha Fin': fecha_fin,
            'Fecha de generación': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        account_info = {'account_id': account_id}

        # Crear el reporte Excel
        return self.create_excel_report(data, filename, tipo, account_info, summary_info)
