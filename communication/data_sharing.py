import socket
from typing import Callable

HOST = "127.0.0.1"
PORT = 5000

_CONN_CLOSE_STR = b"###CLOSE###"
_CALLBACKS: dict[str, Callable[[], bytes]] = {}


def add_callback(callback: Callable[[], bytes], name: str | None = None) -> None:
    """Add a callback to the list of callbacks"""

    _CALLBACKS[name or str(callback)] = callback


def remove_callback(name: str) -> None:
    """Remove a callback from the list of callbacks"""

    _CALLBACKS.pop(name, None)


def start_server() -> None:
    """start the server and listen for the incoming data. Call the callbacks with the received data"""

    server_socket = socket.socket()
    server_socket.bind((HOST, PORT))

    server_socket.listen(2)
    conn, _ = server_socket.accept()

    while True:
        try:
            data = conn.recv(1024)
        except (ConnectionResetError, socket.timeout):
            continue

        if not data:
            continue

        if data == _CONN_CLOSE_STR:
            break

        for callback in list(_CALLBACKS.values()):
            callback(data)

    conn.close()


def send_data(data: bytes) -> bool:
    """Send the given data to the server"""

    try:
        client_socket = socket.socket()
        client_socket.connect((HOST, PORT))

        client_socket.send(data)

        client_socket.close()
    except (ConnectionRefusedError, socket.timeout):
        return False

    return True
