from dishka import Provider, Scope, alias, decorate, make_container, provide

class A:
    pass

class A1(A):
    pass

class A2(A1):
    pass

class ADecorator:
    def __init__(self, a: A):
        self.a = a

def test_simple():
    class MyProvider(Provider):
        a = provide(A, scope=Scope.APP)

    with make_container(MyProvider()) as container:
        a = container.get(A)
        a = decorate(ADecorator)(a)
        assert isinstance(a, ADecorator)
        assert isinstance(a.a, A)

def test_alias():
    class MyProvider(Provider):
        a2 = provide(A2, scope=Scope.APP)
        a1 = alias(source=A2, provides=A1)
        a = alias(source=A1, provides=A)

    with make_container(MyProvider()) as container:
        a2 = container.get(A2)
        a1 = container.get(A1)
        a1 = decorate(ADecorator)(a1)
        a = container.get(A)

        assert isinstance(a1, ADecorator)
        assert isinstance(a1.a, A2)

        assert isinstance(a2, A2)
        assert a2 is a1.a

        assert a is a1

def test_double():
    class MyProvider(Provider):
        a = provide(A, scope=Scope.APP)

    with make_container(MyProvider()) as container:
        a = container.get(A)
        a = decorate(ADecorator)(a)
        a = decorate(ADecorator)(a)
        assert isinstance(a, ADecorator)
        assert isinstance(a.a, ADecorator)
        assert isinstance(a.a.a, A)