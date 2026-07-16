from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'core'
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        # Auto-create the singleton Profile row after migrations so the
        # admin change form always has an object to edit (fixes "can't
        # update Profile" on hosts like PythonAnywhere where the DB starts empty).
        from . import signals  # noqa: F401
