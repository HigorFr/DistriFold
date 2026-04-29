# DistriFold

***
Desenvolvendo um projeto de sistemas distribuidos.

# Ideia inicial:

O projeto é sobre construir uma rede distribuida de treinamento descentralizado de modelos de IA pela técnica de k-fold cross-validation, em que os k folds são distribuídos por entre as máquinas. Essa técnica serve para mitigar viéses na separação de treino/teste, de forma que o modelo possa ser mensurado com maior acurácia. Contudo, isso demanda um tempo de treinamento bem maior, mas que pode ser acelerado por meio da paralelização dos folds em diferentes nós. 


Preciso de uma reestruração das ideias, segundo comentários do professor:

Me parece um bom caso de uso para aplicar o OpenMPI (mas fiquem a vontade para fazer diferente).

Se entendi bem o problema, o processamento de cada trabalhador pode ser agregado individualmente, tornando o problema monotônico (ou seja, a ordem não importa muito, desde que todos os resultados aconteçam), onde a consistência eventual é suficiente.

Detalhe: o termo mestre-escravo está caindo em desuso, dando preferência para líder-seguidor ou similares.

E as especificações
(1) Dos modelos estudados algum se encaixa (em camadas / microserviços / pub sub peer-to-peer (estruturado ou não) )
- Líder-seguidor
(2) Arquitetura de software interna
(3) Como o sistema será testado?
* **Testes de Escalabilidade (Speedup):** Medir o tempo de treinamento com 1, 2, 4 e 8 nós. O objetivo é observar um speedup próximo do linear ($T_{total} \approx T_{1fold} \times (K/N)$
* **Testes de Tolerância a Falhas (Resiliência):** Se um Seguidor cair no meio do treino do Fold 3, o Coordenador consegue detectar o _timeout_ e reatribuir esse fold para outro nó? Isso valida a **consistência eventual**.
(4) Faz sentido usar algum tipo de middleware?
* Sim, o **OpenMPI (Recomendação do Professor):** É o padrão ouro para computação de alto desempenho (HPC). Ele gerencia a execução paralela e oferece primitivas como `bcast` (enviar dados para todos) e `gather` (coletar resultados de todos). Em Python, você usaria o `mpi4py`.

Ideias: K-folds + ensemble de votação
* Primeiro focar em fazer k-fold com rede neural (se sobrar tempo faz ensemble com árvores de decisão);
* K-fold para reduzir viés;
* Votação/média para juntar os folds.

"O sistema consistirá em uma arquitetura **Líder-Seguidor** mediada por **OpenMPI**, onde o particionamento dos dados segue um modelo **monotônico**. A consistência é garantida de forma **eventual**: o estado global do modelo só é consolidado após a unificação dos resultados parciais, permitindo que falhas individuais de nós sejam resolvidas por re-execução sem comprometer a integridade estatística do Cross-Validation."

OpenMPI tem uma fila para gerenciar os folds caso algum cair?
* Se um processo morre em um job MPI padrão, o comportamento padrão é que **toda a aplicação seja interrompida** para evitar corrupção de dados ou estados inconsistentes. Para o seu projeto de sistemas distribuídos, você tem dois caminhos para resolver isso e atender ao que o seu professor sugeriu:
	* (1)-**Líder Dinâmico:** Em vez de distribuir todos os folds de uma vez (`scatter`), o Líder mantém uma lista de folds pendentes.
	* (2) **Solicitação de Carga:** Os Seguidores enviam uma mensagem: "Estou ocioso, mande um fold".
	* (3) - **Timeout:** O Líder registra o tempo. Se o Seguidor $X$ não devolver o resultado em $N$ minutos, o Líder coloca o fold $X$ de volta na lista de "pendentes" para outro Seguidor pegar.
* redundância do lider
