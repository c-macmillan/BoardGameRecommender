class Game():
    def __init__(self, attr):
        for key, value in attr.items():
            self.__setattr__(key, value)
    
    def __str__(self) -> str:
        if self.__getattribute__("name"):
            return self.name