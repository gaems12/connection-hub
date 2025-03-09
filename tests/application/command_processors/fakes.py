# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from typing import Any, Iterable, Final, cast, overload
from datetime import datetime, timedelta
from uuid import UUID

from connection_hub.domain import (
    LobbyId,
    GameId,
    UserId,
    PlayerStateId,
    Lobby,
    Game,
)
from connection_hub.application import (
    LobbyGateway,
    GameGateway,
    Event,
    EventPublisher,
    Task,
    TaskScheduler,
    Serializable,
    CentrifugoPublishCommand,
    CentrifugoUnsubscribeCommand,
    CentrifugoCommand,
    CentrifugoClient,
    IdentityProvider,
)


class FakeLobbyGateway(LobbyGateway):
    __slots__ = ("_lobbies",)

    def __init__(self, lobbies: dict[LobbyId, Lobby] | None = None):
        self._lobbies = lobbies or {}

    @property
    def lobbies(self) -> list[Lobby]:
        return list(self._lobbies.values())

    async def by_id(
        self,
        id: LobbyId,
        *,
        acquire: bool = False,
    ) -> Lobby | None:
        return self._lobbies.get(id, None)

    async def by_user_id(
        self,
        user_id: UserId,
        *,
        acquire: bool = False,
    ) -> Lobby | None:
        for lobby in self._lobbies.values():
            if user_id in lobby.users:
                return lobby
        return None

    async def save(self, lobby: Lobby) -> None:
        self._lobbies[lobby.id] = lobby

    async def update(self, lobby: Lobby) -> None:
        self._lobbies[lobby.id] = lobby

    async def delete(self, lobby: Lobby) -> None:
        self._lobbies.pop(lobby.id, None)


class FakeGameGateway(GameGateway):
    __slots__ = ("_games",)

    def __init__(self, games: dict[GameId, Game] | None = None):
        self._games = games or {}

    @property
    def games(self) -> list[Game]:
        return list(self._games.values())

    async def by_id(
        self,
        id: GameId,
        *,
        acquire: bool = False,
    ) -> Game | None:
        return self._games.get(id, None)

    async def by_player_id(
        self,
        player_id: UserId,
        *,
        acquire: bool = False,
    ) -> Game | None:
        for game in self._games.values():
            if player_id in game.players:
                return game
        return None

    async def save(self, game: Game) -> None:
        self._games[game.id] = game

    async def update(self, game: Game) -> None:
        self._games[game.id] = game

    async def delete(self, game: Game) -> None:
        self._games.pop(game.id)


class FakeEventPublisher(EventPublisher):
    __slots__ = ("_events",)

    def __init__(self, events: list[Event] | None = None):
        self._events = events or []

    @property
    def events(self) -> list[Event]:
        return self._events

    async def publish(self, event: Event) -> None:
        self._events.append(event)


class FakeTaskScheduler(TaskScheduler):
    __slots__ = ("_tasks",)

    def __init__(self, tasks: dict[UUID, Task] | None = None):
        self._tasks = tasks or {}

    @property
    def tasks(self) -> list[Task]:
        return list(self._tasks.values())

    async def schedule(self, task: Task) -> None:
        self._tasks[task.id] = task

    async def unschedule(self, task_id: UUID) -> None:
        self._tasks.pop(task_id, None)

    async def unschedule_many(self, task_ids: Iterable[UUID]) -> None:
        for task_id in task_ids:
            self._tasks.pop(task_id, None)


class FakeCentrifugoClient(CentrifugoClient):
    __slots__ = ("_publications", "_subscriptions")

    def __init__(
        self,
        publications: dict[str, Serializable] | None = None,
        subscriptons: dict[str, list[str]] | None = None,
    ):
        self._publications = publications or {}
        self._subscriptions = subscriptons or {}

    @property
    def publications(self) -> dict[str, Serializable]:
        return self._publications

    @property
    def subscriptions(self) -> dict[str, list[str]]:
        return self._subscriptions

    async def publish(
        self,
        *,
        channel: str,
        data: Serializable,
    ) -> None:
        self._publications[channel] = data

    async def batch(
        self,
        *,
        commands: Iterable[CentrifugoCommand],
        parallel: bool = True,
    ) -> None:
        for command in commands:
            if isinstance(command, CentrifugoPublishCommand):
                self._publications[command.channel] = command.data

            elif isinstance(command, CentrifugoUnsubscribeCommand):
                channels = self._subscriptions.setdefault(command.user, [])
                if command.channel in channels:
                    channels.remove(command.channel)


class FakeIdentityProvider(IdentityProvider):
    __slots__ = ("_user_id",)

    def __init__(self, user_id: UserId):
        self._user_id = user_id

    async def user_id(self) -> UserId:
        return self._user_id


class _Anything:
    __slots__ = ("_name", "_type")

    def __init__(self, name: str, type_: type):
        self._name = name
        self._type = type_

    @classmethod
    @overload
    def create[TH: Any](
        cls,
        *,
        name: str,
        type_: type[Any],
        type_hint: type[TH],
    ) -> TH: ...

    @classmethod
    @overload
    def create[T: Any](
        cls,
        *,
        name: str,
        type_: type[T],
    ) -> T: ...

    @classmethod
    def create[T: Any, TH: Any](
        cls,
        *,
        name: str,
        type_: type[T],
        type_hint: type[TH] | None = None,
    ) -> T | TH:
        anything = _Anything(name, type_)
        if type_hint:
            return cast(TH, anything)

        return cast(T, anything)

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, self._type):
            return NotImplemented
        return True

    def __ne__(self, value: object) -> bool:
        if not isinstance(value, self._type):
            return NotImplemented
        return False

    def __repr__(self) -> str:
        return f"<{self._name}>"


ANY_LOBBY_ID: Final = _Anything.create(
    name="ANY_LOBBY_ID",
    type_=UUID,
    type_hint=LobbyId,
)
ANY_PLAYER_STATE_ID: Final = _Anything.create(
    name="ANY_PLAYER_STATE_ID",
    type_=UUID,
    type_hint=PlayerStateId,
)
ANY_GAME_ID: Final = _Anything.create(
    name="ANY_GAME_ID",
    type_=UUID,
    type_hint=GameId,
)
ANY_STR: Final = _Anything.create(
    name="ANY_STR",
    type_=str,
)
ANY_DATETIME: Final = _Anything.create(
    name="ANY_DATETIME",
    type_=datetime,
)
ANY_TIMEDELTA: Final = _Anything.create(
    name="ANY_TIMEDELTA",
    type_=timedelta,
)
