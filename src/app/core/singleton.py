from __future__ import annotations

from typing import ClassVar


class SingletonMeta(type):
    """
    Metaclass enforcing a single instance per class.

    Notes:
      - Not thread-safe. Wrap __call__ with a Lock if you need safety.
    """

    _instances: ClassVar[dict] = {}

    def __call__(cls, *args, **kwargs):  # instance creation
        if cls not in cls._instances:
            # type.__call__ -> allocates and initializes the instance
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
