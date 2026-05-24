from mpi4py import MPI
import threading
import time

from communication import CommunicationService
from leader import LeaderWork
from worker import WorkerWork


class MainNode:
    def __init__(self, comm):
        self.comm = comm
        self.rank = comm.Get_rank()
        self.size = comm.Get_size()
        self.stop_event = threading.Event()
        self.lock = threading.Lock()
        self.leader_rank = None
        self.last_heartbeat = time.time()

        self.comm_service = CommunicationService(self)
        self.leader_work = LeaderWork(self)
        self.worker_work = WorkerWork(self)

        self.comm_thread = None
        self.leader_thread = None
        self.worker_thread = None


        self.context = None



    def run(self):
        self.start_threads()
        time.sleep(4)
        self.stop_event.set()
        self.comm_thread.join(timeout=1)



    def elect_leader(self):
        leader_rank = self.comm.allreduce(self.rank, op=MPI.MAX)
        with self.lock:
            self.leader_rank = leader_rank
            self.last_heartbeat = time.time()
        self.start_leader_if_self()


    def start_leader_if_self(self):
        if self.rank != self.leader_rank:
            return
        if self.leader_thread and self.leader_thread.is_alive():
            return
        self.leader_thread = threading.Thread(target=self.leader_work.run, daemon=True)
        self.leader_thread.start()


    def start_threads(self):
        self.comm_thread = threading.Thread(target=self.comm_service.run, daemon=True)
        self.comm_thread.start()

        self.worker_thread = threading.Thread(target=self.worker_work.run, daemon=True)
        self.worker_thread.start()







def main():
    comm = MPI.COMM_WORLD
    node = MainNode(comm)
    node.run()


if __name__ == "__main__":
    main()
