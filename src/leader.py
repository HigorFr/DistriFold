import time


class LeaderWork:
    def __init__(self, node):
        self.node = node

    def run(self):
        for i in range(3):
            if self.node.stop_event.is_set():
                break
            print(f"Lider trabalhando no ciclo {i}")
            time.sleep(0.5)
