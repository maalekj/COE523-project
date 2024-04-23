import pandas as pd
from mpi4py import MPI

def main():
    # Initialize MPI
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    # Define CSV file and chunk size
    filename = '10millionPasswords.csv'
    chunk_size = 1000  # Adjust as needed
    target_password = '1212'  # Define the target password

    found_password = False

    if rank == 0:
        # Read CSV file in master process
        chunks = pd.read_csv(filename, chunksize=chunk_size)

        current_process = 1
        # Distribute chunks to other processes
        for chunk_data in chunks:
            if comm.bcast(found_password, root=0):
                print(f"Password found in process {target_password}!")
                break  # Stop if password is found
            comm.send(chunk_data, dest=current_process)
            current_process = (current_process % (size - 1)) + 1

        print('All chunks have been sent to all processes')
        # Signal end of chunks to all processes
        for i in range(1, size):
            comm.send(None, dest=i)

    else:
        # Receive chunks in worker processes
        while True:
            chunk_data = comm.recv(source=0)
            print(f"Process {rank} received chunk data")
            if chunk_data is None:
                break

            # Process chunk data
            if target_password in chunk_data['password'].values:
                found_password = True
                print(f"Password found in process {rank}!")
                comm.bcast(found_password, root=rank)  # Send stop signal

if __name__ == "__main__":
    main()
