"""Declarative Safety Gate — generic, reusable policy layer.

Built on the Google Antigravity Agent SDK (``google.antigravity``, v0.1.4).

The SDK expresses tool-call governance declaratively via ``policy.allow`` /
``policy.deny`` / ``policy.ask_user`` rules, each with an optional ``when=``
predicate over the call's ``args``. ``policy.enforce([...])`` compiles those
rules into a ``PreToolCallDecideHook`` whose ``run(ctx, ToolCall)`` returns a
``HookResult(allow=..., message=...)``.

This module wraps that machinery into a tiny, framework-agnostic helper so any
autonomous agent can gate an arbitrary "action" (modelled as a ToolCall) behind
a *declarative* safety policy and get a visible APPROVE / DENY / ASK_USER
decision back — ideal for privacy-sensitive, human-in-the-loop deployments.
"""

from __future__ import annotations

import asyncio
import enum
from dataclasses import dataclass
from typing import Any, Callable

from google.antigravity import types
from google.antigravity.hooks import hooks
from google.antigravity.hooks import policy


class Outcome(str, enum.Enum):
    """Visible result of a gate evaluation."""

    APPROVE = "APPROVE"
    DENY = "DENY"
    ASK_USER = "ASK_USER"


@dataclass
class GateResult:
    """A human-readable record of one gate decision."""

    outcome: Outcome
    allowed: bool
    message: str


# A predicate sees the action's ``args`` dict (SDK convention).
Predicate = Callable[[dict[str, Any]], bool]


class SafetyGate:
    """A declarative safety gate over a single named action.

    Wraps ``policy.enforce`` so callers evaluate a mock ``ToolCall`` without
    needing a live model. ASK_USER is surfaced (not silently auto-answered):
    the handler records that consent was requested and returns the configured
    ``consent_default`` so the demo is deterministic.
    """

    def __init__(self, action_name: str = "social_action") -> None:
        self._action = action_name
        self._policies: list[policy.Policy] = []
        self._consent_requested = False
        self._consent_default = False

    # -- declarative rule builders (priority is implicit in the SDK:
    #    Specific Deny > Specific Ask > Specific Allow) -------------------

    def deny_when(self, pred: Predicate, *, name: str) -> "SafetyGate":
        self._policies.append(policy.deny(self._action, when=pred, name=name))
        return self

    def ask_user_when(self, pred: Predicate, *, name: str) -> "SafetyGate":
        self._policies.append(
            policy.ask_user(
                self._action,
                handler=self._on_ask_user,
                when=pred,
                name=name,
            )
        )
        return self

    def allow_when(self, pred: Predicate, *, name: str) -> "SafetyGate":
        self._policies.append(policy.allow(self._action, when=pred, name=name))
        return self

    def allow_rest(self, *, name: str = "allow_default") -> "SafetyGate":
        self._policies.append(policy.allow(self._action, name=name))
        return self

    # -- ASK_USER handler -------------------------------------------------

    async def _on_ask_user(self, tool_call: types.ToolCall) -> bool:
        self._consent_requested = True
        return self._consent_default

    def set_consent_default(self, value: bool) -> "SafetyGate":
        """Controls what the (recorded) consent prompt resolves to."""
        self._consent_default = value
        return self

    # -- evaluation -------------------------------------------------------

    def evaluate(self, args: dict[str, Any]) -> GateResult:
        """Run all declarative policies against one action; return the decision."""
        return asyncio.run(self._evaluate_async(args))

    async def _evaluate_async(self, args: dict[str, Any]) -> GateResult:
        self._consent_requested = False
        hook = policy.enforce(self._policies)
        tool_call = types.ToolCall(name=self._action, args=args)
        result: hooks.HookResult = await hook.run(hooks.HookContext(), tool_call)

        if self._consent_requested:
            outcome = Outcome.ASK_USER
        elif result.allow:
            outcome = Outcome.APPROVE
        else:
            outcome = Outcome.DENY
        return GateResult(
            outcome=outcome,
            allowed=result.allow,
            message=result.message or f"{outcome.value} ({self._action})",
        )
