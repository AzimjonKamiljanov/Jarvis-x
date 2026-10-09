"""Tests for model routing and task complexity classification."""

from jarvis.ai.model_router import ModelRouter, TaskComplexity


def test_classify_task_trivial():
    router = ModelRouter()
    assert router.classify_task("hi") == TaskComplexity.TRIVIAL
    assert router.classify_task("salom") == TaskComplexity.TRIVIAL
    assert router.classify_task("yes") == TaskComplexity.TRIVIAL


def test_classify_task_complex():
    router = ModelRouter()
    res = router.classify_task("Explain the theory of relativity in detail.")
    assert res == TaskComplexity.COMPLEX
    res2 = router.classify_task("Can you write a python script to scrape a website?")
    assert res2 == TaskComplexity.COMPLEX


def test_classify_task_moderate():
    router = ModelRouter()
    # Length > 8, no complex keywords
    res = router.classify_task("The weather is really nice today, isn't it beautiful?")
    assert res == TaskComplexity.MODERATE


def test_select_model():
    router = ModelRouter()

    # Should pick fastest model for trivial task
    model_cfg = router.select_model("hi")
    # Expected lowest latency
    fastest = min(router._registry, key=lambda m: m.latency_ms)
    assert model_cfg.name == fastest.name

    # Should pick highest quality for complex task
    model_cfg = router.select_model("Explain the universe.")
    highest_quality = max(router._registry, key=lambda m: m.quality_score)
    assert model_cfg.name == highest_quality.name


def test_force_offline_routing():
    router = ModelRouter()
    model_cfg = router.select_model("hello", force_offline=True)
    assert model_cfg.offline_capable is True
    assert model_cfg.provider == "ollama"
