# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from datetime import timedelta


def str_to_timedelta(value: str) -> timedelta:
    """
    Converts a string representing seconds into a
    timedelta object.
    """
    value_as_int = int(value)
    return timedelta(seconds=value_as_int)
