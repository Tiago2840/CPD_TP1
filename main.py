import random
import math
import time
from multiprocessing import Process, Manager


def miller_rabin(n, k=2):
    # Check immediately if 'n' is 2 or 3, which are known small prime numbers.
    if n == 2 or n == 3:
        return True
    # Return False if 'n' is less than 2 or even, since no even number greater than 2 can be prime.
    if n < 2 or n % 2 == 0:
        return False

    # Decompose (n-1) into 2^s * d where 'd' is odd. This is part of the test setup.
    s, d = 0, n - 1
    while d % 2 == 0:
        d //= 2  # Keep halving 'd' until it's odd.
        s += 1  # Count how many times 'd' was halved to make it odd.

    # Conduct 'k' independent tests to improve the accuracy of the primality decision.
    for _ in range(k):
        a = random.randint(2, n - 2)  # Pick a random integer 'a' between 2 and n-2.
        x = pow(a, d, n)  # Compute a^d % n efficiently using modular exponentiation.
        if x == 1 or x == n - 1:
            continue  # If 'x' is 1 or n-1, this 'a' is a strong witness for n being prime.

        # Repeat squaring 'x' to see if we can find n-1, which would imply n might be prime.
        for _ in range(s - 1):
            x = pow(x, 2, n)  # Square 'x' and reduce modulo 'n'.
            if x == n - 1:
                break  # If x becomes n-1, this round is inconclusive; move to the next round.
        else:
            # If none of the squaring results in n-1, then n is definitely not prime.
            return False

    # If we have performed all 'k' rounds and didn't conclusively prove n is composite,
    # assume n is prime. The probability that n is not prime decreases with more rounds.
    return True


def prime_search(start, end, shared_dict, timeout):
    # Adjust start to the nearest odd number if it is even because even numbers greater than 2 cannot be prime.
    if start % 2 == 0:
        start += 1

    max_prime = start  # Initialize max_prime to the start value. This will track the largest prime found in this process.
    time_limit = time.time() + timeout  # Set a time limit for the prime search to manage execution time effectively.

    i = start  # Start checking from the first odd number in the given range.
    while i <= end and time.time() < time_limit:
        # Check if the current number 'i' is prime using the Miller-Rabin primality test.
        if miller_rabin(i):
            # Acquire the lock to safely update the shared dictionary across multiple processes.
            with shared_dict['lock']:
                # If 'i' is greater than the current 'max_prime' recorded in the shared dictionary, update it.
                if i > shared_dict['max_prime']:
                    shared_dict['max_prime'] = i
        # Increment by 2 to check only odd numbers (even numbers are not prime except 2).
        i += 2


def find_prime(timeout, num_processes):
    # Create a manager to handle shared data between processes
    manager = Manager()
    shared_dict = manager.dict()
    shared_dict['max_prime'] = 2  # Initialize the maximum prime found to the smallest prime number
    shared_dict['lock'] = manager.Lock()  # Lock for synchronizing access to the shared dictionary

    processes = []
    # Calculate the range each process will handle; 2**80 is an arbitrarily large number, representing a large range limit
    range_per_process = math.ceil((2 ** 80) / num_processes)

    # Launch processes to search for primes in parallel
    for i in range(num_processes):
        start = 3 + i * range_per_process  # Calculate the start number for this process, ensuring it starts from an odd number (as even numbers >2 are not prime)
        end = start + range_per_process - 1  # Calculate the end number for this process
        # Create and start a new process
        p = Process(target=prime_search, args=(start, end, shared_dict, timeout))
        processes.append(p)
        p.start()

    # Wait for all processes to complete
    for p in processes:
        p.join()

    # Return the largest prime found across all processes
    return shared_dict['max_prime']


# If this script is run as the main program, execute the function
if __name__ == '__main__':
    print(find_prime(20, 1))
