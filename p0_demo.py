"""P0 — replicate the SDK hooks / policies mechanism (minimal runnable demo).

Run:  uv run --with google-antigravity python p0_demo.py

Demonstrates, against the real ``google.antigravity`` SDK (v0.1.4):
  * an ``Agent`` built from ``AgentConfig`` that carries a *declarative*
    safety ``policy`` + a ``response_schema`` (structured output) + a
    ``triggers.every(...)`` heartbeat — i.e. the full governance surface;
  * the SDK's priority model (Specific Deny > Specific Ask > Specific Allow)
    enforced via a ``pre_tool_call_decide`` hook;
  * visible APPROVE / DENY / ASK_USER decisions over mock actions, driven
    offline (no live model / API key needed) by calling the compiled hook
    directly.
"""

from __future__ import annotations

import asyncio

import pydantic

from google.antigravity import types, triggers, LocalAgentConfig
from google.antigravity.agent import Agent
from google.antigravity.hooks import hooks, policy


# --- response_schema: force structured output out of the agent ----------
class ActionDecision(pydantic.BaseModel):
    action: str
    intensity: int
    rationale: str


def _needs_consent(args: dict) -> bool:
    return bool(args.get("requireConsent")) and args.get("intensity", 0) >= 3


async def _ask_user(_tool_call: types.ToolCall) -> bool:
    # In a real deployment this would prompt a human; here we record + decline.
    print("        [ASK_USER] consent prompt raised -> (demo answers: no)")
    return False


def build_policies() -> list[policy.Policy]:
    """A declarative safety gate as a priority-ordered policy list.

    The SDK buckets these by specificity/safety, so a matching DENY always
    beats ASK_USER, which beats ALLOW.
    """
    return [
        # Hard cap: never exceed the caller's max intensity.
        policy.deny(
            "social_action",
            when=lambda a: a.get("intensity", 0) > a.get("maxIntensity", 10),
            name="cap_intensity",
        ),
        # Require explicit human consent for non-trivial interactions.
        policy.ask_user(
            "social_action",
            handler=_ask_user,
            when=_needs_consent,
            name="require_consent",
        ),
        # Otherwise approve.
        policy.allow("social_action", name="default_allow"),
    ]


def build_agent() -> tuple[Agent, LocalAgentConfig]:
    """Wire the declarative governance into a real Agent (no model run needed)."""

    async def heartbeat(ctx: triggers.TriggerContext) -> None:  # pragma: no cover
        await ctx.send("tick")

    config = LocalAgentConfig(
        system_instructions=(
            "You are an autonomous social agent. Every interaction you take is "
            "governed by a declarative safety gate; respect its decisions."
        ),
        policies=build_policies(),
        triggers=[triggers.every(3600, heartbeat)],
        response_schema=ActionDecision,
    )
    return Agent(config), config


async def run_decisions() -> list[str]:
    """Drive the compiled policy hook over mock actions; return a run log."""
    hook = policy.enforce(build_policies())
    log: list[str] = []

    cases = [
        ("calm low-intensity wave", {"intensity": 2, "maxIntensity": 5, "requireConsent": False}),
        ("over-cap visit (should DENY)", {"intensity": 8, "maxIntensity": 5, "requireConsent": False}),
        ("consent-required meetup (should ASK_USER)", {"intensity": 4, "maxIntensity": 6, "requireConsent": True}),
    ]
    for label, args in cases:
        consent_requested = {"v": False}

        # Re-bind the ask handler to capture whether consent was raised.
        async def ask(tc: types.ToolCall) -> bool:
            consent_requested["v"] = True
            return await _ask_user(tc)

        pols = [
            policy.deny("social_action", when=lambda a: a.get("intensity", 0) > a.get("maxIntensity", 10), name="cap_intensity"),
            policy.ask_user("social_action", handler=ask, when=_needs_consent, name="require_consent"),
            policy.allow("social_action", name="default_allow"),
        ]
        h = policy.enforce(pols)
        tc = types.ToolCall(name="social_action", args=args)
        res: hooks.HookResult = await h.run(hooks.HookContext(), tc)
        outcome = "ASK_USER" if consent_requested["v"] else ("APPROVE" if res.allow else "DENY")
        line = f"  {label:<42} -> {outcome:<9} allow={res.allow!s:<5} {res.message}"
        print(line)
        log.append(line.strip())
    return log


def main() -> None:
    print("=== P0: declarative safety gate on the Google Antigravity SDK ===")
    agent, config = build_agent()
    print(f"Agent built ({type(agent).__name__}). policies={len(config.policies)} "
          f"triggers={len(config.triggers)} response_schema={config.response_schema is not None}")
    print("\nPolicy decisions over mock actions (offline, no model call):")
    asyncio.run(run_decisions())
    print("\nP0 OK: APPROVE / DENY / ASK_USER all observable, decided declaratively.")


if __name__ == "__main__":
    main()
