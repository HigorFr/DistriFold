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
    def run(self):


        # caso caia e volte (ou no início), inicia a eleição realista primeiro
        print(f"[Worker {self.context.rank}] Iniciando e disparando eleição para descobrir líder...")
        if self.comm_service:
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
    

        #Inicializa o KFold TODO CONFERIR SE ESTÁ IDENTICO AO LIDER

        print(f"[Worker {self.context.rank}] Pronto e aguardando ordens de Folds do Líder.")
        

        
        while not self.context.stop_event.is_set():
            #Escuta ordens do lider
            msg = self.connector.check_message(source=self.context.leader_rank, tag=TAG_TASK)
            
            if msg is None:
                continue


            fold_id = msg['fold_id']
            config = msg['config']

            fold_config = config['FOLD']
            kf = KFold(**fold_config)
            splits = list(kf.split(X))


            if fold_id is not None:
                if fold_id == -1:
                    print(f"[Worker {self.context.rank}] Sinal de encerramento recebido do Líder. Desconectando...")
                    self.context.stop_event.set()
                    break
                
                print(f"[Worker {self.context.rank}] Treinando Fold {fold_id}...")
                


                # Pega os índices do fold de forma determinística localmente
                train_idx, test_idx = splits[fold_id]
                config_MLP = config['MLP']
                
                
                #Treina localmente usando a classe do MPL
                res = train_fold_from_arrays(X, y, train_idx, test_idx, config_MLP, fold_id=fold_id)
                
                #Envia só as métricas finais e pesos de volta
                self.connector.send(res, dest=self.context.leader_rank, tag=TAG_RESULT)
                print(f"[Worker {self.context.rank}] Concluiu e enviou métricas do Fold {fold_id}")
            time.sleep(0.1)
