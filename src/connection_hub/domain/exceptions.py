# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

__all__ = (
    "DomainError",
    "UserLimitReachedError",
    "PasswordRequiredError",
    "IncorrectPasswordError",
    "UserIsNotAdminError",
    "UserIsTryingKickHimselfError",
    "PlayerIsDisconnectedError",
    "PlayerIsConnectedError",
)


class DomainError(Exception): ...


class UserLimitReachedError(DomainError): ...


class PasswordRequiredError(DomainError): ...


class IncorrectPasswordError(DomainError): ...


class UserIsNotAdminError(DomainError): ...


class UserIsTryingKickHimselfError(DomainError): ...


class PlayerIsDisconnectedError(DomainError): ...


class PlayerIsConnectedError(DomainError): ...
