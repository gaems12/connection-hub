# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from httpx import AsyncClient


def httpx_client_factory() -> AsyncClient:
    return AsyncClient()
