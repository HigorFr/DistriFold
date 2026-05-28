import mpi4py
mpi4py.rc.initialize = False
mpi4py.rc.finalize = True
from mpi4py import MPI
import threading
import time
from communication import CommunicationService
from leader import LeaderWork
from worker import WorkerWork
from node_context import NodeContext
from communication.network import MPIConnector
import os


# Inicializa o MPI solicitando suporte completo a múltiplas threads concorrentes
provided = MPI.Init_thread(MPI.THREAD_MULTIPLE)


DATASET_ID = "breast_cancer"

CONFIG_FOLD = {
    "n_splits":5, 
    "shuffle":True, 
    'random_state':42
            }


CONFIG_MLP = {
        "h1": 64, "h2": 16, "lr": 0.005,
        "epochs": 100, "batch_size": 32
                }


class MainNode:
    def __init__(self, comm):
        self.context = NodeContext(rank=comm.Get_rank(), size=comm.Get_size())
        
        # Duplica o comunicador para separar o tráfego de controle (threads de heartbeat)
        # do tráfego de dados (seeding/torrent/treino) para evitar colisões
        self.comm_control = comm.Dup()
        self.comm_data = comm.Dup()
        self.src_dir = os.path.dirname(os.path.abspath(__file__))
        self.connector_control = MPIConnector(self.comm_control)
        self.connector_data = MPIConnector(self.comm_data)
        
        self.comm_service = CommunicationService(
            context=self.context,
            connector=self.connector_control,
            on_leader_elected_callback=self.on_leader_elected
        )
        self.leader_work = LeaderWork(self.context, self.connector_data, DATASET_ID, CONFIG_MLP, CONFIG_FOLD)
        self.worker_work = WorkerWork(self.context, self.connector_data, comm_service=self.comm_service)

        #Controle de Threads
        self.comm_thread = None
        self.leader_thread = None
        self.worker_thread = None






    def on_leader_elected(self, leader_rank):
        # Callback disparado quando a eleição termina
        self.start_leader_if_self()

    def start_leader_if_self(self):
        if self.context.rank != self.context.leader_rank:
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




    def run(self):
        # if self.comm_control.Get_rank() == 0:
        #     self.clear_locals()
        
        self.start_threads()
        #Loop principal do Orquestrador
        while not self.context.stop_event.is_set():
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                self.context.stop_event.set()


    #Limpa a pasta locals para simular nós novos zerados (exceto o npz do 0, que é o primeiro lider)



def main():
    comm = MPI.COMM_WORLD
    node = MainNode(comm)

    node.run()


if __name__ == "__main__":
    main()
