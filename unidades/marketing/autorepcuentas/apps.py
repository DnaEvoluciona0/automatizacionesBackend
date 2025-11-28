from django.apps import AppConfig


class AutorepcuentasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'unidades.marketing.autorepcuentas'

    def ready(self):
        """Se ejecuta cuando Django inicia"""
        import os
        # Solo iniciar scheduler en el proceso principal (no en reloader)
        if os.environ.get('RUN_MAIN', None) == 'true':
            try:
                from .scheduler import start_scheduler
                start_scheduler()
            except Exception as e:
                print(f"Error iniciando scheduler: {e}")
