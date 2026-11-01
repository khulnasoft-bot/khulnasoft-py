"""Celery integration for Khulnasoft Queue Service."""

from kombu.transport import TRANSPORT_ALIASES, virtual

from celery.app import backends as celery_backends
from celery.app.defaults import DEFAULTS as CELERY_DEFAULTS
from khulnasoft.queue import CommunicationError, TokenResolutionError, UnauthorizedError

from ._broker import (
    AutoChannel,
    PollChannel,
    PushChannel,
    _configure_existing_app_defaults,
    _install_app_finalize_hook,
    _install_connection_transport_options_hook,
    _register_existing_app_queues,
    _set_default_broker_set_by_installer,
    register_celery_app_queues,
)
from ._result_backend import DEFAULT_RESULT_BACKEND_ALIAS, KhulnasoftRuntimeCacheBackend
from .version import __version__

_DEFAULT_CONNECTION_PARAMS = {"hostname": None, "port": None}
# Token resolution depends on request-scoped OIDC context that may be
# momentarily unavailable on Celery-owned threads (and refreshes with the next
# push delivery). A cached token can also expire between local resolution and the
# remote request, producing UnauthorizedError once before the next resolution
# evicts it. CommunicationError is ordinary network trouble. Treat all three as
# recoverable connection failures so the Celery consumer restarts instead of
# shutting the worker down permanently. Kombu's own connection_errors use
# amqp.exceptions.ConnectionError, not the builtin, so CommunicationError must be
# listed explicitly.
_CONNECTION_ERRORS = (
    *virtual.Transport.connection_errors,
    TokenResolutionError,
    UnauthorizedError,
    CommunicationError,
)


class KhulnasoftQueueTransport(virtual.Transport):
    """Kombu transport that auto-selects Khulnasoft Queue Service delivery mode.

    The transport uses push delivery when running on Khulnasoft and polling otherwise.
    It is registered as ``khulnasoft://`` by ``install_khulnasoft_celery_integration``.
    """

    Channel = AutoChannel
    driver_type = "khulnasoft"
    driver_name = "Khulnasoft Queue Service"
    default_connection_params = _DEFAULT_CONNECTION_PARAMS
    connection_errors = _CONNECTION_ERRORS


class KhulnasoftQueuePollTransport(virtual.Transport):
    """Kombu transport that always polls Khulnasoft Queue Service.

    It is registered as ``khulnasoft-poll://`` by
    ``install_khulnasoft_celery_integration`` and is intended for workers that cannot
    receive Khulnasoft Queue push deliveries.
    """

    Channel = PollChannel
    driver_type = "khulnasoft"
    driver_name = "Khulnasoft Queue Service (poll)"
    default_connection_params = _DEFAULT_CONNECTION_PARAMS
    connection_errors = _CONNECTION_ERRORS


class KhulnasoftQueuePushTransport(virtual.Transport):
    """Kombu transport that receives Khulnasoft Queue Service push deliveries.

    It is registered as ``khulnasoft-push://`` by
    ``install_khulnasoft_celery_integration`` and requires the app's queues to be
    registered as Khulnasoft Queue topic subscribers.
    """

    Channel = PushChannel
    driver_type = "khulnasoft"
    driver_name = "Khulnasoft Queue Service (push)"
    default_connection_params = _DEFAULT_CONNECTION_PARAMS
    connection_errors = _CONNECTION_ERRORS


def install_khulnasoft_celery_integration(
    *,
    register_queues: bool = True,
    set_default_broker: bool = True,
    set_default_result_backend: bool = True,
) -> None:
    """Register Khulnasoft Queue Service as a Celery broker integration.

    Register ``khulnasoft://``. ``khulnasoft-poll://``, and ``khulnasoft-push://`` as valid
    Kombu transport aliases for automatic push/poll, always-poll, and always-push modes
    correspondingly. When
    *set_default_broker* is ``True`` (default), also set Celery default broker URL to ``khulnasoft://``
    when no broker is configured already. When *set_default_result_backend* is ``True`` (default),
    set Celery's default result backend to ``khulnasoft-runtime-cache://`` when no result backend is
    configured already. When *register_queues* is `True` (default), automatically register all
    Celery queues as Khulnasoft Queues topic subscribers.

    This also registers ``khulnasoft-runtime-cache://`` as the Khulnasoft Runtime Cache
    result backend alias.
    """
    TRANSPORT_ALIASES["khulnasoft"] = (
        f"{KhulnasoftQueueTransport.__module__}:{KhulnasoftQueueTransport.__name__}"
    )
    TRANSPORT_ALIASES["khulnasoft-poll"] = (
        f"{KhulnasoftQueuePollTransport.__module__}:{KhulnasoftQueuePollTransport.__name__}"
    )
    TRANSPORT_ALIASES["khulnasoft-push"] = (
        f"{KhulnasoftQueuePushTransport.__module__}:{KhulnasoftQueuePushTransport.__name__}"
    )
    celery_backends.BACKEND_ALIASES[DEFAULT_RESULT_BACKEND_ALIAS] = (
        f"{KhulnasoftRuntimeCacheBackend.__module__}:{KhulnasoftRuntimeCacheBackend.__name__}"
    )
    default_broker_url = "khulnasoft://" if set_default_broker else None
    default_result_backend = (
        f"{DEFAULT_RESULT_BACKEND_ALIAS}://" if set_default_result_backend else None
    )
    if set_default_broker and CELERY_DEFAULTS.get("broker_url") is None:
        CELERY_DEFAULTS["broker_url"] = default_broker_url
        _set_default_broker_set_by_installer(value=True)
    if set_default_result_backend and CELERY_DEFAULTS.get("result_backend") is None:
        CELERY_DEFAULTS["result_backend"] = default_result_backend
    _install_connection_transport_options_hook()
    _install_app_finalize_hook(register_queues=register_queues)
    _configure_existing_app_defaults(
        broker_url=default_broker_url,
        result_backend=default_result_backend,
    )
    if register_queues:
        _register_existing_app_queues()


__all__ = [
    "KhulnasoftQueuePollTransport",
    "KhulnasoftQueuePushTransport",
    "KhulnasoftQueueTransport",
    "KhulnasoftRuntimeCacheBackend",
    "__version__",
    "install_khulnasoft_celery_integration",
    "register_celery_app_queues",
]
