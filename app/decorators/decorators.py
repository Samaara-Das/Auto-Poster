import functools
import random
from time import sleep

def rest(func):
    '''This decorator adds a random sleep time between 1 and 2 seconds after the decorated function is called. This was created to reduce the likelihood of the Retry button appearing on X'''
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        sleep_time = random.uniform(1, 2.5)
        print(f'Sleeping for {sleep_time} seconds')
        sleep(sleep_time)
        return result
    return wrapper