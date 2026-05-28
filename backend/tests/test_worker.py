from worker import _reset_rope_cache


class _FakeModule:
    """Stand-in for an nn.Module that may hold a lazily-cached freqs_cis."""

    def __init__(self, freqs_cis="unset"):
        if freqs_cis != "unset":
            self.freqs_cis = freqs_cis


class _FakeModel:
    def __init__(self, submodules):
        self._submodules = submodules

    def modules(self):
        return iter([self, *self._submodules])


def test_reset_rope_cache_clears_populated_caches():
    rope = _FakeModule(freqs_cis="tensor-on-cuda0")
    other = _FakeModule()  # no freqs_cis attribute at all
    model = _FakeModel([rope, other])

    count = _reset_rope_cache(model)

    assert rope.freqs_cis is None
    assert count == 1


def test_reset_rope_cache_ignores_already_empty_caches():
    rope = _FakeModule(freqs_cis=None)
    model = _FakeModel([rope])

    count = _reset_rope_cache(model)

    assert rope.freqs_cis is None
    assert count == 0
