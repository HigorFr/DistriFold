***
Coordenaçaão
1. Mecanismo de Sincronização
R: Não é necessário porque não é necessário uma ordem de estados (não precisam estar sincronizados)

2. Exclusão Mútua (Distribuída):

R: Será necessário exclusão mútua centralizada porque os folds depois de realizados precisam ser recombinados para avaliação final do modelo, e é o líder que vai responsável por isso. Então o modelo centralizado encaixa perfeitamente, pois ele concentrará a operação e o gerenciamento. O recurso compartilhado é o processamento nesse caso.

3. Será necessário algum algoritmo de Eleição? Qual

R: Sim, como teremos um líder, que planejamos que seja tolerante a cadas, será necessário eleger um novo líder para realizar o trabalho de delegação de folds. Acreditamos que um mecanismo simples será útil.#Como a quantidade de máquinas não é muito dinamico, nem tem muitas conexões, a chance de falha é baixa, então um mecanismo desse é mais que suficiente. Assim, teremos um mecanismo de eleição por Bullying

4. Se vai usar pubsub, como será implementado

R: Não vamos usar pub/sub uma vez que a implementação OpenMPI usa MPI (Message Passing Interface) que é dividido por clusters e implementa grupo de processos com identificador $G_{id}$ e $P_{id}$ (que é um tipo de comunicação orientada a mensagens).


Protocolos de disseminação (mais peer-to-peer) / replicação (primário).