from src.devices.audio.audio_device_controller import ADCControllerManager
from src.devices.camera.vendors.hikvision.ds_2dy9250iax_a import DS2DY9250IAXA
from src.devices.camera.ptz_controller import PTZController
from src.network.helpers.networks import get_networks
from src.network.helpers.ping import ping
from src.settings import SETTINGS
from rich.console import Console
from src.logger import logger
from rich.table import Table
from rich.text import Text

import subprocess
import sys
import os

console = Console(force_terminal=True)


# ---------- UTILITIES ----------


def print_current_diagnostic(title: str):
    console.print()
    header = Text("*** [ DIAGNOSING ]: ", style="bold magenta")
    header.append(title, style="magenta")
    console.print(header)
    console.rule(style="dim")


def print_log(shape: str, message: str):
    if shape == "cross":
        symbol = Text("❌", style="red")
    elif shape == "check":
        symbol = Text("✅", style="green")
    else:
        symbol = Text("ℹ️", style="blue")

    log_text = (
        Text("[", style="dim") + symbol + Text("]", style="dim") + Text(f" {message}")
    )
    console.print(log_text)


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
        return {"stdout": result.stdout.strip(), "stderr": "", "success": True}
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {command} -> {e.stderr.strip()}")
        return {"stdout": "", "stderr": e.stderr.strip(), "success": False}


def is_service_active(service: str) -> bool:
    result = run_linux_command(f"systemctl is-active {service}")
    return result["success"] and result["stdout"] == "active"


# ---------- DIAGNOSTICS ----------


def diagnose_networks():
    print_current_diagnostic("Network interfaces and addresses")
    networks = get_networks()
    for interface, nets in networks.items():
        console.print(f"[bold cyan]{interface}[/bold cyan]:")
        for net in nets:
            console.print(f"  {net['network']}")


def diagnose_routing():
    print_current_diagnostic("Network routing table")
    result = run_linux_command("ip route")
    console.print(result["stdout"] or result["stderr"])


def diagnose_firewalld():
    print_current_diagnostic("FirewallD")

    if not is_service_active("firewalld"):
        print_log("info", "Firewalld service inactive")
        return

    print_log("check", "Firewalld service active")

    result = run_linux_command("firewall-cmd --list-all")
    if result["success"]:
        console.print(result["stdout"])
    else:
        print_log("cross", "Failed to retrieve firewall configuration")


def diagnose_rtp_devices(auto: bool = True):
    section_title = (
        "RTP devices (Auto Discover)" if auto else "RTP devices (From Files)"
    )
    print_current_diagnostic(section_title)

    controller_manager = ADCControllerManager()
    if SETTINGS.DEVICES_CONFIG_PATH:
        controller_manager.load_devices_from_files(SETTINGS.DEVICES_CONFIG_PATH)
    else:
        controller_manager.auto_discover()
    devices = controller_manager.adc_devices

    table = Table(show_header=True, header_style="bold cyan")
    headers = [
        "Name",
        "Model",
        "IPv4",
        "Port",
        "Multicast IP",
        "RTP Payload",
        "Interface",
        "Nb Channels",
        "Online",
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
            str(d.nb_channels),
            status,
        )

    console.print(table)

    # Check firewall port status
    if is_service_active("firewalld"):
        for d in devices:
            result = run_linux_command(f"firewall-cmd --query-port={d.port}/udp")
            is_open = result["stdout"].strip() == "yes"
            print_log(
                "check" if is_open else "cross",
                f"Port {d.port}/udp is {'open' if is_open else 'closed'}",
            )


def diagnose_env():
    print_current_diagnostic("Environment")
    current_file_path = os.path.abspath(__file__)
    script_dir = os.path.dirname(current_file_path)
    project_root = os.path.abspath(os.path.join(script_dir, ".."))
    source_file = os.path.join(project_root, ".env")

    if not os.path.exists(source_file):
        print_log("cross", "No .env file found.")
        return

    print_log("check", f"Found .env file at {source_file}")
    console.print(run_linux_command(f"cat {source_file}")["stdout"])


def diagnose_ptz():
    print_current_diagnostic("PTZ")
    res = ping(SETTINGS.PTZ_HOST)
    if res:
        print_log("check", f"PTZ host {SETTINGS.PTZ_HOST} is reachable")
        print_log("info", f"Start client initialization...")
        try:
            PTZController(
                "main_camera",
                DS2DY9250IAXA,
                host=SETTINGS.PTZ_HOST,
                username=SETTINGS.PTZ_USERNAME,
                password=SETTINGS.PTZ_PASSWORD,
                start_azimuth=SETTINGS.PTZ_START_AZIMUTH,
                end_azimuth=SETTINGS.PTZ_END_AZIMUTH,
            )
            print_log("check", "PTZ client initialized")
        except Exception as e:
            print_log("cross", f"Failed to initialize PTZ client: {e}")
    else:
        print_log("cross", f"PTZ host {SETTINGS.PTZ_HOST} is unreachable")


def run_doctor():
    diagnose_networks()
    diagnose_routing()
    diagnose_firewalld()
    diagnose_env()
    diagnose_rtp_devices(auto=True)
    diagnose_rtp_devices(auto=False)
    diagnose_ptz()
    console.rule("[bold magenta]Diagnostics complete[/bold magenta]")
    sys.exit(0)
