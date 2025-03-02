# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

__all__ = ("CommonRetort", "common_retort_factory")

from datetime import timedelta
from typing import NewType

from adaptix import Retort, loader, dumper


CommonRetort = NewType("CommonRetort", Retort)  # type: ignore


def common_retort_factory() -> CommonRetort:
    """
    Retort additionally supports:

        - Loading `timedelta` from a `float` or a `str` representing
          the total number of seconds.

        - Dumping `timedelta` to a `float` representing
          the total number of seconds.
    """
    recipe = (
        loader(timedelta, lambda seconds: timedelta(seconds=float(seconds))),
        dumper(timedelta, timedelta.total_seconds),
    )
    retort = Retort(recipe=recipe)

    return CommonRetort(retort)
