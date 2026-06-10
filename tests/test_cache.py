from rag.cache import PromptCache


def test_prompt_cache_round_trips_json_values(tmp_path):
    cache = PromptCache(tmp_path / "cache")

    cache.set("provider:model:prompt", {"text": "answer", "cached": False})

    assert cache.get("provider:model:prompt") == {"text": "answer", "cached": False}


def test_prompt_cache_accepts_structured_keys(tmp_path):
    cache = PromptCache(tmp_path / "cache")

    cache.put({"provider": "echo", "prompt": "hello"}, {"text": "world"})

    assert cache.get({"prompt": "hello", "provider": "echo"}) == {"text": "world"}
