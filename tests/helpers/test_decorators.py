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

class TestRangeDataclass:
    
    def test_range_creation(self):

        r = Range(min=1, max=10)
        assert r.min == 1
        assert r.max == 10
    
    def test_range_frozen_immutable(self):
        r = Range(min=0, max=100)
        with pytest.raises(AttributeError):
            r.min = 5 # type: ignore[attr-defined]
    
    def test_range_invalid_values(self):
        r1 = Range(min=10, max=1)  
        r2 = Range(min=-5, max=0) 
        assert r1.min == 10
        assert r2.max == 0

@pytest.fixture(autouse=True) 
def cleanup_singletons():

    yield
    SingletonMeta.clear()