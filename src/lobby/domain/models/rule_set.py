# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True, slots=True)
class FourInARowRuleSet:
    time_for_each_player: timedelta


type RuleSet = FourInARowRuleSet
