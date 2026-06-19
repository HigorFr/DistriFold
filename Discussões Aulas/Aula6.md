#Tolerância a Falhas

#Para seu projeto, é mais importante disponibilidade ou confiabilidade.
    #No geral, por se tratar especificamente de divisão de folds para o treinamento ds IA, confiabilidade dos dados é claramente mais importante que a disponibilidade, até porque a única consequencia de uma falta de disponibilidade é a perda de poder de processamento, já que a tarefa por essência não interfere entre sí, sendo bem paralaela.


#Quais tipos de falha deseja-te Totelerar? (Crash, omissão temporal, resposta, bizantina)
    #Em teoria, qualquer tipo de falha que impessa o envio de dados, isto é, Crash, Omissão Temporal, Falta de resposta etc... Já que quando qualquer nó cai, isso é detectado via um Heartbeat feito manualmente, e é só necessário reenviar o trabalho para outro tralhador disponível. Isso vale tanto para o líder, que sempre envia um contexto atualizado, tanto para o trabalhador. Mesmo na hipotese de do líder caí antes de atualizar o contexto, não terá problema. 


#Quantos processos falhantes serão suportados?
    #O processo de envio e recebimento de dataset, que ocorre via p2p, ou seja, o swarm naturalmente ignora falhas, pois haverá outros nós com o dataset para substitui-lo (O que só não funcionará se NEHUM nó possui aquela parte esepecifica do dataset). O líder também terá suporte á falhas, já que todo contexto calculado por ele será enviado para os trabalhadores para que qualquer um possa substitui-lo (Via eleição por builling caso ele caia.) E como mencionado anteriormente, caso o worker caia, ele simplesmente será ignorado pelo líder até retornar. 

#Qual estrategia para detectar falhar?
    A única estratégia, e acreditamos que mais que suficnete é utiliar um timeout desde o último "heartbeat" de cada nó, tanto do Worker para o líder, tanto do Líder para o worker.

