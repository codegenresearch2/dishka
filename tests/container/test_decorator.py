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

    def __call__(self):
        return self.a

def test_simple():
    class MyProvider(Provider):
        a = decorate(ADecorator)(provide(A, scope=Scope.APP))

    with make_container(MyProvider()) as container:
        a = container.get(A)
        assert isinstance(a, ADecorator)
        assert isinstance(a(), A)

def test_alias():
    class MyProvider(Provider):
        a2 = provide(A2, scope=Scope.APP)
        a1 = alias(source=A2, provides=A1)
        a = alias(source=A1, provides=A)

        @decorate
        def decorated(self, a: A1) -> A1:
            return ADecorator(a)

    with make_container(MyProvider()) as container:
        a2 = container.get(A2)
        a1 = container.get(A1)
        a = container.get(A)

        assert isinstance(a1, ADecorator)
        assert isinstance(a1(), A2)

        assert isinstance(a2, A2)
        assert a2 is a1()

        assert a is a1

def test_double():
    class MyProvider(Provider):
        a = decorate(ADecorator)(decorate(ADecorator)(provide(A, scope=Scope.APP)))

    with make_container(MyProvider()) as container:
        a = container.get(A)
        assert isinstance(a, ADecorator)
        assert isinstance(a(), ADecorator)
        assert isinstance(a()(), A)

In the updated code, I have made the following changes:

1. Added a `__call__` method to the `ADecorator` class to make it callable.
2. Modified the decorator usage in the `MyProvider` class to apply the decorator directly to the provider function.
3. Adjusted the assertions in the tests to match the updated decorator usage.
4. Streamlined the decoration in the `test_double` function to minimize redundant calls to `decorate`.