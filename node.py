import hashlib
from mpi4py import MPI
import sys

COMMON_PASSWORDS = ['11111','22222','33333','44444']

# receive hash and salt from command line arguments
hash = sys.argv[1]
salt = sys.argv[2]


passwordFoud = False

comm = MPI.COMM_WORLD
rank = comm.Get_rank() # MPI.COMM_WORLD.Get_rank(): process id within the MPI communicator starting from 0,1,2,3.......
size = comm.Get_size() # Number of Processes in the MPI communicator

if rank == 0:
    print('Number of Processes = ', size)
    print('Rank 0 is sending data to all other processes')

# Scatter the data to all processes
received = comm.scatter(COMMON_PASSWORDS, root=0)


computed_hash = hashlib.sha256((received + salt).encode()).hexdigest()
if computed_hash == hash:
    print('Password found: ',received, " Rank = ",rank)
    passwordFoud = True
    

if not passwordFoud:
    print('Password not found in the chunk of data received by Rank = ',rank)

