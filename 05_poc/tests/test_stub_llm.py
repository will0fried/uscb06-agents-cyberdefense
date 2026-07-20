"""Tests du provider stub : déterminisme et interface bind_tools/invoke."""
from langchain_core.messages import AIMessage, HumanMessage

from aica_agent.stub_llm import StubChatModel


def test_default_script_runs_isolate_then_terminate_then_finish():
    llm = StubChatModel().bind_tools([])
    msgs = [HumanMessage(content="go")]

    r1 = llm.invoke(msgs)
    assert isinstance(r1, AIMessage)
    assert r1.tool_calls
    assert r1.tool_calls[0]["name"] == "isolate_pod"

    r2 = llm.invoke(msgs)
    assert r2.tool_calls
    assert r2.tool_calls[0]["name"] == "terminate_5g_session"

    r3 = llm.invoke(msgs)
    assert not r3.tool_calls
    assert "MISSION_TERMINEE" in r3.content


def test_stub_is_idempotent_after_script_ends():
    llm = StubChatModel()
    for _ in range(3):
        llm.invoke([])  # consomme le script
    extra = llm.invoke([])
    # Dernier tour répété indéfiniment
    assert "MISSION_TERMINEE" in extra.content


def test_custom_script():
    llm = StubChatModel(scripted_steps=["bonjour", "au revoir"])
    assert llm.invoke([]).content == "bonjour"
    assert llm.invoke([]).content == "au revoir"
    assert llm.invoke([]).content == "au revoir"  # idempotent


def test_reset_replays_script():
    llm = StubChatModel(scripted_steps=["a", "b"])
    assert llm.invoke([]).content == "a"
    assert llm.invoke([]).content == "b"
    llm.reset()
    assert llm.invoke([]).content == "a"
