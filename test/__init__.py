class ExceptionMatching(str):
    def __eq__(self, other):
        return str(self) == str(other)
