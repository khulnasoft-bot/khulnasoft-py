SECRET_KEY = "khulnasoft-django-tasks-tests"
USE_TZ = True
INSTALLED_APPS: list[str] = []
TASKS = {
    "default": {
        "BACKEND": "khulnasoft.integrations.django.KhulnasoftQueuesBackend",
        "QUEUES": ["default"],
        "OPTIONS": {
            "result_namespace": "django.results",
            "result_ttl_seconds": 120,
        },
    }
}
