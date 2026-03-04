from contextlib import contextmanager
from multiprocessing import Process


@contextmanager
def managed_processes(targets):
    processes = [Process(target=t) for t in targets]
    try:
        for p in processes: p.start()
        yield processes
    finally:
        for p in processes: p.join()
