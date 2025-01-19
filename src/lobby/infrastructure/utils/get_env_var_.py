# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

import os
from typing import Any, Callable, TypeVar, overload


_T = TypeVar("_T", bound=Any)


@overload
def get_env_var(key: str, value_factory: None = None) -> str: ...


@overload
def get_env_var(key: str, value_factory: Callable[[str], _T]) -> _T: ...


def get_env_var(
    key: str,
    value_factory: Callable[[str], _T] | None = None,
) -> str | _T:
    """
    Retrieves the value of an environment variable and
    optionally transforms it.

    This function retrieves the value of the specified environment
    variable. If a `value_factory` function is provided, the value
    is passed through this function before being returned. If the
    environment variable is not found or is empty, an exception
    is raised.
    """
    value = os.getenv(key)
    if not value:
        message = f"Env var {key} doesn't exist"
        raise Exception(message)

    if value_factory:
        return value_factory(value)

    return value
