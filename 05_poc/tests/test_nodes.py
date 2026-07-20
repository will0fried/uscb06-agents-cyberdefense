"""
Tests unitaires des nœuds AICA.

On teste séparément sensing, perception, world_model - le LLM-dépendant
(decision) est testé via le test d'intégration avec le stub.
"""
from aica_agent.nodes import sensing_node, perception_node, world_model_node


def _empty_state(**overrides):
    """Construit un AgentState minimal avec champs requis."""
    base = {
        "messages": [],
        "raw_observations": [],
        "structured_facts": [],
        "world_state": {},
        "planned_action": None,
        "executed_actions": [],
        "step_count": 0,
        "objective": "test",
        "finished": False,
    }
    base.update(overrides)
    return base


# ---------- sensing ----------

def test_sensing_collects_two_sources():
    """Sensing doit produire deux sources : k8s.pods et k8s.events."""
    out = sensing_node(_empty_state())
    assert "raw_observations" in out
    sources = {o["source"] for o in out["raw_observations"]}
    assert sources == {"k8s.pods", "k8s.events"}


def test_sensing_pods_have_expected_fields():
    out = sensing_node(_empty_state())
    pods = next(o["data"] for o in out["raw_observations"] if o["source"] == "k8s.pods")
    assert pods, "sensing devrait remonter au moins un pod"
    for p in pods:
        assert {"name", "namespace", "status", "restarts", "node"} <= set(p.keys())


# ---------- perception ----------

def test_perception_extracts_warnings_as_alerts():
    """Tout événement Warning du sensing doit devenir un fait 'alert'."""
    state = _empty_state(raw_observations=[{
        "source": "k8s.events",
        "data": [
            {"type": "Warning", "reason": "X", "object": "pod/foo", "message": "boom"},
            {"type": "Normal",  "reason": "Y", "object": "pod/bar", "message": "calme"},
        ],
    }])
    out = perception_node(state)
    facts = out["structured_facts"]
    assert len(facts) == 1
    assert facts[0]["kind"] == "alert"
    assert facts[0]["subject"] == "pod/foo"


def test_perception_flags_pods_with_restarts():
    state = _empty_state(raw_observations=[{
        "source": "k8s.pods",
        "data": [
            {"name": "stable", "restarts": 0},
            {"name": "flaky",  "restarts": 3},
        ],
    }])
    out = perception_node(state)
    instabilities = [f for f in out["structured_facts"] if f["kind"] == "instability"]
    assert len(instabilities) == 1
    assert instabilities[0]["subject"] == "flaky"


# ---------- world model ----------

def test_world_model_marks_subjects_with_two_alerts_as_suspects():
    state = _empty_state(structured_facts=[
        {"kind": "alert", "subject": "pod/foo", "detail": "1"},
        {"kind": "alert", "subject": "pod/foo", "detail": "2"},
        {"kind": "alert", "subject": "pod/bar", "detail": "3"},
    ])
    out = world_model_node(state)
    assert "pod/foo" in out["world_state"]["suspects"]
    assert "pod/bar" not in out["world_state"]["suspects"]


def test_world_model_aggregates_total_facts():
    state = _empty_state(structured_facts=[
        {"kind": "alert", "subject": "x", "detail": "."},
        {"kind": "instability", "subject": "y", "detail": "."},
    ])
    out = world_model_node(state)
    assert out["world_state"]["total_facts"] == 2
