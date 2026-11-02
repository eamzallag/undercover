import pytest
from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from agent import main
from backend.main import app
from backend.seed import seed


class StubModel(GenericFakeChatModel):
    """A chat model that gives scripted replies in place of a real model."""

    def bind_tools(self, tools, **kwargs):
        return self


def calls(*steps, reply="Done."):
    """Script a stub model: one tool call per step, then a final reply."""
    messages = [
        AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": str(n)}])
        for n, (name, args) in enumerate(steps)
    ]
    return StubModel(messages=iter([*messages, AIMessage(content=reply)]))


@pytest.fixture
def client(tmp_path, monkeypatch):
    """The backend on a fresh database, which the agent reaches in place of HTTP."""
    monkeypatch.setenv("UNDERCOVER_DB", str(tmp_path / "test.db"))
    seed()
    monkeypatch.setattr(main, "backend", lambda: TestClient(app))
    return TestClient(app)
