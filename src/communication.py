import time

TAG_HELLO = 1
TAG_ACK = 2


class CommunicationService:
    def __init__(self, node, heartbeat_interval=1.0, timeout_seconds=3.0):
        self.node = node
        self.heartbeat_interval = heartbeat_interval
        self.timeout_seconds = timeout_seconds



    def run(self):
        self.node.elect_leader()
        while not self.node.stop_event.is_set():
            self.tick()

    def tick(self):
        if self.node.rank == self.node.leader_rank:
            self._leader_send()
            self._leader_collect()
            self._leader_sleep()
        else:
            self._worker_receive()
            self._worker_check_timeout()



    def _leader_send(self):
        for dest in range(self.node.size):
            if dest == self.node.leader_rank:
                continue

            self.node.comm.send("PING", dest=dest, tag=TAG_HELLO)

    def _leader_collect(self):
        end_time = time.time() + 0.5
        while time.time() < end_time:
            if self.node.stop_event.is_set():
                break
            for source in range(self.node.size):
                if source == self.node.leader_rank:
                    continue
                if self.node.comm.iprobe(source=source, tag=TAG_ACK):
                    msg = self.node.comm.recv(source=source, tag=TAG_ACK)
                    print(f"Lider recebeu de {source}: {msg}")
            time.sleep(0.05)

    def _leader_sleep(self):
        time.sleep(self.heartbeat_interval)



    def _worker_receive(self):
        if self.node.leader_rank is None:
            self.node.elect_leader()
            return

        if self.node.comm.iprobe(source=self.node.leader_rank, tag=TAG_HELLO):
            msg = self.node.comm.recv(source=self.node.leader_rank, tag=TAG_HELLO)
            print(f"Worker {self.node.rank} recebeu: {msg}")
            self.node.comm.send("ACK", dest=self.node.leader_rank, tag=TAG_ACK)
            with self.node.lock:
                self.node.last_heartbeat = time.time()

    def _worker_check_timeout(self):
        with self.node.lock:
            elapsed = time.time() - self.node.last_heartbeat

        if elapsed > self.timeout_seconds:
            self.node.elect_leader()
        else:
            time.sleep(0.1)
