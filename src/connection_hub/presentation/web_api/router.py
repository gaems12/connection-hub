# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from fastapi import APIRouter

from .internal_routes import internal_router


router = APIRouter()
router.include_router(internal_router)
