import pytest
from pathlib import Path as PathlibPath


from helpers.decorators import SingletonMeta, singleton, Range


class TestSingletonDecorator:

    def test_clear(self):
        class MyClass:
            pass

        MyClass()
        SingletonMeta.clear()

        assert SingletonMeta._instances == {}

    def test_singleton_decorator(self):
        @singleton
        class MyClass:
            def __init__(self, value=50):
                self.value = value

        instance1 = MyClass()
        instance2 = MyClass()
        

        assert instance1 is instance2
        instance2.value = 40
        assert instance1.value == 40
