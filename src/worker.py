import time
from logger import print_to_node as print
from sklearn.model_selection import KFold
from node_context import NodeContext
from communication.network import MPIConnector
from communication.torrent import TorrentEngine
from communication.communication_tags import *
from MLP import train_fold_from_arrays
class WorkerWork:
    def __init__(self, context: NodeContext, connector: MPIConnector, comm_service=None):
        self.context = context
        self.connector = connector
        self.comm_service = comm_service
        self.torrent = TorrentEngine(context, connector)
        self.next_query_rank = (context.rank + 1) % context.size
        self.last_query_time = 0
    
    def run(self):
        # caso caia e volte (ou no início), inicia a eleição realista primeiro
        if not self.context.recovering:
            print(f"[Worker {self.context.rank}] Iniciando e disparando eleição para descobrir líder...")
            self.comm_service.start_election()


            #Aguarda a eleição do líder inicial antes de iniciar qualquer trabalho
            while self.context.leader_rank is None:
                time.sleep(0.1)


            #Por enquanto o Líder não deve agir como worker para evitar conflitos de processamento e deadlocks
            #TODO clocar lider para processar também
            if self.context.rank == self.context.leader_rank:
                print(f"[Nó {self.context.rank}] Sou o Líder, ignorando papel de Worker.")
                return

        print(f"[Worker {self.context.rank}] Iniciando verificação do Dataset...")
        #Faz o download ou carrega localmente as fatias do dataset
        X, y = self.torrent.download_as_worker()
        self.context.ready_to_work = True
        print(f"[Worker {self.context.rank}] Pronto e aguardando ordens de Folds do Líder.")

        #Inicializa o KFold TODO CONFERIR SE ESTÁ IDENTICO AO LIDER

        
        



        #Loop principal
        while not self.context.stop_event.is_set():
            if self.context.leader_rank == self.context.rank:
                print(f"[Nó {self.context.rank}] Virou líder, encerrando papel de Worker.")
                return
            # if not self.context._node_esta_ativo():
            #     time.sleep(0.1)
            #     continue


            

            if self.context.leader_rank is None:
                if self.context.needs_full_sync:
                    now = time.time()
                    if now - self.last_query_time > 0.5:
                        if self.next_query_rank == self.context.rank:
                            self.next_query_rank = (self.next_query_rank + 1) % self.context.size
                        self.comm_service.enqueue("worker", dest=self.next_query_rank, tag=TAG_LEADER_QUERY, payload="WHO")
                        self.last_query_time = now
                        self.next_query_rank = (self.next_query_rank + 1) % self.context.size

                    for source in range(self.context.size):
                        if source == self.context.rank:
                            continue
                        

                    leader_reply = self.comm_service.Poll(tag=TAG_LEADER_REPLY)
                    if leader_reply is not None:
                        with self.context.lock:
                            self.context.leader_rank = leader_reply
                            self.context.last_heartbeat = time.time()

                    if self.context.leader_rank is not None:
                        self.comm_service.enqueue("worker", dest=self.context.leader_rank, tag=TAG_CONTEXT_REQ, payload="CTX")
                        ctx_msg = self.comm_service.Poll(source=self.context.leader_rank, tag=TAG_CONTEXT_RESP)
                        
                        if ctx_msg:
                            with self.context.lock:
                                self.context.leader_context = ctx_msg
                                self.context.needs_full_sync = False
                                self.context.recovering = False
                                self.context.last_heartbeat = time.time()


                            print(f"Worker {self.context.rank} sincronizou contexto após retorno")

                    time.sleep(0.1)
                    continue


                self.comm_service.start_election()
                time.sleep(0.1)
                continue

            if self.context.recovering:
                time.sleep(0.1)
                continue




            msg = self.comm_service.Poll(source=self.context.leader_rank, tag=TAG_HELLO)
            
            if msg:
                print(f"Worker {self.context.rank} recebeu PING do líder")

                if self.context.ready_to_work:
                    self.comm_service.enqueue("worker", dest=self.comm_service.leader_tag, tag=TAG_NODE_READY, payload="ACK")
                else:
                    self.comm_service.enqueue("worker", dest=self.comm_service.leader_tag, tag=TAG_ACK, payload="ACK")

                with self.context.lock:
                    self.context.last_heartbeat = time.time()

            state_msg = self.comm_service.Poll(source=self.context.leader_rank, tag=TAG_STATE_SYNC)
            
            if state_msg:
                with self.context.lock:
                    if state_msg["epoch"] > self.context.leader_context["epoch"]:
                        self.context.leader_context = state_msg
                        print(f"Worker {self.context.rank} sincronizou contexto para epoch {state_msg['epoch']}")

            
            with self.context.lock:
                elapsed = time.time() - self.context.last_heartbeat

            if elapsed > self.comm_service.timeout_seconds:
                print(f"Worker {self.context.rank} detectou timeout do líder!")
                self.comm_service.start_election()
                time.sleep(0.1)
                continue


            #Escuta ordens do liders
            msg = None
            if self.comm_service:
                msg = self.comm_service.Poll(source=self.context.leader_rank, tag=TAG_TASK)
            
            if msg is None:
                continue


            fold_id = msg['fold_id']


            if fold_id is not None:
                if fold_id == -1:
                    print(f"[Worker {self.context.rank}] Sinal de encerramento recebido do Líder. Desconectando...")
                    self.context.stop_event.set()
                    break
                
                print(f"[Worker {self.context.rank}] Treinando Fold {fold_id}...")
                
                
                config = msg['config']
                fold_config = config['FOLD']
                kf = KFold(**fold_config)
                splits = list(kf.split(X))

                # Pega os índices do fold de forma determinística localmente
                print(fold_id)
                print(fold_config)

                train_idx, test_idx = splits[fold_id]
                config_MLP = config['MLP']
                
                
                #Treina localmente usando a classe do MPL
                res = train_fold_from_arrays(X, y, train_idx, test_idx, config_MLP, fold_id=fold_id)
                
                #Envia só as métricas finais e pesos de volta
                if not self.context._node_esta_ativo():
                    time.sleep(0.1)
                    continue
                
                if self.comm_service:
                    self.comm_service.enqueue("worker", dest=self.comm_service.leader_tag, tag=TAG_RESULT, payload=res)
                print(f"[Worker {self.context.rank}] Concluiu e enviou métricas do Fold {fold_id}")
            time.sleep(0.1)
