from collections import defaultdict
from typing import Any, Dict

from dishka import Scope, make_container

class A:
    pass

class A1(A):
    pass

class A2(A1):
    pass

class ADecorator:
    def __init__(self, a: A):
        self.a = a

class MyFactories:
    def __init__(self):
        self.factory_depth = defaultdict(int)
        self.instances = {}

    def create_a(self) -> A:
        self.factory_depth['A'] += 1
        try:
            if 'A' not in self.instances:
                self.instances['A'] = A()
            return self.instances['A']
        finally:
            self.factory_depth['A'] -= 1

    def create_a1(self) -> A1:
        self.factory_depth['A1'] += 1
        try:
            if 'A1' not in self.instances:
                self.instances['A1'] = A1()
            return self.instances['A1']
        finally:
            self.factory_depth['A1'] -= 1

    def create_a2(self) -> A2:
        self.factory_depth['A2'] += 1
        try:
            if 'A2' not in self.instances:
                self.instances['A2'] = A2()
            return self.instances['A2']
        finally:
            self.factory_depth['A2'] -= 1

    def decorate_a(self, a: A) -> A:
        return ADecorator(a)

def test_simple():
    factories = MyFactories()
    with make_container(factories, scopes=Scope) as container:
        a = container.get(factories.create_a)
        assert isinstance(a, ADecorator)
        assert isinstance(a.a, A)

def test_alias():
    factories = MyFactories()
    with make_container(factories, scopes=Scope) as container:
        a2 = container.get(factories.create_a2)
        a1 = container.get(factories.create_a1)
        a = container.get(factories.create_a)

        a1 = factories.decorate_a(a1)
        assert isinstance(a1, ADecorator)
        assert isinstance(a1.a, A2)

        assert isinstance(a2, A2)
        assert a2 is a1.a

        assert a is a1