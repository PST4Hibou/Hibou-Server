import pytest
from pathlib import Path as PathlibPath


from helpers.decorators import SingletonMeta, singleton, Range


class TestSingleton:
    def test_clear(self):
        class MyClass:
            pass

        MyClass()
        SingletonMeta.clear()

        assert SingletonMeta._instances == {}


class TestSingletonDecorator:

    def test_singleton_decorator(self):
        @singleton
        class MyClass:
            def __init__(self):
                # No initialization needed for singleton decorator test
                pass

        instance1 = MyClass()
        instance2 = MyClass()

        assert instance1 is instance2
