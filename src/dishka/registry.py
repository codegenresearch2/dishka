from typing import Any, List, NewType, Type

from .dependency_source import Alias, Decorator, DependencyFactory
from .provider import Provider
from .scope import BaseScope

class DependencyRegistry:
    __slots__ = ("scope", "_factories")

    def __init__(self, scope: BaseScope):
        self._factories = {}
        self.scope = scope

    def add_factory(self, factory: DependencyFactory):
        self._factories[factory.provides] = factory

    def get_factory(self, dependency: Any) -> DependencyFactory:
        return self._factories.get(dependency)

def create_registries(
        *providers: Provider, scopes: Type[BaseScope],
) -> List[DependencyRegistry]:
    dependency_scopes = {}
    for provider in providers:
        for source in provider.dependency_sources:
            if hasattr(source, "scope"):
                dependency_scopes[source.provides] = source.scope

    registries = {scope: DependencyRegistry(scope) for scope in scopes}

    for provider in providers:
        for source in provider.dependency_sources:
            if isinstance(source, DependencyFactory):
                scope = source.scope
            elif isinstance(source, Alias):
                scope = dependency_scopes[source.source]
                dependency_scopes[source.provides] = scope
                source = source.as_factory(scope)
            elif isinstance(source, Decorator):
                scope = dependency_scopes[source.provides]
                registry = registries[scope]
                undecorated_type = NewType(
                    f"Undecorated_{source.provides.__name__}",
                    source.provides,
                )
                old_factory = registry.get_factory(source.provides)
                old_factory.provides = undecorated_type
                registry.add_factory(old_factory)
                source = source.as_factory(
                    scope, undecorated_type,
                )
            else:
                raise ValueError("Unknown dependency source type")
            registries[scope].add_factory(source)

    return list(registries.values())