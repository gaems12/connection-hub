# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

__all__ = ("UserRole",)

from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    REGULAR_MEMBER = "regular_member"
