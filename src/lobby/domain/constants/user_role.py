# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    REGULAR_MEMBER = "regular_member"
