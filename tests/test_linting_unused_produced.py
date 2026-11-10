"""Tests for unused-produced-field, incl. policies.escalation consumption."""

from agent_blueprint.ir.compiler import compile_blueprint
from agent_blueprint.linting import lint_blueprint
from agent_blueprint.models.blueprint import BlueprintSpec


def lint(raw: dict):
    spec = BlueprintSpec.model_validate(raw)
    return [
        f
        for f in lint_blueprint(spec, compile_blueprint(spec))
        if f.code == "unused-produced-field"
    ]


def _base(*, extra: dict | None = None) -> dict:
    raw = {
        "blueprint": {"name": "produced"},
        "state": {
            "fields": {
                "messages": {"type": "list[message]", "reducer": "append"},
                "confidence": {"type": "number", "nullable": True},
            }
        },
        "graph": {
            "entry_point": "router",
            "nodes": {
                "router": {"type": "function"},
                "esc": {"type": "function"},
            },
            "edges": [
                {"from": "router", "to": "END"},
                {"from": "esc", "to": "END"},
            ],
        },
        "contracts": {
            "nodes": {
                "router": {"produces": ["confidence"]},
            }
        },
    }
    if extra:
        raw.update(extra)
    return raw


_ESCALATION = {
    "policies": {
        "escalation": {
            "on_low_confidence": "esc",
            "confidence_threshold": 0.7,
        }
    }
}


class TestUnusedProducedField:
    def test_warns_when_confidence_is_unused(self):
        findings = lint(_base())
        assert len(findings) == 1
        assert "confidence" in findings[0].message
        assert findings[0].location == "contracts.nodes.router.produces"

    def test_escalation_policy_counts_confidence_as_consumed(self):
        findings = lint(_base(extra=_ESCALATION))
        assert findings == []
