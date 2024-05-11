
class Task:

    def __init__(self, name):
        self.name = name

    def begin(self) -> None:
        pass

    def end(self) -> None:
        pass

    def run(self) -> None:
        raise NotImplementedError("Task not Implemented!")
