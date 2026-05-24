from mpi4py import MPI

TAG_HELLO = 1
TAG_ACK = 2


def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    if rank == 0:
        for dest in range(1, size):
            comm.send("OLa", dest=dest, tag=TAG_HELLO)
        for source in range(1, size):
            msg = comm.recv(source=source, tag=TAG_ACK)
            print(f"Lider recebeu de {source}: {msg}")
    else:
        msg = comm.recv(source=0, tag=TAG_HELLO)
        print(f"Worker {rank} recebeu: {msg}")
        comm.send("RECEBI", dest=0, tag=TAG_ACK)


if __name__ == "__main__":
    main()
