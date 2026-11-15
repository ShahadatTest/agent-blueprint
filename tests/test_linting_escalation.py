"""Escalation consumes the same confidence field as the generated runtime."""

import pytest

from agent_blueprint.ir.compiler import compile_blueprint
from agent_blueprint.linting import lint_blueprint
from agent_blueprint.models.blueprint import BlueprintSpec


def findings(policy, produced="confidence"):
    raw = {
        "blueprint": {"name": "escalation-usage"},
        "state": {"fields": {produced: {"type": "float"}}},
        "graph": {
            "entry_point": "router",
            "nodes": {"router": {"type": "function"}, "human": {"type": "function"}},
            "edges": [{"from": "router", "to": "human"}, {"from": "human", "to": "END"}],
        },
        "contracts": {"nodes": {"router": {"produces": [produced]}}},
    }
    if policy is not None:
        raw["policies"] = {"escalation": policy}
    spec = BlueprintSpec.model_validate(raw)
    return [
        finding for finding in lint_blueprint(spec, compile_blueprint(spec))
        if finding.code == "unused-produced-field"
    ]


@pytest.mark.parametrize("threshold", [0.0, 0.75])
def test_low_confidence_policy_consumes_confidence(threshold):
    assert findings({"on_low_confidence": "human", "confidence_threshold": threshold}) == []


@pytest.mark.parametrize("policy", [None, {}, {"on_low_confidence": "human"}])
def test_inactive_escalation_does_not_consume_confidence(policy):
    assert len(findings(policy)) == 1


def test_escalation_does_not_consume_other_produced_fields():
    assert len(findings(
        {"on_low_confidence": "human", "confidence_threshold": 0.75},
        produced="other_confidence",
    )) == 1
