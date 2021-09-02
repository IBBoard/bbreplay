from bbreplay import Peekable


class iter_(Peekable):
    def __init__(self, generator):
        super().__init__(generator)
        self.__i = 0

    def next(self):
        datum = super().next()
        print(f"\tConsuming {type(datum).__name__} {self.__i}: {datum}")
        self.__i += 1
        return datum
