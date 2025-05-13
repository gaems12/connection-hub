# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

__all__ = ("ConnectFourRuleSet", "RuleSet")

from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True, slots=True)
class ConnectFourRuleSet:
    time_for_each_player: timedelta


type RuleSet = ConnectFourRuleSet
