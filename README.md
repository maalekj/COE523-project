# Distributed Password Strength Checker

## Overview
The Distributed Password Strength Checker is a system designed to assess the security of passwords used on various websites. Utilizing a distributed computing approach, this system checks passwords in parallel, efficiently identifying weak passwords and enhancing online security.

## Features
- **Distributed Computing:** Leverages multiple nodes to process large datasets of passwords swiftly.
- **Scalable Architecture:** Scales dynamically with the number of processing nodes to handle varying loads.
- **Comprehensive Password Evaluation:** Uses cryptographic hash functions and custom algorithms to evaluate password strength against common attack vectors.

## Technologies Used
- **Python:** Primary programming language.
- **MPI (Message Passing Interface):** Used for managing parallel processes via `mpi4py`.
- **Pandas:** Utilized for efficient data handling and operations on large datasets.
- **Hashlib:** Provides hashing functions to check password integrity and strength.

## Installation

### Prerequisites
- Python 3.x
- mpi4py
- Pandas

To set up the necessary environment, run the following commands:

```bash
pip install mpi4py pandas
```

## Usage

To run the system, use the following command:

```bash
mpiexec -n <number_of_processes> python password_checker.py 'your_password' 'your_salt' --hash_algorithm sha256
```
Replace `<number_of_processes>` with the number of worker nodes you want to use. Adjust `'your_password'` and `'your_salt'` as required. Include the `--is_hashed` flag if your password is already hashed.

## Testing

To test the system's functionality:
- Ensure correct identification of password strength.
- Test with varying numbers of nodes to assess scalability and efficiency.
- Simulate node failures to verify system robustness.