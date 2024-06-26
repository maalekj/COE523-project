import pandas as pd
from mpi4py import MPI
import hashlib
import time
import argparse

def get_hash_function(algorithm_name):
    """Returns a hash function from hashlib based on the given algorithm name."""
    try:
        return getattr(hashlib, algorithm_name)
    except AttributeError:
        raise ValueError(f"Unsupported hash algorithm: {algorithm_name}")

def main(target_password, salt, is_hashed, hash_algorithm):
    # Initialize MPI
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    # Enable ULFM error handling
    errhandler = MPI.ERRORS_RETURN
    MPI.COMM_WORLD.Set_errhandler(errhandler)

    # Define CSV file and chunk size
    filename = 'passwords.csv'
    chunk_size = 1000

    # Get hash function based on user input
    hash_func = get_hash_function(hash_algorithm)

    # Check if password needs hashing
    if not is_hashed:
        target_password = hash_func((target_password + salt).encode()).hexdigest()

    if rank == 0:
        start_time = time.time()  # Start timing

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
            result = comm.Iprobe(source=MPI.ANY_SOURCE, tag=200)
            if flag:
                if result:
                    print(f"Password found! Stopping all processes.")
                    break

            failed_flag = comm.Iprobe(source=MPI.ANY_SOURCE, tag=77, status=status)
            if status.source in failed_processes:
                continue
            if failed_flag:
                if status.source not in failed_processes:
                    failed_process = status.source
                    failed_processes.append(failed_process)
                    print(f"Process {failed_process} failed. Reassigning tasks.")

        # Signal end of processing to all processes
        for i in range(1, size):
            comm.send(None, dest=i, tag=1)

        end_time = time.time()  # End timing
        print(f"Total execution time: {end_time - start_time} seconds")

    else:
        while True:
            try:
                chunk_data = comm.recv(source=0, tag=MPI.ANY_TAG, status=MPI.Status())
                if chunk_data is None:
                    break

                # if rank == 3:
                #     raise Exception("Simulating process failure")

                for password in chunk_data['password'].values:
                    computed_hash = hash_func((str(password) + salt).encode()).hexdigest()
                    if computed_hash == target_password:
                        print(f"Password found by process {rank}: {password}")
                        comm.send(True, dest=0, tag=200)

                # Notify master the task is done
                comm.send(True, dest=0, tag=201)

            except Exception as e:
                # Handle MPI exceptions, mark the process for failure
                print(f"Failure in process {rank}, notifying master.")
                comm.send(f"Process {rank} failed", dest=0, tag=77)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MPI-based Password Checker")
    parser.add_argument('target_password', type=str, help='Target password hash or plaintext')
    parser.add_argument('salt', type=str, help='Salt to be used for hashing')
    parser.add_argument('--is_hashed', action='store_true', help='Flag to indicate if the target password is already hashed')
    parser.add_argument('--hash_algorithm', default='sha256', type=str, help='Hash algorithm to use (e.g., sha256, md5, sha1)')
    args = parser.parse_args()

    main(args.target_password, args.salt, args.is_hashed, args.hash_algorithm)
