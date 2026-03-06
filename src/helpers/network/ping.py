import subprocess


def ping(ip, count=1, timeout=1) -> bool:
    """
    Ping an IP address and return True if reachable, False otherwise.
    Works on Linux/macOS.
    """
    try:
        subprocess.run(
            ["ping", "-c", str(count), "-W", str(timeout), ip],
            stdout=subprocess.DEVNULL,  # hide output
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False
