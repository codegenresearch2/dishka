from collections import defaultdict
from typing import Type, TypeVar

from dishka import Provider, Scope, alias, make_container, provide

T = TypeVar('T')

class A:
    pass

class A1(A):
    pass

class A2(A1):
    pass

class ADecorator:
    def __init__(self, a: A):
        self.a = a

class MyProvider(Provider):
    factory_methods = defaultdict(dict)

    @classmethod
    def register_factory(cls, provides: Type[T], scope: Scope) -> callable:
        def decorator(func: callable) -> callable:
            cls.factory_methods[provides][scope] = func
            return func
        return decorator

    @register_factory(A, Scope.APP)
    @provide(scope=Scope.APP)
    def create_a(self) -> A:
        return A()

    @register_factory(ADecorator, Scope.APP)
    @provide(scope=Scope.APP, provides=A)
    def create_decorated_a(self, a: A) -> ADecorator:
        return ADecorator(a)

    @register_factory(A2, Scope.APP)
    @provide(scope=Scope.APP)
    def create_a2(self) -> A2:
        return A2()

    @register_factory(A1, Scope.APP)
    @alias(source=A2, provides=A1)
    def alias_a1_to_a2(self, a2: A2) -> A1:
        return a2

    @register_factory(A, Scope.APP)
    @alias(source=A1, provides=A)
    def alias_a_to_a1(self, a1: A1) -> A:
        return a1

def test_simple():
    with make_container(MyProvider()) as container:
        a = container.get(A)
        assert isinstance(a, ADecorator)
        assert isinstance(a.a, A)

def test_alias():
    with make_container(MyProvider()) as container:
        a1 = container.get(A1)
        assert isinstance(a1, ADecorator)
        assert isinstance(a1.a, A2)

        a2 = container.get(A2)
        assert isinstance(a2, A2)
        assert a2 is a1.a

        a = container.get(A)
        assert a is a1