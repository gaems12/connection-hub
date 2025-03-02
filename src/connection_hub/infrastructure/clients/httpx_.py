# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from httpx import AsyncClient


def httpx_client_factory() -> AsyncClient:
    return AsyncClient()
