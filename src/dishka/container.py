from dataclasses import dataclass
from threading import Lock
from typing import Callable, List, Optional, Type, TypeVar

from .dependency_source import Factory, FactoryType
from .provider import Provider
from .registry import Registry, make_registries
from .scope import BaseScope, Scope

T = TypeVar("T")

@dataclass
class Exit:
    __slots__ = ("type", "callable")
    factory_type: FactoryType
    callable: Callable

class DependencyContainer:
    __slots__ = (
        "registry", "child_registries", "context", "parent_container",
        "lock", "exits",
    )

    def __init__(
            self,
            registry: Registry,
            *child_registries: Registry,
            parent_container: Optional["DependencyContainer"] = None,
            context: Optional[dict] = None,
            use_lock: bool = False,
    ):
        self.registry = registry
        self.child_registries = child_registries
        self.context = {type(self): self}
        if context:
            self.context.update(context)
        self.parent_container = parent_container
        if use_lock:
            self.lock = Lock()
        else:
            self.lock = None
        self.exits: List[Exit] = []

    def create_child(
            self,
            context: Optional[dict],
            use_lock: bool,
    ) -> "DependencyContainer":
        return DependencyContainer(
            *self.child_registries,
            parent_container=self,
            context=context,
            use_lock=use_lock,
        )

    def __call__(
            self,
            context: Optional[dict] = None,
            use_lock: bool = False,
    ) -> "ContextWrapper":
        """
        Prepare container for entering the inner scope.
        :param context: Data which will be available in inner scope
        :param use_lock: Whether to synchronize dependency cache or not
        :return: context manager for inner scope
        """
        if not self.child_registries:
            raise ValueError("No child scopes found")
        return ContextWrapper(self.create_child(context, use_lock))

    def get_from_parent(self, dependency_type: Type[T]) -> T:
        return self.parent_container.get(dependency_type)

    def get_from_self(
            self,
            dependency_provider: Factory,
    ) -> T:
        sub_dependencies = [
            self.get_unlocked(dependency)
            for dependency in dependency_provider.dependencies
        ]
        if dependency_provider.type is FactoryType.GENERATOR:
            generator = dependency_provider.source(*sub_dependencies)
            self.exits.append(Exit(dependency_provider.type, generator))
            return next(generator)
        elif dependency_provider.type is FactoryType.FACTORY:
            return dependency_provider.source(*sub_dependencies)
        elif dependency_provider.type is FactoryType.VALUE:
            return dependency_provider.source
        else:
            raise ValueError(f"Unsupported type {dependency_provider.type}")

    def get(self, dependency_type: Type[T]) -> T:
        lock = self.lock
        if not lock:
            return self.get_unlocked(dependency_type)
        with lock:
            return self.get_unlocked(dependency_type)

    def get_unlocked(self, dependency_type: Type[T]) -> T:
        if dependency_type in self.context:
            return self.context[dependency_type]
        provider = self.registry.get_provider(dependency_type)
        if not provider:
            if not self.parent_container:
                raise ValueError(f"No provider found for {dependency_type!r}")
            return self.parent_container.get(dependency_type)
        solved = self.get_from_self(provider)
        self.context[dependency_type] = solved
        return solved

    def close(self):
        e = None
        for exit_generator in self.exits:
            try:
                if exit_generator.factory_type is FactoryType.GENERATOR:
                    next(exit_generator.callable)
            except StopIteration:
                pass
            except Exception as err:  # noqa: BLE001
                e = err
        if e:
            raise e

class ContextWrapper:
    __slots__ = ("container",)

    def __init__(self, container: DependencyContainer):
        self.container = container

    def __enter__(self) -> DependencyContainer:
        return self.container

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.container.close()

def make_dependency_container(
        *providers: Provider,
        scopes: Type[BaseScope] = Scope,
        context: Optional[dict] = None,
        use_lock: bool = False,
) -> ContextWrapper:
    registries = make_registries(*providers, scopes=scopes)
    return ContextWrapper(
        DependencyContainer(*registries, context=context, use_lock=use_lock),
    )