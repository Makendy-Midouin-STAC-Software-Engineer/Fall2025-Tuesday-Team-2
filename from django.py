from django.apps import AppConfig

class YourAppConfig(AppConfig):
    name = 'yourapp'

    def ready(self):
        import yourapp.signals