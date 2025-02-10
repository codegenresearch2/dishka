from collections import defaultdict
from typing import Any, List, NewType, Type

from .dependency_source import Factory
from .provider import Provider
from .scope import BaseScope

class Registry:
    __slots__ = ("scope", "factories")

    def __init__(self, scope: BaseScope):
        self.factories = {}
        self.scope = scope

    def add_factory(self, factory: Factory):
        self.factories[factory.provides] = factory

    def get_factory(self, dependency: Any) -> Factory:
        return self.factories.get(dependency)

def create_registries(
        *providers: Provider, scopes: Type[BaseScope],
) -> List[Registry]:
    dependency_scopes = {}
    alias_sources = {}
    for provider in providers:
        for factory in provider.factories:
            dependency_scopes[factory.provides] = factory.scope
        for alias in provider.aliases:
            alias_sources[alias.provides] = alias.source

    registries = {scope: Registry(scope) for scope in scopes}
    decorator_depth = defaultdict(int)

    for provider in providers:
        for factory in provider.factories:
            scope = factory.scope
            registries[scope].add_factory(factory)
        for alias in provider.aliases:
            alias_source = alias.source
            visited_types = [alias_source]
            while alias_source not in dependency_scopes:
                alias_source = alias_sources[alias_source]
                if alias_source in visited_types:
                    raise ValueError(f"Cycle aliases detected: {visited_types}")
                visited_types.append(alias_source)
            scope = dependency_scopes[alias_source]
            dependency_scopes[alias.provides] = scope
            factory = alias.as_factory(scope)
            registries[scope].add_factory(factory)
        for decorator in provider.decorators:
            provides = decorator.provides
            scope = dependency_scopes[provides]
            registry = registries[scope]
            undecorated_type = NewType(
                f"{provides.__name__}@{decorator_depth[provides]}",
                decorator.provides,
            )
            decorator_depth[provides] += 1
            old_factory = registry.get_factory(provides)
            old_factory.provides = undecorated_type
            registry.add_factory(old_factory)
            factory = decorator.as_factory(
                scope, undecorated_type,
            )
            registries[scope].add_factory(factory)

    return list(registries.values())