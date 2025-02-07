from typing import Any, List, NewType, Type

from .dependency_source import FactorySource, AliasSource, DecoratorSource
from .provider import Provider
from .scope import BaseScope


class Registry:
    __slots__ = ("scope", "_providers")

    def __init__(self, scope: BaseScope):
        self._providers = {}
        self.scope = scope

    def add_provider(self, provider: FactorySource):
        self._providers[provider.provides] = provider

    def get_provider(self, dependency: Any) -> FactorySource:
        return self._providers.get(dependency)


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
            if isinstance(source, FactorySource):
                scope = source.scope
            elif isinstance(source, AliasSource):
                scope = dep_scopes[source.source]
                dep_scopes[source.provides] = scope
                source = source.as_provider(scope)
            elif isinstance(source, DecoratorSource):
                scope = dep_scopes[source.provides]
                registry = registries[scope]
                undecorated_type = NewType(
                    f"Old_{source.provides.__name__}",
                    source.provides,
                )
                old_provider = registry.get_provider(source.provides)
                old_provider.provides = undecorated_type
                registry.add_provider(old_provider)
                source = source.as_provider(
                    scope, undecorated_type,
                )
            else:
                raise ValueError("Unknown dependency source type")
            registries[scope].add_provider(source)

    return list(registries.values())
