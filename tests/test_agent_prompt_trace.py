from __future__ import annotations

from contextlib import contextmanager

from app import agent as agent_module


class ManagedPrompt:
    version = 3

    def compile(self, **variables: str) -> str:
        return (
            f"Feature={variables['feature']}\n"
            f"Docs={variables['docs']}\n"
            f"Question={variables['message']}"
        )


class RecordingLangfuseClient:
    def __init__(self) -> None:
        self.prompt = ManagedPrompt()
        self.span_updates: list[dict] = []

    def get_prompt(self, name: str, **kwargs):
        return self.prompt

    def update_current_span(self, **kwargs) -> None:
        self.span_updates.append(kwargs)


def test_agent_records_prompt_version_with_v4_observation_api(monkeypatch) -> None:
    monkeypatch.setenv("LANGFUSE_PROMPT_NAME", "day13-chat")
    monkeypatch.setenv("LANGFUSE_PROMPT_LABEL", "production")
    client = RecordingLangfuseClient()
    monkeypatch.setattr(agent_module, "get_langfuse_client", lambda: client)
    monkeypatch.setattr(agent_module, "tracing_enabled", lambda: True)

    propagated: list[dict] = []

    @contextmanager
    def record_attributes(**kwargs):
        propagated.append(kwargs)
        yield

    monkeypatch.setattr(agent_module, "propagate_attributes", record_attributes)

    agent = agent_module.LabAgent()
    agent_module.LabAgent.run.__wrapped__(
        agent,
        user_id="student-01",
        feature="qa",
        session_id="session-01",
        message="Explain traces",
        correlation_id="req-12345678",
    )

    span_update = client.span_updates[-1]
    assert span_update["metadata"] == {
        "doc_count": 1,
        "query_preview": "Explain traces",
        "prompt_name": "day13-chat",
        "prompt_label": "production",
        "prompt_version": "3",
        "prompt_source": "langfuse",
        "prompt_fetch_error": "",
    }
    assert span_update["version"] == "3"
    assert propagated[0]["metadata"]["correlation_id"] == "req-12345678"
    assert propagated[-1]["prompt"] is client.prompt


class RecordingObservation:
    def __init__(self, name: str, as_type: str, kwargs: dict) -> None:
        self.name = name
        self.as_type = as_type
        self.kwargs = kwargs
        self.updates: list[dict] = []

    def update(self, **kwargs):
        self.updates.append(kwargs)
        return self


def test_agent_creates_retrieval_and_generation_child_observations(monkeypatch) -> None:
    client = RecordingLangfuseClient()
    monkeypatch.setattr(agent_module, "get_langfuse_client", lambda: client)
    monkeypatch.setattr(agent_module, "tracing_enabled", lambda: True)

    observations: list[RecordingObservation] = []

    @contextmanager
    def record_observation(*, name: str, as_type: str = "span", **kwargs):
        observation = RecordingObservation(name, as_type, kwargs)
        observations.append(observation)
        yield observation

    monkeypatch.setattr(agent_module, "start_observation", record_observation)

    agent = agent_module.LabAgent()
    result = agent_module.LabAgent.run.__wrapped__(
        agent,
        user_id="student-01",
        feature="qa",
        session_id="session-01",
        message="Explain monitoring, email a@b.com",
        correlation_id="req-12345678",
    )

    assert [(o.name, o.as_type) for o in observations] == [
        ("retrieval", "retriever"),
        ("llm-generation", "generation"),
    ]
    retrieval, generation = observations
    assert "a@b.com" not in str(retrieval.kwargs) + str(retrieval.updates)
    assert retrieval.updates[-1]["output"]["doc_count"] == 1
    assert generation.kwargs["model"] == agent.model
    update = generation.updates[-1]
    assert update["usage_details"] == {"input": result.tokens_in, "output": result.tokens_out}
    assert update["cost_details"]["total"] == result.cost_usd
    assert "a@b.com" not in str(generation.kwargs) + str(generation.updates)
