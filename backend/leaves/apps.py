from django.apps import AppConfig


class LeavesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'leaves'
    verbose_name = 'Отпуска'

    def ready(self):
        import leaves.signals  # noqa: F401
