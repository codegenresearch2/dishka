from typing import Any, List, Type

from .dependency_source import Alias, Decorator, Factory
from .provider import Provider
from .scope import BaseScope


class Registry:
    __slots__ = ("scope", "_providers")

    def __init__(self, scope: BaseScope):
        self._providers = {}
        self.scope = scope

    def add_provider(self, provider: Factory):
        self._providers[provider.provides] = provider

    def get_provider(self, dependency: Any):
        return self._providers.get(dependency)


def create_registries(
        *providers: Provider, scope_types: Type[BaseScope]
) -> List[Registry]:
    dependency_scopes = {}
    for provider in providers:
        for source in provider.dependency_sources:
            if hasattr(source, "scope"):
                dependency_scopes[source.provides] = source.scope

    registries = {scope: Registry(scope) for scope in scope_types}

    for provider in providers:
        for source in provider.dependency_sources:
            if isinstance(source, Factory):
                scope = source.scope
            elif isinstance(source, Alias):
                scope = dependency_scopes[source.source]
                dependency_scopes[source.provides] = scope
                source = source.as_provider(scope)
            elif isinstance(source, Decorator):
                scope = dependency_scopes[source.provides]
                registry = registries[scope]
                undecorated_type = type(f"Old_{source.provides.__name__}", (source.provides,), {})
                old_provider = registry.get_provider(source.provides)
                old_provider.provides = undecorated_type
                registry.add_provider(old_provider)
                source = source.as_provider(scope, undecorated_type)
            else:
                raise ValueError("Unknown dependency source type")
            registries[scope].add_provider(source)

    return list(registries.values())