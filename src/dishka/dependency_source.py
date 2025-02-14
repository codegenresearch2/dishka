from collections import defaultdict
from collections.abc import AsyncIterable, Iterable
from enum import Enum
from inspect import (
    isasyncgenfunction,
    isclass,
    iscoroutinefunction,
    isgeneratorfunction,
)
from typing import (
    Any,
    Callable,
    Optional,
    Sequence,
    Type,
    Union,
    get_args,
    get_origin,
    get_type_hints,
    overload,
)

from .scope import BaseScope

class FactoryType(Enum):
    GENERATOR = "generator"
    ASYNC_GENERATOR = "async_generator"
    FACTORY = "factory"
    ASYNC_FACTORY = "async_factory"
    VALUE = "value"

def _identity(x: Any) -> Any:
    return x

class Factory:
    __slots__ = (
        "dependencies", "source", "provides", "scope", "type",
        "is_to_bound",
    )

    def __init__(
            self,
            dependencies: Sequence[Any],
            source: Any,
            provides: Type,
            scope: Optional[BaseScope],
            type: FactoryType,
            is_to_bound: bool,
    ):
        self.dependencies = dependencies
        self.source = source
        self.provides = provides
        self.scope = scope
        self.type = type
        self.is_to_bound = is_to_bound

    def __get__(self, instance, owner):
        if instance is None:
            return self
        if self.is_to_bound:
            source = self.source.__get__(instance, owner)
        else:
            source = self.source
        return Factory(
            dependencies=self.dependencies,
            source=source,
            provides=self.provides,
            scope=self.scope,
            type=self.type,
            is_to_bound=False,
        )

def make_factory(
        provides: Any,
        scope: Optional[BaseScope],
        source: Callable,
) -> Factory:
    if isclass(source):
        hints = get_type_hints(source.__init__, include_extras=True)
        hints.pop("return", None)
        possible_dependency = source
        is_to_bind = False
    else:
        hints = get_type_hints(source, include_extras=True)
        possible_dependency = hints.pop("return", None)
        is_to_bind = True

    if isclass(source):
        provider_type = FactoryType.FACTORY
    elif isasyncgenfunction(source):
        provider_type = FactoryType.ASYNC_GENERATOR
        if get_origin(possible_dependency) is AsyncIterable:
            possible_dependency = get_args(possible_dependency)[0]
        else:  # async generator
            possible_dependency = get_args(possible_dependency)[0]
    elif isgeneratorfunction(source):
        provider_type = FactoryType.GENERATOR
        if get_origin(possible_dependency) is Iterable:
            possible_dependency = get_args(possible_dependency)[0]
        else:  # generator
            possible_dependency = get_args(possible_dependency)[1]
    elif iscoroutinefunction(source):
        provider_type = FactoryType.ASYNC_FACTORY
    else:
        provider_type = FactoryType.FACTORY

    return Factory(
        dependencies=list(hints.values()),
        type=provider_type,
        source=source,
        scope=scope,
        provides=provides or possible_dependency,
        is_to_bound=is_to_bind,
    )

@overload
def provide(
        *,
        scope: BaseScope,
        provides: Any = None,
) -> Callable[[Callable], Factory]:
    ...

@overload
def provide(
        source: Union[Callable, Type],
        *,
        scope: BaseScope,
        provides: Any = None,
) -> Factory:
    ...

def provide(
        source: Union[None, Callable, Type] = None,
        *,
        scope: BaseScope,
        provides: Any = None,
):
    if source is not None:
        return make_factory(provides, scope, source)

    def scoped(func):
        return make_factory(provides, scope, func)

    return scoped

class Alias:
    __slots__ = ("source", "provides")

    def __init__(self, source, provides):
        self.source = source
        self.provides = provides

    def as_factory(self, scope: BaseScope) -> Factory:
        return Factory(
            scope=scope,
            source=_identity,
            provides=self.provides,
            is_to_bound=False,
            dependencies=[self.source],
            type=FactoryType.FACTORY,
        )

    def __get__(self, instance, owner):
        return self

def alias(
        *,
        source: Type,
        provides: Type,
):
    return Alias(
        source=source,
        provides=provides,
    )

class Decorator:
    __slots__ = ("provides", "factory")

    def __init__(self, factory: Factory):
        self.factory = factory
        self.provides = factory.provides

    def as_factory(
            self, scope: BaseScope, new_dependency: Any,
    ) -> Factory:
        return Factory(
            scope=scope,
            source=self.factory.source,
            provides=self.factory.provides,
            is_to_bound=self.factory.is_to_bound,
            dependencies=[
                new_dependency if dep is self.provides else dep
                for dep in self.factory.dependencies
            ],
            type=self.factory.type,
        )

    def __get__(self, instance, owner):
        return Decorator(self.factory.__get__(instance, owner))

def decorate(
        source: Union[None, Callable, Type] = None,
        provides: Any = None,
):
    if source is not None:
        return Decorator(make_factory(provides, None, source))

    def scoped(func):
        return Decorator(make_factory(provides, None, func))

    return scoped

DependencySource = Alias | Factory | Decorator

class Registry:
    def __init__(self, scope: BaseScope):
        self.factories = defaultdict(Factory)
        self.scope = scope

    def add_factory(self, factory: Factory):
        self.factories[factory.provides] = factory

    def get_factory(self, dependency: Any) -> Factory:
        return self.factories.get(dependency)

def make_registries(
        *providers: Provider, scopes: Type[BaseScope],
) -> list[Registry]:
    dependency_scopes = defaultdict(BaseScope)
    for provider in providers:
        for source in provider.dependency_sources:
            if hasattr(source, "scope"):
                dependency_scopes[source.provides] = source.scope

    registries = {scope: Registry(scope) for scope in scopes}
    decorator_depth = defaultdict(int)

    for provider in providers:
        for source in provider.dependency_sources:
            provides = source.provides
            if isinstance(source, Factory):
                scope = source.scope
            elif isinstance(source, Alias):
                scope = dependency_scopes[source.source]
                dependency_scopes[provides] = scope
                source = source.as_factory(scope)
            elif isinstance(source, Decorator):
                scope = dependency_scopes[provides]
                registry = registries[scope]
                undecorated_type = Type(
                    f"{provides.__name__}@{decorator_depth[provides]}",
                    (source.provides,),
                )
                decorator_depth[provides] += 1
                old_factory = registry.get_factory(provides)
                old_factory.provides = undecorated_type
                registry.add_factory(old_factory)
                source = source.as_factory(
                    scope, undecorated_type,
                )
            else:
                raise ValueError("Unknown dependency source type")
            registries[scope].add_factory(source)

    return list(registries.values())