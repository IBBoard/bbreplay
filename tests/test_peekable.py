import pytest
from bbreplay import Peekable

CONTENTS = [1, 2, 3]


@pytest.fixture
def peekable():
    return Peekable(i for i in CONTENTS)


def test_peekable_works_with_next(peekable):
    assert next(peekable) == 1
    assert next(peekable) == 2
    assert next(peekable) == 3
    assert next(peekable, None) is None


def test_peekable_works_with_iterating(peekable):
    for i, val in enumerate(peekable):
        assert val == CONTENTS[i]


def test_peekable_raises_stop_iteration_exception(peekable):
    for _ in peekable:
        pass
    with pytest.raises(StopIteration):
        next(peekable)


def test_peek_then_fetch(peekable):
    assert peekable.peek() == 1
    assert next(peekable) == 1


def test_multiple_peeks_then_fetch(peekable):
    assert peekable.peek() == 1
    assert peekable.peek() == 1
    assert peekable.peek() == 1
    assert peekable.peek() == 1
    assert next(peekable) == 1


def test_fetch_updates_peek(peekable):
    assert peekable.peek() == 1
    next(peekable)
    assert peekable.peek() == 2


def test_peek_at_completion(peekable):
    for _ in peekable:
        pass
    assert peekable.peek() is None
