import pandas as pd
from mpi4py import MPI
import hashlib

def main():
    # Initialize MPI
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    # Enable ULFM error handling
    errhandler = MPI.ERRORS_RETURN
    MPI.COMM_WORLD.Set_errhandler(errhandler)

    # Define CSV file and chunk size
    filename = '10millionPasswords.csv'
    chunk_size = 1000
    target_password = 'b51be2abaaaa125f2ac7458be8161230ddf8246917115684272c0745275401cf'
    salt = 'salt'

    if rank == 0:
        # Read CSV file in master process
        chunks = pd.read_csv(filename, chunksize=chunk_size)
        task_queue = list(enumerate(chunks))  # Create a queue of (index, chunk) pairs
        process_to_tasks = {i: None for i in range(1, size)}  # Track tasks per process
        failed_processes = []

        while task_queue:
            for process in range(1, size):
                if process in failed_processes:
                    continue

                if not task_queue:
                    break
                task_index, chunk_data = task_queue.pop(0)
                try:
                    # Send data to worker
                    comm.send(chunk_data, dest=process, tag=1)
                    process_to_tasks[process] = task_index
                except Exception as e:
                    print(f"Failed to send data to process {process}. Error: {e}")
                    task_queue.append((task_index, chunk_data))  # Requeue the task

            # Check for completed tasks or process failures
            status = MPI.Status()
            flag = comm.Iprobe(source=MPI.ANY_SOURCE, tag=201, status=status)
            if flag:
                result = comm.Iprobe(source=status.source, tag=200)
                if result:
                    print(f"Password found! Stopping all processes.")
                    break

            failed_flag = comm.Iprobe(source=MPI.ANY_SOURCE, tag=77, status=status)
            if failed_flag:
                if status.source not in failed_processes:
                    failed_process = status.source
                    failed_processes.append(failed_process)
                    print(f"Process {failed_process} failed. Reassigning tasks.")

        # Signal end of processing to all processes
        for i in range(1, size):
            comm.send(None, dest=i, tag=1)

    else:
        while True:
            try:
                chunk_data = comm.recv(source=0, tag=MPI.ANY_TAG, status=MPI.Status())
                if rank == 2:
                    raise Exception("Simulated failure")
                if chunk_data is None:
                    break

                for password in chunk_data['password'].values:
                    computed_hash = hashlib.sha256((str(password) + salt).encode()).hexdigest()
                    if computed_hash == target_password:
                        print(f"Password found by process {rank}: {password}")
                        comm.send(True, dest=0, tag=200)
                        return  # Exit after finding the password

                # Notify master the task is done
                comm.send(True, dest=0, tag=201)

            except Exception as e:
                # Handle MPI exceptions, mark the process for failure
                print(f"Failure in process {rank}, notifying master.")
                comm.send(f"Process {rank} failed", dest=0, tag=77)
                break

if __name__ == "__main__":
    main()
