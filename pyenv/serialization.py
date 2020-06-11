from abc import abstractmethod
from pickle import Pickler, Unpickler
from typing import BinaryIO, Iterable, Dict, Set


class CustomPickler(Pickler):
    pass


class CustomUnpickler(Unpickler):
    pass


class Dump:
    def __init__(self, value: BinaryIO):
        self._value = value

    def value(self) -> BinaryIO:
        return self._value


class PrimitiveDump(Dump):
    def __init__(self, value: BinaryIO, name: str):
        super().__init__(value)
        self._name = name

    def name(self) -> str:
        return self._name


class ComponentDump(Dump):
    def __init__(self, value: BinaryIO, var_names: Set[str], non_serialized_vars: Set[str]):
        super().__init__(value)
        self._var_names = set(var_names)
        self._non_serialized_vars = set(non_serialized_vars)

    def var_names(self) -> Set[str]:
        return set(self._var_names)

    def non_serialized_vars(self) -> Set[str]:
        return set(self._non_serialized_vars)


class LoadedComponent:
    def __init__(self, variables: Dict[str, object], non_deserialized_vars: Set[str]):
        self._variables = dict(variables)
        self._non_deserialized_vars = set(non_deserialized_vars)

    def variables(self) -> Dict[str, object]:
        return dict(self._variables)

    def non_deserialized_vars(self) -> Set[str]:
        return set(self._non_deserialized_vars)


class Serializer:
    @abstractmethod
    def dump(self, variables: Dict[str, object], dirty: Iterable[str]) -> Iterable[Dump]:
        pass


class Deserializer:
    @abstractmethod
    def load(self, raw: BinaryIO) -> LoadedComponent:
        pass
