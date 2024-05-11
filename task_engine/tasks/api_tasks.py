from task_engine.tasks.base import Task


class RefreshMetricTask(Task):

    def __init__(self):
        super().__init__(name="RefreshMetricTask")

    def run(self) -> None:
        print("Test!")
