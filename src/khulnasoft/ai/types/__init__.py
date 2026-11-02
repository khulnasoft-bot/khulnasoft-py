# Import agent-layer submodules after ``events`` is fully loaded, since
# :mod:`.agent_events` and :mod:`.message_hydrator` import from
# :mod:`.events`.
from . import agent_events, events, media, message_hydrator, messages, tools, usage  # noqa: E402

# Backward compatibility: agent-layer event types and the message hydrator
# remain accessible via ``khulnasoft.ai.types.events.<Name>`` even though
# they now live in dedicated submodules.
for _name in (
    "Aggregator",
    "AgentEvent",
    "BaseEvent",
    "BuiltinToolDelta",
    "BuiltinToolEnd",
    "BuiltinToolResult",
    "BuiltinToolStart",
    "CancelledHookEvent",
    "Event",
    "FileEvent",
    "HookEvent",
    "MessageHydrator",
    "ModelEvent",
    "OmitEventMessages",
    "PendingHookEvent",
    "PartialToolCallResult",
    "ReasoningDelta",
    "ReasoningEnd",
    "ReasoningStart",
    "ResolvedHookEvent",
    "Retry",
    "RunBlocked",
    "RunStateTracker",
    "StreamEnd",
    "StreamStart",
    "TextDelta",
    "TextEnd",
    "TextStart",
    "ToolDelta",
    "ToolCallResult",
    "ToolEnd",
    "ToolStart",
    "_EventMessage",
    "_RetryFilter",
    "_serialize_event_message",
    "_serialize_omitting_event_messages",
    "_validate_event_message",
    "drop_discarded",
    "_replay_message_events",
):
    _source = (
        agent_events
        if hasattr(agent_events, _name)
        else (message_hydrator if hasattr(message_hydrator, _name) else events)
    )
    setattr(events, _name, getattr(_source, _name))

__all__ = [
    "agent_events",
    "events",
    "media",
    "message_hydrator",
    "messages",
    "tools",
    "usage",
]
