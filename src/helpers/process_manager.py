from contextlib import contextmanager
import multiprocessing as mp
import datetime


@contextmanager
def managed_processes(targets):
    dt = datetime.datetime.now()

    processes = [mp.Process(target=t, args=(dt,)) for t in targets]
    try:
        for p in processes:
            p.start()
        yield processes
    finally:
        for p in processes:
            p.join()
