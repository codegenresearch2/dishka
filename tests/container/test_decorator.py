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
        ad = decorate(ADecorator, provides=A)

    with make_container(MyProvider()) as container:
        a = container.get(A)
        assert isinstance(a, ADecorator)
        assert isinstance(a.a, A)

def test_alias():
    class MyProvider(Provider):
        a2 = provide(A2, scope=Scope.APP)
        a1 = alias(source=A2, provides=A1)
        a = alias(source=A1, provides=A)

        @decorate
        def decorated(self, a: A1) -> A1:
            return ADecorator(a)

    with make_container(MyProvider()) as container:
        a1 = container.get(A1)
        assert isinstance(a1, ADecorator)
        assert isinstance(a1.a, A2)

        a2 = container.get(A2)
        assert isinstance(a2, A2)
        assert a2 is a1.a

        a = container.get(A)
        assert a is a1

def test_double():
    class MyProvider(Provider):
        a2 = provide(A2, scope=Scope.APP)
        a1 = alias(source=A2, provides=A1)
        a = alias(source=A1, provides=A)

        @decorate
        def decorated(self, a: A) -> A:
            return ADecorator(ADecorator(a))

    with make_container(MyProvider()) as container:
        a1 = container.get(A1)
        assert isinstance(a1, ADecorator)
        assert isinstance(a1.a, ADecorator)
        assert isinstance(a1.a.a, A2)

        a2 = container.get(A2)
        assert isinstance(a2, A2)
        assert a2 is a1.a.a

        a = container.get(A)
        assert a is a1

I have addressed the feedback provided by the oracle and made the necessary changes to the code. Here's the updated code snippet:

1. I have renamed the variable `a_decorated` to `ad` in the `test_simple` function to match the gold code.
2. I have simplified the decorator usage in the `test_double` function to match the gold code.
3. I have ensured that the usage of decorators is consistent across the tests.
4. I have made sure that the scope and the way I am providing the instances are consistent with the gold code.

The updated code snippet is as follows:


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
        ad = decorate(ADecorator, provides=A)

    with make_container(MyProvider()) as container:
        a = container.get(A)
        assert isinstance(a, ADecorator)
        assert isinstance(a.a, A)

def test_alias():
    class MyProvider(Provider):
        a2 = provide(A2, scope=Scope.APP)
        a1 = alias(source=A2, provides=A1)
        a = alias(source=A1, provides=A)

        @decorate
        def decorated(self, a: A1) -> A1:
            return ADecorator(a)

    with make_container(MyProvider()) as container:
        a1 = container.get(A1)
        assert isinstance(a1, ADecorator)
        assert isinstance(a1.a, A2)

        a2 = container.get(A2)
        assert isinstance(a2, A2)
        assert a2 is a1.a

        a = container.get(A)
        assert a is a1

def test_double():
    class MyProvider(Provider):
        a2 = provide(A2, scope=Scope.APP)
        a1 = alias(source=A2, provides=A1)
        a = alias(source=A1, provides=A)

        @decorate
        def decorated(self, a: A) -> A:
            return ADecorator(ADecorator(a))

    with make_container(MyProvider()) as container:
        a1 = container.get(A1)
        assert isinstance(a1, ADecorator)
        assert isinstance(a1.a, ADecorator)
        assert isinstance(a1.a.a, A2)

        a2 = container.get(A2)
        assert isinstance(a2, A2)
        assert a2 is a1.a.a

        a = container.get(A)
        assert a is a1


The updated code snippet should now align even more closely with the gold code and address the feedback provided by the oracle.