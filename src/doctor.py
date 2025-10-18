from src.network.helpers.networks import get_networks
from src.devices.devices import Devices
from src.settings import SETTINGS
from rich.console import Console
from src.logger import logger
from rich.table import Table
from rich.text import Text

import subprocess


console = Console(force_terminal=True)


def print_current_diagnostic(title: str):
    header = Text("*** [ DIAGNOSING ]: ", style="bold magenta")
    header.append(title, style="magenta")
    console.print("\n", header)


def run_linux_command(command):
    try:
        result = subprocess.run(
            command,
            shell=True,
            executable="/bin/bash",
            capture_output=True,
            text=True,
            check=True,
        )
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e.stderr}")


def diagnose_networks():
    print_current_diagnostic("Network interfaces and addresses")
    networks = get_networks()
    for interface, nets in networks.items():
        print(f"{interface}:")
        for net in nets:
            print(f"  {net['network']}")


def diagnose_routing():
    print_current_diagnostic("Network routing table")
    run_linux_command("ip route")


def diagnose_firewalld():
    print_current_diagnostic("FirewallD")
    # TODO: Check firewalld rules


def diagnose_rtp_devices(auto: bool = True):
    if auto:
        print_current_diagnostic("RTP devices (Auto Discover)")
        devices = Devices.auto_discover()
    else:
        print_current_diagnostic("RTP devices (From Files)")
        devices = Devices.load_devices_from_files(SETTINGS.DEVICES_CONFIG_PATH)
    table = Table()
    headers = [
        "Name",
        "model",
        "ipv4",
        "port",
        "multicast_ip",
        "rtp_payload",
        "interface",
        "online",
    ]
    for h in headers:
        table.add_column(h, justify="center")

    for d in devices:
        status = Text("✅", style="green") if d.is_online() else Text("🟥", style="red")
        table.add_row(
            d.name,
            d.model,
            d.ipv4,
            str(d.port),
            d.multicast_ip,
            str(d.rtp_payload),
            d.interface,
            status,
        )

    console.print(table)


def run_doctor():
    diagnose_networks()
    diagnose_routing()
    diagnose_firewalld()
    diagnose_rtp_devices(auto=True)
    diagnose_rtp_devices(auto=False)

    return exit(0)
