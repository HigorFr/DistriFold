#tags pra deixar código mais legível

#Heartbeats
TAG_HELLO = 1
TAG_ACK = 2

#FOLD
TAG_TASK = 3
TAG_RESULT = 4
TAG_STATE_SYNC = 5
TAG_TASK_CONFIG = 6



#DADOS DO TORRENT
TAG_TORRENT_META = 10   #Envio de metadados do torrent (ex: formato, quantidade de chunks)
TAG_TORRENT_SEED = 11   #Envio do pedaço inicial para cada nó (Seeding inicial)
TAG_TORRENT_HAVE = 12   #Envio do vetor de inventário (quais pedaços eu tenho)
TAG_TORRENT_REQ = 13    #Solicitação de um pedaço específico
TAG_TORRENT_PIECE = 14  #Envio do pedaço físico solicitado


#Nó pronto
TAG_NODE_READY = 20

#Eleição e requisição de metadados
TAG_ELECTION_START = 21   #Pedido de eleição (ELECTION)
TAG_ELECTION_RANK = 22    #Resposta indicando que está vivo (ANSWER)
TAG_TORRENT_META_REQ = 23  #Solicitação de metadados do torrent
TAG_LEADER_ANNOUNCE = 24   #Anúncio do novo líder (COORDINATOR)
TAG_ELECTION_CONTEXT = 25  #Envio do contexto durante eleição
TAG_LEADER_QUERY = 26      #Pergunta quem é o líder
TAG_LEADER_REPLY = 27      #Resposta do líder atual
TAG_CONTEXT_REQ = 28       #Pedido de contexto ao líder
TAG_CONTEXT_RESP = 29      #Resposta de contexto do líder