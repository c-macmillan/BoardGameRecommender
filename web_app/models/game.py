from typing import Any


class Game():
    def __init__(self, attr):
        for key, value in attr.items():
            self.__setattr__(key, value)
        if not self.__getattribute__("expected_play_time"):
            if not self.__getattribute__("max_play_time"):
                self.expected_play_time = self.max_play_time
            else:
                self.expected_play_time = 90
    
    def __str__(self) -> str:
        if self.__getattribute__("name"):
            return self.name
        