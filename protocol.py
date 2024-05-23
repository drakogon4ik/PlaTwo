"""
Author: Oleg Shkolnik יא9.
Description: receive function that make sure that was received all data
Date: 23/05/24
"""


def receive_all(sock, def_size=1024):
    """
    function make sure that we received all information
    :param sock: socket of client
    :param def_size: default type of socket.recv
    :return: all data
    """
    data = b''
    while True:
        chunk = sock.recv(def_size)
        if not chunk:
            break
        data += chunk
        if len(chunk) < def_size:
            break
    return data
