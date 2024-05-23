"""
Author: Oleg Shkolnik יא9.
Description: Server for the game PlaTwo working on PyGame.
             Server that waiting for connections of two users and messages ready.
             It sends all data that he received from one client to another while there two clients connected.
             It sends direction of the ball, and it's x coordinate to the clients at the start of the game.
             When the game ends server waits for ready and start messages of clients to send start data.
             When one of the clients disconnects it sends to the second one command for returning to the start screen
             and waits for another client.
Date: 23/05/24
"""


import socket
import random
import select
from protocol import *


port = 3969
ip = '172.16.9.215'


def random_direction():
    """
    generates number from 1 to 4 which will be direction of the ball
    :return: number from 1 to 4
    """
    return str(random.randint(1, 4))


def change_num(number):
    """
    changes the number depending on its direction
    :param number: random number from 1 to 4
    :return: number with opposite direction (1 and 3) (2 and 4)
    """
    res = ''
    if number == '1':
        res = '3'

    elif number == '3':
        res = '1'

    elif number == '2':
        res = '4'

    elif number == '4':
        res = '2'

    return res


def main():

    start_flag = False
    ball_flag = True

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        server_socket.bind((ip, port))
        server_socket.listen(2)  # listening 2 clients

        # list of sockets to check input/output
        sockets_list = [server_socket]

        print("server is running. Waiting for two clients")

        # dictionary for displaying sockets on client's addresses
        clients = {}

        while True:

            # select to check input/output
            read_sockets, _, _ = select.select(sockets_list, [], [])

            for notified_socket in read_sockets:
                # new connection
                if notified_socket == server_socket:
                    client_socket, client_address = server_socket.accept()
                    print(f"new connection: {client_address}")

                    # adding socket
                    sockets_list.append(client_socket)

                    # saving info about socket in the dictionary
                    clients[client_socket] = client_address

                    # if 2 clients, stop listening for new clients
                    if len(clients) == 2:
                        print('Two clients are connected, sending direction of the ball...')

                        # sending number which is direction of the ball to the both clients
                        num = random_direction()
                        for client_socket in clients:
                            client_socket.send(num.encode())
                            num = change_num(num)

                else:
                    try:
                        # getting data from client
                        message = receive_all(notified_socket)

                        # if client disconnected
                        if not message:
                            print(f"connection is closed: {clients[notified_socket]}")
                            # delete socket from the list and dictionary
                            sockets_list.remove(notified_socket)
                            del clients[notified_socket]

                            # start listening for new clients
                            if len(clients) < 2 and server_socket not in sockets_list:
                                sockets_list.append(server_socket)
                                print('Waiting for the new connection...')

                            continue

                        # identify who send message
                        client_address = clients[notified_socket]

                        print(f"Get message from {client_address}: {message.decode()}")

                        if ball_flag:
                            """
                            in the start of the game, send random x coordinate to the clients
                            """
                            x = random.randint(100, 650)
                            for client_socket in clients:
                                client_socket.send(str(x).encode())
                                x = 750 - x
                            ball_flag = False

                        if message.decode() == 'ready':
                            start_flag = True

                        if start_flag and message.decode() == 'start':
                            """
                            if clients pressed their button - sends direction of the ball
                            """
                            num = random_direction()
                            for client_socket in clients:
                                client_socket.send(num.encode())
                                num = change_num(num)
                                start_flag = False
                                ball_flag = True

                        else:
                            for client_socket in clients:
                                if client_socket != notified_socket:
                                    client_socket.send(message)

                    except socket.error as err:
                        print('received socket error on server socket' + str(err))
                        # delete socket from the list and dictionary
                        sockets_list.remove(notified_socket)
                        del clients[notified_socket]

                        for client_socket in clients:
                            if client_socket != notified_socket:
                                client_socket.send('break'.encode())

                        # start listening for new clients
                        if len(clients) < 2 and server_socket not in sockets_list:
                            sockets_list.append(server_socket)
                            print('Waiting for the new client...')

    except socket.error as err:
        """
        Send the name of error in error situation
        """
        print('received socket error on server socket' + str(err))

    finally:
        server_socket.close()


if __name__ == "__main__":
    assert not random_direction() == '0'
    assert change_num('1') == '3'
    assert change_num('0') == ''
    main()
