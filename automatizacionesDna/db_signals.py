from django.db.backends.signals import connection_created
from django.dispatch import receiver

@receiver(connection_created)
def set_search_path(sender, connection, **kwargs):
    """
    Establece el search_path para cada conexión de Django
    """
    if connection.alias == 'default':
        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO django_reportes, public;")