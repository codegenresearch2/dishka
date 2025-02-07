from typing import Any, List, NewType, Type

from .dependency_source import Factory, Alias, Decorator
from .provider import Provider
from .scope import BaseScope


class Registry:
    __slots__ = ("scope", "_factories")

    def __init__(self, scope: BaseScope):
        self._factories = {}
        self.scope = scope

    def add_factory(self, factory: Factory):
        self._factories[factory.provides] = factory

    def get_factory(self, dependency: Any) -> Factory:
        return self._factories.get(dependency)


def make_registries(
        *providers: Provider,
        scopes: Type[BaseScope],
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
                scope = dep_scopes[source.source]
                dep_scopes[source.provides] = scope
                source = source.as_provider(scope)
            elif isinstance(source, Decorator):
                scope = dep_scopes[source.provides]
                registry = registries[scope]
                undecorated_type = NewType(
                    f"Old_{source.provides.__name__}",
                    source.provides,
                )
                old_factory = registry.get_factory(source.provides)
                old_factory.provides = undecorated_type
                registry.add_factory(old_factory)
                source = source.as_provider(
                    scope, undecorated_type,
                )
            else:
                raise ValueError("Unknown dependency source type")
            registries[scope].add_factory(source)

    return list(registries.values())
