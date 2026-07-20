import mpi4py
mpi4py.rc.initialize = False
mpi4py.rc.finalize = True

import sys
import os
import time
import shutil

# Adiciona o diretório 'src' ao path do Python para importações corretas
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

# Para cenários que não testam a distribuição P2P em si, pré-copia o dataset do Rank 0
# para evitar que trabalhadores fiquem presos no download P2P de um líder prestes a cair
test_scenario = os.getenv("DISTRIFOLD_TEST")
if test_scenario and test_scenario != "p2p":
    src_locals = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "Locals")
    rank0_dir = os.path.join(src_locals, "Rank 0")
    os.makedirs(rank0_dir, exist_ok=True)
    rank0_npz = os.path.join(rank0_dir, "breast_cancer.npz")
    if not os.path.exists(rank0_npz):
        try:
            from sklearn.datasets import load_breast_cancer
            import numpy as np
            data = load_breast_cancer()
            np.savez(rank0_npz, X=data.data, y=data.target)
        except Exception:
            pass
    if os.path.exists(rank0_npz):
        for r in range(1, 10):
            r_dir = os.path.join(src_locals, f"Rank {r}")
            os.makedirs(r_dir, exist_ok=True)
            r_npz = os.path.join(r_dir, "breast_cancer.npz")
            if not os.path.exists(r_npz):
                try:
                    shutil.copy(rank0_npz, r_npz)
                except Exception:
                    pass

import node_context
import worker

original_node_context_init = node_context.NodeContext.__init__

def patched_node_context_init(self, rank, size, teste=None):
    test_scenario = os.getenv("DISTRIFOLD_TEST")
    custom_teste = None
    
    if test_scenario in ["eleicao", "falha_leader"]:
        # O líder (rank 0) morre após 3s. Os demais trabalhadores continuam ativos.
        if rank == 0:
            custom_teste = {'time_working': 3, 'time_timeout': 100}
        else:
            custom_teste = {'time_working': 0, 'time_timeout': 0}
    elif test_scenario == "elegibilidade":
        # O líder morre após 3s. Rank 1 é elegível. Rank 2 é forçado a ser inelegível (sem dataset).
        if rank == 0:
            custom_teste = {'time_working': 3, 'time_timeout': 100}
        else:
            custom_teste = {'time_working': 0, 'time_timeout': 0}
    elif test_scenario == "falha_worker":
        # Líder e Rank 2 continuam ativos. Rank 1 morre temporariamente após 3s e volta após 5s.
        if rank == 1:
            custom_teste = {'time_working': 3, 'time_timeout': 5}
        else:
            custom_teste = {'time_working': 0, 'time_timeout': 0}
    elif test_scenario == "recuperacao":
        # Líder continua ativo. Rank 1 morre após 3s e retorna após 4s.
        if rank == 1:
            custom_teste = {'time_working': 3, 'time_timeout': 4}
        else:
            custom_teste = {'time_working': 0, 'time_timeout': 0}
    else:
        # Sem queda simulada
        custom_teste = {'time_working': 0, 'time_timeout': 0}

    original_node_context_init(self, rank, size, teste=custom_teste)

node_context.NodeContext.__init__ = patched_node_context_init

@property
def has_dataset_completed_prop(self):
    no_dataset_rank = os.getenv("DISTRIFOLD_NO_DATASET_WORKER")
    if no_dataset_rank is not None and str(self.rank) == no_dataset_rank:
        return False
    test_scenario = os.getenv("DISTRIFOLD_TEST")
    if test_scenario in ["eleicao", "falha_leader", "elegibilidade"]:
        if self.rank != 0:
            return True
    return getattr(self, "_has_dataset_completed", False)

@has_dataset_completed_prop.setter
def has_dataset_completed_prop(self, val):
    self._has_dataset_completed = val

node_context.NodeContext.has_dataset_completed = has_dataset_completed_prop

original_train_fold_from_arrays = worker.train_fold_from_arrays

def patched_train_fold_from_arrays(X, y, train_idx, test_idx, config, fold_id=None):
    from mpi4py import MPI
    rank = MPI.COMM_WORLD.Get_rank()
    slow_rank = os.getenv("DISTRIFOLD_SLOW_WORKER")
    if slow_rank is not None and str(rank) == slow_rank:
        print(f"[TEST MONKEYPATCH] Rank {rank} simulando lentidão (dormindo por 2s antes do treino)...")
        time.sleep(2.0)
    return original_train_fold_from_arrays(X, y, train_idx, test_idx, config, fold_id)

worker.train_fold_from_arrays = patched_train_fold_from_arrays

import MPI_start

if __name__ == "__main__":
    import threading
    def auto_stopper():
        # Encerra os processos suavemente após tempo suficiente para concluir o cenário
        t_max = 14.0
        if test_scenario in ["falha_worker", "recuperacao", "falha_leader"]:
            t_max = 18.0
        time.sleep(t_max)
        os._exit(0)
        
    threading.Thread(target=auto_stopper, daemon=True).start()
    MPI_start.main()
