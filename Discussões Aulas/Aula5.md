Haverá replicação no projeto?
    Se não, quis as consequências?
    Se sim, quais dados dados serão replicados?

        Sim, as entidades replicadas serão: o contexto do líder (que inclui informações de trabalho, resultados e outros aspectos), já que é necessário uma redundância, caso ele caia e todos os nós devem poder assumir a liderança. Além disso, outra entidade que é replicada é o dataset, que é distribuído entre todos os nós antes dos trabalhos de fold começarem efetivamente.

Qual modelo de consistência será usado? (eventual, forte, causal, etc)

    Consistencia forte no dataset porque é necessário que os dados (dataset) estejam atualizados para os nós processarem as tarefas de fold, e eventual para o contexto do líder, já que não é necessário que esteja atualizado para os nós processarem as tarefas de fold, e o contexto do líder é mais importante para a redundância do que para a consistência, além disso eventualmente todos convergem para ficar  com a época mais atualizada (já que a atualização de contexto demora para acontecer)

Como distribuir as cópias? Estatico ou dinamico?
     
    Conforme sugestão do professor, as cópias do dataset são distribuídas por torreting peer-to-peer começando pelo líder, e depois os nós também passam a se comunicar entre si para distribuir as cópias do dataset. Já contexto do líder é replicado para os nós de forma dinâmica, ou seja, quando o líder atualiza seu contexto, ele replica para os nós, e quando um nó assume como líder, ele replica seu contexto para os outros nós e assim por diante.

Qual protolo de consistência será usado?
    Implementar ou usar uma biblioteca pronta?

    No dataset, é adotado um protocolo de sincronização por barreira (barrier synchronization), p/ todos os nós sincronizarem antes. Para o contexto do líder é utilizado um protocolo Primary-Backup assíncrono baseado em épocas, resultando em consistência eventual. Usa a biblioteca OpenMPI como middleware de comunicação. 
