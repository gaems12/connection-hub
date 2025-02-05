# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

__all__ = (
    "DomainError",
    "UserLimitReachedError",
    "PasswordRequiredError",
    "IncorrectPasswordError",
    "UserIsNotAdminError",
    "PlayerIsDisconnectedError",
    "PlayerIsConnectedError",
)


class DomainError(Exception): ...


class UserLimitReachedError(DomainError): ...


class PasswordRequiredError(DomainError): ...


class IncorrectPasswordError(DomainError): ...


class UserIsNotAdminError(DomainError): ...


class PlayerIsDisconnectedError(DomainError): ...


class PlayerIsConnectedError(DomainError): ...
