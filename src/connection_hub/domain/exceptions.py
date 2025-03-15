# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

__all__ = (
    "DomainError",
    "UserLimitReachedError",
    "PasswordRequiredError",
    "IncorrectPasswordError",
    "CurrentUserIsNotAdminError",
    "CurrentUserIsTryingKickHimselfError",
    "CurrentUserIsDisconnectedFromGameError",
    "CurrentUserIsConnectedToGameError",
)


class DomainError(Exception): ...


class UserLimitReachedError(DomainError): ...


class PasswordRequiredError(DomainError): ...


class IncorrectPasswordError(DomainError): ...


class CurrentUserIsNotAdminError(DomainError): ...


class CurrentUserIsTryingKickHimselfError(DomainError): ...


class CurrentUserIsDisconnectedFromGameError(DomainError): ...


class CurrentUserIsConnectedToGameError(DomainError): ...
