# Message Publisher Documentation

## 📚 Table of Contents

- [Lobby Related Events](#lobby-related-events)
    - [Lobby Created](#lobby-created)
    - [User Joined To Lobby](#user-joined-to-lobby)
    - [User Left Lobby](#user-left-lobby)
    - [User Kicked From Lobby](#user-kicked-from-lobby)
- [Game Related Events](#game-related-events)
    - [Connect Four Game Created](#connect-four-game-created)
    - [Player Disconnected From Connect Four Game](#player-disconnected-from-connect-four-game)
    - [Player Reconnected To Connect Four Game](#player-reconnected-to-connect-four-game)
    - [Player Disqualified From Connect Four Game](#player-disqualified-from-connect-four-game)


## Lobby Related Events

### Lobby Created

**Stream**: `games` \
**Subject**: `connection_hub.lobby.created` \
**Body Example:**
```json
{
    "lobby_id": "067cef373d9979eb8000403ac2c4dee4",
    "name": "Lobby Name",
    "admin_id": "067cef3969c278db800034e552b3a7c9",
    "has_password": true,
    "rule_set": {
        "type": "connect_four",
        "time_for_each_player": 60
    },
    "operation_id": "067cef3c429976588000cb3adfb40239"
}
```

### User Joined To Lobby

**Stream**: `games` \
**Subject**: `connection_hub.user_joined` \
**Body Example:**
```json
{
    "lobby_id": "067cef373d9979eb8000403ac2c4dee4",
    "user_id": "067cef5a386477078000997b0bb19bfb",
    "operation_id": "067cef3c429976588000cb3adfb40239"
}
```

### User Left Lobby

**Stream**: `games` \
**Subject**: `connection_hub.user_left` \
**Body Example:**

**If user was a regular member**:
```json
{
    "lobby_id": "067cef373d9979eb8000403ac2c4dee4",
    "user_id": "067cef5a386477078000997b0bb19bfb",
    "new_admin_id": null,
    "operation_id": "067cef3c429976588000cb3adfb40239"
}
```

**If user was an admin**:
```json
{
    "lobby_id": "067cef373d9979eb8000403ac2c4dee4",
    "user_id": "067cef5a386477078000997b0bb19bfb",
    "new_admin_id": "067cef650ce17aba8000d25da8049f4b",
    "operation_id": "067cef3c429976588000cb3adfb40239"
}
```

### User Kicked From Lobby

**Stream**: `games` \
**Subject**: `connection_hub.user_kicked` \
**Body Example:**
```json
{
    "lobby_id": "067cef373d9979eb8000403ac2c4dee4",
    "user_id": "067cef5a386477078000997b0bb19bfb",
    "operation_id": "067cef3c429976588000cb3adfb40239"
}
```

## Game Related Events

### Connect Four Game Created

**Stream**: `games` \
**Subject**: `connection_hub.connect_four.games.created` \
**Body Example:**
```json
{
    "game_id": "067cef373d9979eb8000403ac2c4dee4",
    "lobby_id": "067cef8a7d26755a80008094b5c9ae20",
    "first_player_id": "067cef8b5f2f7e348000d2483f4efd39",
    "second_player_id": "067cef5a386477078000997b0bb19bfb",
    "time_for_each_player": 60,
    "created_at": "2025-03-10T14:38:04.374229+00:00",
    "operation_id": "067cef3c429976588000cb3adfb40239"
}
```

### Player Disconnected From Connect Four Game

**Stream**: `games` \
**Subject**: `connection_hub.connect_four.games.player_disconnected` \
**Body Example:**
```json
{
    "game_id": "067cef373d9979eb8000403ac2c4dee4",
    "player_id": "067cef8b5f2f7e348000d2483f4efd39",
    "operation_id": "067cef3c429976588000cb3adfb40239"
}
```

### Player Reconnected To Connect Four Game

**Stream**: `games` \
**Subject**: `connection_hub.connect_four.games.player_disconnected` \
**Body Example:**
```json
{
    "game_id": "067cef373d9979eb8000403ac2c4dee4",
    "player_id": "067cef8b5f2f7e348000d2483f4efd39",
    "operation_id": "067cef3c429976588000cb3adfb40239"
}
```

### Player Disqualified From Connect Four Game

**Stream**: `games` \
**Subject**: `connection_hub.connect_four.games.player_disconnected` \
**Body Example:**
```json
{
    "game_id": "067cef373d9979eb8000403ac2c4dee4",
    "player_id": "067cef8b5f2f7e348000d2483f4efd39",
    "operation_id": "067cef3c429976588000cb3adfb40239"
}
```
