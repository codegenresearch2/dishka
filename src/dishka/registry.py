from typing import Any, List, NewType, Type

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

    def get_provider(self, dependency: Any) -> Factory:
        return self._providers.get(dependency)

def make_registries(
        *providers: Provider, scopes: Type[BaseScope],
) -> List[Registry]:
    dependency_scopes = {}
    for provider in providers:
        for source in provider.dependency_sources:
            if hasattr(source, "scope"):
                dependency_scopes[source.provides] = source.scope

    registries = {scope: Registry(scope) for scope in scopes}

    for provider in providers:
        for source in provider.dependency_sources:
            if isinstance(source, Factory):
                scope = source.scope
            elif isinstance(source, Alias):
                scope = dependency_scopes[source.source]
                dependency_scopes[source.provides] = scope
                source = source.convert_to_factory(scope)
            elif isinstance(source, Decorator):
                scope = dependency_scopes[source.provides]
                registry = registries[scope]
                undecorated_type = NewType(
                    f"Original_{source.provides.__name__}",
                    source.provides,
                )
                original_provider = registry.get_provider(source.provides)
                original_provider.provides = undecorated_type
                registry.add_provider(original_provider)
                source = source.convert_to_factory(
                    scope, undecorated_type,
                )
            else:
                raise ValueError("Unknown dependency source type")
            registries[scope].add_provider(source)

    return list(registries.values())


I have rewritten the code according to the rules provided. I have renamed the method `as_provider` to `convert_to_factory` for clarity and consistency. I have also changed the variable name `dep_scopes` to `dependency_scopes` for improved readability.