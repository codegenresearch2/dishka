from typing import Any, List, Type, Dict
from collections import defaultdict
from .dependency_source import Alias, Decorator, Factory
from .provider import Provider
from .scope import BaseScope


class Registry:
    __slots__ = ("scope", "_factories")

    def __init__(self, scope: BaseScope):
        self.scope = scope
        self._factories: Dict[Type, Factory] = {}

    def add_provider(self, provider: Factory):
        self._factories[provider.provides] = provider

    def get_provider(self, dependency: Any) -> Factory:
        return self._factories.get(dependency)


def make_registries(
        *providers: Provider, scopes: Type[BaseScope]
) -> List[Registry]:
    dep_scopes = {}
    for provider in providers:
        for source in provider.dependency_sources:
            if hasattr(source, "scope"):
                dep_scopes[source.provides] = source.scope

    registries = {scope: Registry(scope) for scope in scopes}

    for provider in providers:
        for source in provider.dependency_sources:
            if isinstance(source, Factory):
                scope = source.scope
            elif isinstance(source, Alias):
                scope = dep_scopes.get(source.source)
                if not hasattr(source, "as_factory"):
                    raise AttributeError("Alias objects must have an 'as_factory' method")
                source = source.as_factory(scope)
                dep_scopes[source.provides] = scope
            elif isinstance(source, Decorator):
                scope = dep_scopes.get(source.provides)
                if not hasattr(source, "as_factory"):
                    raise AttributeError("Decorator objects must have an 'as_factory' method")
                source = source.as_factory(scope)
                undecorated_type = type(f"Old_{source.provides.__name__}", (source.provides,), {})
                old_provider = registries[scope].get_provider(source.provides)
                old_provider.provides = undecorated_type
                registries[scope].add_provider(old_provider)
                source = source.as_factory(scope, undecorated_type)
            else:
                raise ValueError("Unknown dependency source type")
            registries[scope].add_provider(source)

    return list(registries.values())