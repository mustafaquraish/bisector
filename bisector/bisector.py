"""
This module contains the core logic for the Bisector.
"""

from enum import Enum
from typing import TypeVar, Generic, List, Any, Tuple

T = TypeVar('T')

class BisectionResult(Enum):
    """
    Represents the final status after running the bisector.
    """
    ALL_GOOD = 0
    ALL_BAD = 1
    FOUND_BAD = 2
    NOT_FOUND = 2

class Status(Enum):
    """
    Represents the status of a particular option.
    """
    GOOD = "good"
    BAD = "bad"
    SKIP = "skip"

class Bisector(Generic[T]):
    """
    A class to help with bisection of a list of options. The class should be
    initialized with a list of options. The user can then query the idx
    option and set the status of that option to good, bad, or skip, which will
    automatically compute the next option to query.

    If the bisector has found a bad option, it will be returned as the second
    value of the tuple when calling `get_result`. The first value of the tuple
    will be a `BisectionResult` enum value indicating the final status of the
    bisector.

    Example usage:

        ```python
        b = Bisector([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        while not b.is_done():
            x = b.idx()
            if x < 5:
                b.set_good()
            else:
                b.set_bad()
        result, value = b.get_result()
        ```

    """
    def __init__(self, options: List[T], statuses: List[Status] = None) -> None:
        self.options = options
        if statuses is not None:
            self.statuses = statuses
        else:
            self.statuses = [None] * len(options) # Don't know any statuses yet

        self.lo = 0
        self.hi = len(options)  # exclusive
        self._update()

    @classmethod
    def from_json(cls, data: dict) -> 'Bisector':
        options = data['options']
        statuses = [Status[s.upper()] if s is not None else None for s in data['statuses']]
        lo = data['lo']
        hi = data['hi']
        idx = data['idx']
        bisector = cls(options, statuses)
        bisector.lo = lo
        bisector.hi = hi
        bisector.idx = idx
        bisector._update()
        return bisector

    def to_json(self) -> dict:
        return {
            'options': self.options,
            'statuses': [s.value if s is not None else s for s in self.statuses],
            'lo': self.lo,
            'hi': self.hi,
            'idx': self.idx
        }

    @property
    def current(self) -> T:
        return self.options[self.idx]

    def is_done(self) -> bool:
        return self.lo >= self.hi

    def _update(self):
        self.idx = (self.lo + self.hi) // 2
        if not self.is_done() and self.statuses[self.idx] is not None:
            self.set_status(self.statuses[self.idx])

    def set_status(self, result: Status) -> None:
        if result == Status.SKIP:
            raise ValueError("Cannot skip an option yet")

        self.statuses[self.idx] = result
        if result == Status.BAD:
            self.hi = self.idx
        else:
            self.lo = self.idx + 1

        self._update()

    def set_good(self) -> None: self.set_status(Status.GOOD)
    def set_bad(self)  -> None: self.set_status(Status.BAD)
    def set_skip(self) -> None: self.set_status(Status.SKIP)


    def get_result(self) -> Tuple[BisectionResult, Any]:
        if self.hi == 0:
            return BisectionResult.ALL_BAD, None
        elif self.lo == len(self.options):
            return BisectionResult.ALL_GOOD, None
        elif self.idx == self.lo:
            return BisectionResult.FOUND_BAD, self.options[self.idx]
        else:
            return BisectionResult.NOT_FOUND, None