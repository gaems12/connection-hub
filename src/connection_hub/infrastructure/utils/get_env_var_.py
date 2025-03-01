# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

import os
from typing import Any, Callable, overload


@overload
def get_env_var(key: str) -> str: ...


@overload
def get_env_var[T: Any](
    key: str,
    *,
    value_factory: Callable[[str], T],
) -> T: ...


@overload
def get_env_var[T: Any, D: Any](
    key: str,
    *,
    value_factory: Callable[[str], T],
    default: D,
) -> T | D: ...


@overload
def get_env_var[D: Any](
    key: str,
    *,
    default: D,
) -> str | D: ...


def get_env_var[T: Any, D: Any](
    key: str,
    *,
    value_factory: Callable[[str], T] | None = None,
    default: D | None = None,
) -> str | T | D:
    """
    Retrieves the value of an environment variable and optionally
    transforms it.

    This function retrieves the value of the specified environment
    variable. If a `value_factory` function is provided, the variable's
    value is passed through this function before being returned. If the
    environment variable is not found or is empty, the `default` value
    is returned if provided; otherwise, an exception is raised.
    """
    value = os.getenv(key)
    if not value:
        if default:
            return default

        raise Exception(f"Env var {key} doesn't exist")

    if value_factory:
        return value_factory(value)

    return value
