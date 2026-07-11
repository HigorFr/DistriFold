import os
import json
import time

TAG_NAMES = {
    1: "PING",
    2: "ACK",
    3: "TASK_ASSIGN",
    4: "RESULT",
    5: "STATE_SYNC",
    6: "TASK_CONFIG",
    10: "TORRENT_META",
    11: "TORRENT_SEED",
    12: "TORRENT_HAVE",
    13: "TORRENT_REQ",
    14: "TORRENT_PIECE",
    20: "NODE_READY",
    21: "ELECTION_START",
    22: "ELECTION_RANK",
    23: "TORRENT_META_REQ",
    24: "LEADER_ANNOUNCE",
    25: "ELECTION_CONTEXT",
    26: "LEADER_QUERY",
    27: "LEADER_REPLY",
    28: "CONTEXT_REQ",
    29: "CONTEXT_RESP"
}

class VisualizerLogger:
    def __init__(self, rank):
        self.rank = rank
        self.enabled = True
        try:
            src_dir = os.path.dirname(os.path.abspath(__file__))
            self.log_dir = os.path.join(src_dir, "Locals", f"Rank {rank}")
            os.makedirs(self.log_dir, exist_ok=True)
            self.log_path = os.path.join(self.log_dir, "visual_events.jsonl")
            
            # Remove o log de execução anterior se ele existir para iniciar limpo
            if os.path.exists(self.log_path):
                try:
                    os.remove(self.log_path)
                except Exception:
                    pass
        except Exception as e:
            # Print warning to stdout but do not crash the node execution
            print(f"[VisualizerLogger] Rank {rank}: Aviso: Falha ao inicializar o logger de visualização ({e}). Visualização desativada para este nó.")
            self.enabled = False

    def log_event(self, event_type, **kwargs):
        if not self.enabled:
            return
        event = {
            "time": time.time(),
            "type": event_type,
            "rank": self.rank,
            **kwargs
        }
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")
        except Exception:
            # Prevent visual logging failures from interrupting core execution
            pass
