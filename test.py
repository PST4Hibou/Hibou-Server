import socket

IP = "192.168.250.15"
PORT = 49280


def send_command(message):
    message = " " + message + "\n"
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)
            s.connect((IP, PORT))
            s.sendall(message.encode())
            print(f"Sent: {message}")
            return s.recv(1024)
    except Exception as e:
        print(f"Error: {e}")


def set_phantom_power(channel_index, state):
    message = f"set IO:Current/InCh/48VOn {channel_index} 0 {state}"
    send_command(message)


def set_hagain(channel_index, state):
    message = f"set IO:Current/InCh/HAGain {channel_index} 0 {state}"
    send_command(message)


def get_general_phantom_power():
    message = f"get IO:Current/Dev/48VMasterOn 0 0"
    result = send_command(message)
    if not result:
        return
    is_general_phantom_power_powered_on = (
        result.decode().replace("\n", "").split(" ")[-1] == "1"
    )
    return is_general_phantom_power_powered_on


set_phantom_power(0, 0)
set_hagain(1, 10)
print(get_general_phantom_power())
