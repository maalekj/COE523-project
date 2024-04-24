import pandas as pd
from mpi4py import MPI

def main():
    # Initialize MPI
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    # Define CSV file and chunk size
    filename = '10millionPasswords.csv'
    chunk_size = 1000
    target_password = '1212'  # Define the target password

    found_password = False

    if rank == 0:
        # Read CSV file in master process
        chunks = pd.read_csv(filename, chunksize=chunk_size)

        current_process = 1
        for chunk_data in chunks:
            # Before sending new data, check if password has been found using a non-blocking receive
            status = MPI.Status()
            flag = comm.Iprobe(source=MPI.ANY_SOURCE, tag=0, status=status)
            if flag:
                comm.recv(source=status.Get_source(), tag=0)
                print(f"Password found! Stopping all processes.")
                break

            comm.send(chunk_data, dest=current_process, tag=1)
            current_process = (current_process % (size - 1)) + 1

        # Signal end of chunks to all processes
        for i in range(1, size):
            comm.send(None, dest=i, tag=1)

    else:
        while True:
            status = MPI.Status()
            chunk_data = comm.recv(source=0, tag=MPI.ANY_TAG, status=status)
            if status.Get_tag() == 1:
                if chunk_data is None:
                    break

                # Process chunk data
                if target_password in chunk_data['password'].values:
                    found_password = True
                    print(f"Password found in process {rank}!")
                    for i in range(size):
                        comm.send(True, dest=i, tag=0)
                    break

            elif status.Get_tag() == 0:
                break  # Receive termination signal

if __name__ == "__main__":
    main()
