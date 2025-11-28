#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SCHEDULER - AutoRepCuentas
Programador de tareas automaticas para renovacion de tokens
Se ejecuta cada Lunes a las 9:00 AM
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def renovar_tokens_job():
    """Job que se ejecuta para renovar tokens"""
    from .services.token_service import TokenService

    logger.info("=" * 50)
    logger.info("EJECUTANDO RENOVACION AUTOMATICA DE TOKENS")
    logger.info("=" * 50)

    try:
        token_service = TokenService()
        resultado = token_service.renovar_todos(solo_proximos_a_expirar=True)

        if resultado['status'] == 'success':
            stats = resultado['stats']
            logger.info(f"Renovacion completada:")
            logger.info(f"  - OK: {stats['ok']}")
            logger.info(f"  - Renovados: {stats['renovados']}")
            logger.info(f"  - Errores: {stats['errores']}")
        else:
            logger.error(f"Error en renovacion: {resultado.get('message')}")

    except Exception as e:
        logger.error(f"Error ejecutando renovacion de tokens: {str(e)}")


def start_scheduler():
    """Inicia el scheduler de tareas programadas"""
    scheduler = BackgroundScheduler()

    # Programar renovacion de tokens cada Lunes a las 9:00 AM
    scheduler.add_job(
        renovar_tokens_job,
        trigger=CronTrigger(
            day_of_week='mon',  # Lunes
            hour=9,             # 9:00 AM
            minute=0
        ),
        id='renovar_tokens_semanal',
        name='Renovar Tokens Meta Ads - Lunes 9:00 AM',
        replace_existing=True
    )

    scheduler.start()
    logger.info("Scheduler iniciado - Renovacion de tokens programada para Lunes 9:00 AM")

    return scheduler
