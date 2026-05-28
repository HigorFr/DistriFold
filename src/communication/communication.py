import time
from logger import print_to_node as print
from .communication_tags import *
from node_context import NodeContext
from .network import MPIConnector

#comunicação padrão
class CommunicationService:
    def __init__(self, context: NodeContext, connector: MPIConnector, on_leader_elected_callback):
        self.context = context
        self.connector = connector
        self.on_leader_elected = on_leader_elected_callback
        self.heartbeat_interval = 1.0
        self.timeout_seconds = 3.0
        self.in_election = False

    def run(self):
        # eleição inicial realista
        self.start_election()
        while not self.context.stop_event.is_set():
            self.tick()

    # realiza eleição com contagem de tempo coletando os ranks que aparecerem
    def start_election(self):
        with self.context.lock:
            if self.in_election:
                return
            self.in_election = True
            self.context.leader_rank = None

        print(f"[Nó {self.context.rank}] Iniciando eleição...")

        # pede eleição enviando start para todos
        for dest in range(self.context.size):
            if dest != self.context.rank:
                self.connector.send("ELECTION_START", dest=dest, tag=TAG_ELECTION_START)

        # inicia com seu próprio número
        votes = {self.context.rank}


        # envia seu número para todos
        for dest in range(self.context.size):
            if dest != self.context.rank:
                self.connector.send(self.context.rank, dest=dest, tag=TAG_ELECTION_VOTE)


        #inicia contagem de tempo
        end_time = time.time() + 1.5
        while time.time() < end_time:
            if self.context.stop_event.is_set():
                break

            # coleta os votos e start de outros
            for source in range(self.context.size):
                if source == self.context.rank:
                    continue

                # se alguém pediu eleição no meio, respondemos com nosso número
                msg_start = self.connector.check_message(source=source, tag=TAG_ELECTION_START)
                if msg_start:
                    self.connector.send(self.context.rank, dest=source, tag=TAG_ELECTION_VOTE)

                # coleta voto do outro
                vote = self.connector.check_message(source=source, tag=TAG_ELECTION_VOTE)
                if vote is not None:
                    print(f"[Nó {self.context.rank}] Recebeu número {vote} do Nó {source} na eleição")
                    votes.add(vote)

            time.sleep(0.05)


        #menor deles é o novo líder
        new_leader = min(votes)
        print(f"[Nó {self.context.rank}] Fim da contagem de tempo. Menor número é {new_leader}. Novo líder eleito!")

        with self.context.lock:
            self.context.leader_rank = new_leader
            self.context.last_heartbeat = time.time()
            self.in_election = False

        # callback para atualizar threads
        if self.on_leader_elected:
            self.on_leader_elected(new_leader)




    # ticka todas as funções de comunicação
    def tick(self):
        
        #sempre checa se alguém pediu eleição pra poder votar/participar
        for source in range(self.context.size):
            if source == self.context.rank:
                continue
            msg_start = self.connector.check_message(source=source, tag=TAG_ELECTION_START)
            if msg_start:
                self.start_election()
                return

        if self.context.rank == self.context.leader_rank:
            self._leader_send()
            self._leader_collect()
            time.sleep(self.heartbeat_interval)
        else:
            self._worker_receive()
            self._worker_check_timeout()




    # Envio em BROADCAST pra todo mundo, nos dois tipos de mensagem
    def _leader_send(self):
        # Heartbeat
        for dest in range(self.context.size):
            if dest == self.context.leader_rank:
                continue
            self.connector.send("PING", dest=dest, tag=TAG_HELLO)
            
        # Clonar o contexto, se mudou
        with self.context.lock:
            dirty = self.context.context_dirty
            payload = dict(self.context.leader_context)
            
        if dirty:
            print(f"[Líder {self.context.rank}] Redundância: Sincronizando contexto (epoch {payload['epoch']}) com os backups...")
            for dest in range(self.context.size):
                if dest == self.context.leader_rank:
                    continue

                self.connector.send(payload, dest=dest, tag=TAG_STATE_SYNC) 

            with self.context.lock:
                self.context.context_dirty = False


    # recebe ACKs do heartbeat e sinais de nó pronto
    def _leader_collect(self):
        acked_nodes = set()
        end_time = time.time() + 0.5
        while time.time() < end_time:
            if self.context.stop_event.is_set():
                break
            for source in range(self.context.size):
                if source == self.context.leader_rank:
                    continue

                #recebe ACKs normais
                msg = self.connector.check_message(source=source, tag=TAG_ACK)
                if msg:
                    print(f"Líder recebeu ACK de {source}")
                    acked_nodes.add(source)
                                    
                with self.context.lock:               
                    self.context.setAlive(source)

                #recebe sinal de nó pronto/recuperado
                msg_ready = self.connector.check_message(source=source, tag=TAG_NODE_READY)
                if msg_ready:
                    print(f"Líder recebeu ACK-Pronto do Nó {source}")
                    acked_nodes.add(source) #se está pronto, com certeza está vivo

                    with self.context.lock:
                        self.context.setAlive(source)
                        self.context.setReady(source)

            time.sleep(0.05)
        
        #coloca como morto se o node n enviou o ack nos 0.5s
        for source in range(self.context.size):
            if source == self.context.leader_rank:
                continue
            if source not in acked_nodes:
                with self.context.lock:
                    if source in self.context.leader_context["alive_nodes"]:
                        print(f"Líder detectou timeout do Nó {source} (sem ACK em 0.5s)!")
                        self.context.setDead(source)





    def _worker_receive(self):
        if self.context.leader_rank is None:
            self.start_election()
            return

        # Recebe Heartbeat do Lider e já envia ACK, se ele tiver pronto ele já envia isso também
        msg = self.connector.check_message(source=self.context.leader_rank, tag=TAG_HELLO)
        if msg:
            print(f"Worker {self.context.rank} recebeu PING do líder")
            
            if self.context.ready_to_work:
                self.connector.send("ACK", dest=self.context.leader_rank, tag=TAG_NODE_READY)
            else:
                self.connector.send("ACK", dest=self.context.leader_rank, tag=TAG_ACK)

            with self.context.lock:
                self.context.last_heartbeat = time.time()
                


        
        # Recebe contexto do Lider
        state_msg = self.connector.check_message(source=self.context.leader_rank, tag=TAG_STATE_SYNC)
        if state_msg:
            with self.context.lock:
                if state_msg["epoch"] > self.context.leader_context["epoch"]:
                    self.context.leader_context = state_msg
                    print(f"Worker {self.context.rank} sincronizou contexto para epoch {state_msg['epoch']}")




    # Função só pra chegar se lider caiu
    def _worker_check_timeout(self):
        with self.context.lock:
            elapsed = time.time() - self.context.last_heartbeat
        if elapsed > self.timeout_seconds:
            print(f"Worker {self.context.rank} detectou timeout do líder!")
            self.start_election()
        else:
            time.sleep(0.1)