# khulnasoft-django-tasks

Django task backend backed by Khulnasoft Queue Service. The installer uses
`KhulnasoftQueuesBackend` as Django's default task backend when no `TASKS`
backends are configured and registers generated queue subscribers.

Register push subscribers during application startup:

```python
from khulnasoft.integrations.django import install_khulnasoft_django_task_integration

install_khulnasoft_django_task_integration()
```

No `TASKS` setting is required. Configure one explicitly to customize the
backend or to use a different backend:

```python
TASKS = {
    "default": {
        "BACKEND": "khulnasoft.integrations.django.KhulnasoftQueuesBackend",
        "QUEUES": ["default"],
        "OPTIONS": {
            "result_namespace": "django-task-results",
            "result_ttl_seconds": 86400,
        },
    },
}
```

Declare the module that loads your Django application in `pyproject.toml` so
Khulnasoft generates a queue subscriber function:

```toml
[[tool.khulnasoft.subscribers]]
entrypoint = "my_project.wsgi"
```

No manual queue endpoint is required.

Task result state is stored in Khulnasoft Runtime Cache. Results are cache-backed
and expire according to `result_ttl_seconds`; they are not durable storage.

This package depends on Django, `khulnasoft-queue`, and `khulnasoft-cache`.
