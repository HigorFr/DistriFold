from mpi4py import MPI

class MPIConnector:
    def __init__(self, comm):
        self.comm = comm

    #esperar receber
    def send(self, data, dest, tag):
        self.comm.send(data, dest=dest, tag=tag)

    #joga pra fila
    def isend(self, data, dest, tag):
        return self.comm.isend(data, dest=dest, tag=tag)
    

    #Função utilitaria só pra pegar mensagem sem travar
    def check_message(self, source, tag):
        if source is None:
            return None
        if self.comm.iprobe(source=source, tag=tag):
            return self.comm.recv(source=source, tag=tag)
        return None
    



    def check_message_all(self, source, tag):
        if source is None:
            source = MPI.ANY_SOURCE
        if tag is None:
            tag = MPI.ANY_TAG

        status = MPI.Status()
        if self.comm.iprobe(source=source, tag=tag, status=status):
            data = self.comm.recv(
                source=status.Get_source(),
                tag=status.Get_tag(),
                status=status
            )
            return {
                "source": status.Get_source(),
                "tag": status.Get_tag(),
                "data": data
            }

        return None