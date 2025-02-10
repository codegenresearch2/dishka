def test_simple():
    class MyFactories(Provider):
        a = provide(A, scope=Scope.APP)

        @decorate(source=A, provides=A)
        def decorate_a(self, a: A) -> A:
            return ADecorator(a)

    with make_container(MyFactories(), scopes=Scope) as container:
        a = container.get(A)
        assert isinstance(a, ADecorator)
        assert isinstance(a.a, A)

def test_alias():
    class MyFactories(Provider):
        a2 = provide(A2, scope=Scope.APP)

        @alias(source=A2, provides=A1)
        def alias_a2_to_a1(self, a2: A2) -> A1:
            return a2

        @alias(source=A1, provides=A)
        def alias_a1_to_a(self, a1: A1) -> A:
            return a1

        @decorate(source=A1, provides=A1)
        def decorate_a1(self, a1: A1) -> A1:
            return ADecorator(a1)

    with make_container(MyFactories(), scopes=Scope) as container:
        a2 = container.get(A2)
        a1 = container.get(A1)
        a = container.get(A)

        assert isinstance(a1, ADecorator)
        assert isinstance(a1.a, A2)

        assert isinstance(a2, A2)
        assert a2 is a1.a

        assert a is a1