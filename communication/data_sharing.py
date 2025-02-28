"""This module provides a simple way to share data between different python processes using sockets"""

import socket
import threading
from typing import Callable

HOST = "127.0.0.1"
KEY_TRACKER_PORT = 27845


class Informer:
    """A class to inform the other processes about the changes"""

    def __init__(self, port: int = 0) -> None:
        self._is_active = False
        self._port = port
        self._callbacks: dict[str, Callable[[bytes], None]] = {}

    @property
    def port(self) -> int:
        """Get the port number"""
        return self._port

    @classmethod
    def send_data(cls, data: bytes, port: int) -> bool:
        """Send the given data to the server"""

        try:
            client_socket = socket.socket()
            client_socket.connect((HOST, port))

            client_socket.send(data)

            client_socket.close()
        except (ConnectionRefusedError, socket.timeout):
            return False

        return True

    def add_callback(self, callback: Callable[[bytes], None], name: str | None = None) -> None:
        """Add a callback to the list of callbacks"""

        self._callbacks[name or str(callback)] = callback

    def remove_callback(self, name_or_callback: str | Callable[[bytes], None]) -> None:
        """Remove a callback from the list of callbacks"""

        if isinstance(name_or_callback, str):
            self._callbacks.pop(name_or_callback, None)
        else:
            self._callbacks.pop(str(name_or_callback), None)

    def start_server(self) -> None:
        """start the server and listen for the incoming data. Call the callbacks with the received data"""

        self._is_active = True
        threading.Thread(target=self._start_server_in_bg, daemon=True).start()

    def shutdown(self) -> None:
        """Shutdown the server"""

        self._is_active = False

    def _start_server_in_bg(self) -> None:
        server_socket = socket.socket()
        server_socket.bind((HOST, self._port))
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.listen(10)

        if self._port == 0:
            self._port = server_socket.getsockname()[1]

        while self._is_active:
            conn, _ = server_socket.accept()

            client_thread = threading.Thread(target=self._handle_client, args=(conn,))
            client_thread.start()

        server_socket.close()

    def _handle_client(self, conn: socket.socket) -> None:
        """Handle a single client connection"""

        while self._is_active:
            try:
                data = conn.recv(1024)
            except (ConnectionResetError, socket.timeout):
                break

            if not data:
                continue

            for callback in list(self._callbacks.values()):
                callback(data)

        conn.close()
