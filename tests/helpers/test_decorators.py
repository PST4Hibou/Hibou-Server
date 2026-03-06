import pytest
from pathlib import Path as PathlibPath




from helpers.decorators import SingletonMeta, singleton, Range

class TestSingletonMeta:
    
    def test_singleton_same_instance(self):
        class Config(metaclass=SingletonMeta):
            def __init__(self):
                self.value = 42
        
        c1 = Config()
        c2 = Config()
        c3 = Config()
        
        assert c1 is c2 is c3
        assert c1.value == 42
    
    def test_singleton_different_classes(self):
        class ConfigA(metaclass=SingletonMeta):
            pass
    
        class ConfigB(metaclass=SingletonMeta):
            pass
        
        a1 = ConfigA()
        a2 = ConfigA()
        b1 = ConfigB()
        
        assert a1 is a2
        assert a1 is not b1
        assert b1 is ConfigB()

    def test_singleton_clear_resets(self):
        class TestClass(metaclass=SingletonMeta):
            pass
        
        first = TestClass()
        SingletonMeta.clear()
        second = TestClass()
        
        assert first is not second
    
    def test_singleton_args_kwargs_preserved(self):

        class Config(metaclass=SingletonMeta):
            def __init__(self, name, value=0):
                self.name = name
                self.value = value
        
        config = Config("test", value=123)
        assert config.name == "test"
        assert config.value == 123

class TestSingletonDecorator:
    
    def test_singleton_decorator_fails(self):
        @singleton
        class Cache:
            pass
        
        c1 = Cache()
        c2 = Cache()
        assert c1 is c2 


@pytest.fixture(autouse=True) 
def cleanup_singletons():

    yield
    SingletonMeta.clear()