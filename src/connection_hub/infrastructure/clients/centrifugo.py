# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

import logging
from urllib.parse import urljoin
from dataclasses import dataclass
from typing import Iterable, Final

from httpx import AsyncClient, Timeout
from tenacity import (
    RetryCallState,
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from connection_hub.application import (
    Serializable,
    CentrifugoPublishCommand,
    CentrifugoUnsubscribeCommand,
    CentrifugoCommand,
    CentrifugoClient,
)
from connection_hub.infrastructure.utils import get_env_var


_logger: Final = logging.getLogger(__name__)

_MAX_RETRIES: Final = 20
_BASE_BACKOFF_DELAY: Final = 0.5
_MAX_BACKOFF_DELAY: Final = 10

_REQUEST_TIMEOUT: Final = Timeout(30)


class CentrifuoClientError(Exception): ...


def load_centrifugo_config() -> "CentrifugoConfig":
    return CentrifugoConfig(
        url=get_env_var("CENTRIFUGO_URL"),
        api_key=get_env_var("CENTRIFUGO_API_KEY"),
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class CentrifugoConfig:
    url: str
    api_key: str


def _log_before_retry(retry_state: RetryCallState) -> None:
    _logger.debug(
        {
            "message": "Going to retry request to centrifugo.",
            "retry_number": retry_state.attempt_number,
            "retries_left": _MAX_RETRIES - retry_state.attempt_number,
        },
    )


class HTTPXCentrifugoClient(CentrifugoClient):
    __slots__ = ("_httpx_client", "_config")

    def __init__(
        self,
        httpx_client: AsyncClient,
        config: CentrifugoConfig,
    ):
        self._httpx_client = httpx_client
        self._config = config

    async def publish(
        self,
        *,
        channel: str,
        data: Serializable,
    ) -> None:
        await self._send_request(
            url=urljoin(self._config.url, "publish"),
            json_={"channel": channel, "data": data},
            retry_on_failure=True,
        )

    async def batch(
        self,
        *,
        commands: Iterable[CentrifugoCommand],
        parallel: bool = True,
    ) -> None:
        commands_as_dicts = self._commands_to_dicts(commands)

        await self._send_request(
            url=urljoin(self._config.url, "batch"),
            json_={"commands": commands_as_dicts, "parallel": parallel},
            retry_on_failure=True,
        )

    def _commands_to_dicts(
        self,
        commands: Iterable[CentrifugoCommand],
    ) -> list[Serializable]:
        commands_as_dicts: list[Serializable] = []

        for command in commands:
            if isinstance(command, CentrifugoPublishCommand):
                command_as_dict = {
                    "publish": {
                        "channel": command.channel,
                        "data": command.data,
                    },
                }
                commands_as_dicts.append(command_as_dict)  # type: ignore[arg-type]

            elif isinstance(command, CentrifugoUnsubscribeCommand):
                command_as_dict = {
                    "ubsubscribe": {
                        "user": command.user,
                        "channel": command.channel,
                    },
                }
                commands_as_dicts.append(command_as_dict)  # type: ignore[arg-type]

        return commands_as_dicts

    @retry(
        stop=stop_after_attempt(_MAX_RETRIES),
        wait=wait_exponential(_BASE_BACKOFF_DELAY, _MAX_BACKOFF_DELAY),
        retry=retry_if_exception_type(CentrifuoClientError),
        before_sleep=_log_before_retry,
        reraise=True,
    )
    async def _send_request(
        self,
        *,
        url: str,
        json_: Serializable,
        retry_on_failure: bool,
    ) -> None:
        try:
            _logger.debug(
                {
                    "message": "Going to make request to centrifugo.",
                    "url": url,
                    "json": json_,
                },
            )
            response = await self._httpx_client.post(
                url=url,
                json=json_,
                headers={"X-API-Key": self._config.api_key},
                timeout=_REQUEST_TIMEOUT,
            )
        except Exception as error:
            error_message = (
                "Unexpected error occurred during request to centrifugo."
            )
            _logger.exception(error_message)

            raise CentrifuoClientError(error_message) from error

        if response.status_code == 200:
            _logger.debug(
                {
                    "message": "Centrifuo responded.",
                    "status_code": response.status_code,
                    "Centrifuo responded.content": response.content.decode(),
                },
            )
            return

        error_message = "Centrifugo responded with bad status code."
        _logger.error(
            {
                "message": error_message,
                "status_code": response.status_code,
                "content": response.content.decode(),
            },
        )

        raise CentrifuoClientError(error_message)
