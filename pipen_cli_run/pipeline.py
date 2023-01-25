from abc import ABC, abstractmethod
from functools import wraps
from typing import Any, Mapping, Callable

from diot import Diot
from pipen import Pipen


class Pipeline(ABC):
    """The pipeline base class"""

    __slots__ = ("options", "starts", "ends", "procs")

    _PIPELINE = None
    defaults = Diot()

    def __new__(cls, *args, **kwargs):
        """Make sure only one instance is created"""
        if cls._PIPELINE is None:
            cls._PIPELINE = super().__new__(cls)
        return cls._PIPELINE

    def __init__(
        self,
        options: Mapping[str, Any] = None,
    ) -> None:
        self.options = Diot(self.__class__.defaults or {}) | (options or {})
        self.starts = []
        self.ends = []
        self.procs = Diot()

        self.build()

        if not self.starts:
            raise ValueError(
                "No start processes found. "
                "Did you forget to add them in build()?"
            )

    @abstractmethod
    def build(self) -> None:  # pragma: no cover
        """Build the pipeline"""
        raise NotImplementedError

    def run(self, data=None, **kwargs) -> Pipen:
        """Run the pipeline

        Args:
            data: The data to run the pipeline with
            kwargs: The keyword arguments to pass to Pipen

        Returns:
            The Pipen instance
        """
        kwargs.setdefault("name", self.__class__.__name__)
        if self.__doc__:
            kwargs.setdefault("desc", self.__doc__.lstrip().splitlines()[0])
        pipe = Pipen(**kwargs).set_start(self.starts)
        if data is not None:
            pipe.set_data(data)
        pipe.run()
        return pipe


def process(method: Callable = None, start: bool = False, end: bool = False):
    """Decorator to add a process to a pipeline

    Args:
        method: The method to decorate
        start: Whether the process is a start process
        end: Whether the process is an end process

    Returns:
        The decorated method
    """
    if method is None:
        return lambda meth: process(meth, start, end)

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        proc = method(self, *args, **kwargs)
        if start:
            self.starts.append(proc)
        if end:
            self.ends.append(proc)
        self.procs[proc.name] = proc
        return proc

    return wrapper
