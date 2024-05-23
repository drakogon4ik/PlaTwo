"""
Author: Oleg Shkolnik יא9.
Description: Client for the game PlaTwo working on PyGame
             Client shows waiting screen at the start until the other user connect.
             Then user need to press ready button and client waits for the data from server.
             Client Receives direction of the ball, and it's x coordinate.
             Client saves all data in the list that it clears after ending the game.
             After ending the game user need to press ready button.
             When two users pressed buttons clients sends start messages and receive start data from server.
             If the other user close the game, client sends his user to the start (waiting window).
Date: 23/05/24
"""


import socket
import pygame
import threading
import time
from protocol import *
import re


port = 3969
ip = '172.16.9.215'

WINDOW_WIDTH = 750
WINDOW_HEIGHT = 560

BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
high_plat_color = (105, 144, 128)
down_plat_color = (96, 100, 149)

win_filename = 'win.jpg'
lose_filename = 'lose.jpg'
gray_ball_filename = 'ball2.png'
walls_filename = 'border.png'
loading_filename = 'loading_screen.jpg'
waiting_button_filename = 'waiting_button.png'
ready_button_filename = 'ready_button.png'
play_again_filename = 'play_again.png'

REFRESH_RATE = 250
START_CORDS = (30, 30)


class Ball:
    """
    class for the ball
    """
    def __init__(self):
        self.radius = 52
        self.x = WINDOW_WIDTH / 2
        self.y = WINDOW_HEIGHT / 2

    def move(self, flag_w, flag_h, speed):
        """
        function changes ball's coordinates and checks if ball needs to change direction
        :param flag_w: horizontal direction of the ball
        :param flag_h: vertical direction of the ball
        :param speed: how far does he travel each frame
        :return: direction of the ball
        """
        if flag_w and flag_h:
            self.x += speed
            self.y += speed
            if self.x >= WINDOW_WIDTH - self.radius:
                flag_w = False
            if self.y >= WINDOW_HEIGHT - self.radius:
                flag_h = False
        elif flag_w:
            self.x += speed
            self.y -= speed
            if self.x >= WINDOW_WIDTH-self.radius:
                flag_w = False
            if self.y <= self.radius:
                flag_h = True
        elif flag_h:
            self.x -= speed
            self.y += speed
            if self.x <= self.radius:
                flag_w = True
            if self.y >= WINDOW_HEIGHT-self.radius:
                flag_h = False
        else:
            self.x -= speed
            self.y -= speed
            if self.x <= self.radius:
                flag_w = True
            if self.y <= self.radius:
                flag_h = True
        return flag_w, flag_h

    def get_cords(self):
        return self.x, self.y

    def get_radius(self):
        return self.radius - 30

    def set_coordinates(self, x):
        self.x = x
        self.y = WINDOW_HEIGHT / 2


class Platform:
    """
    class for platforms
    """

    def __init__(self, y):
        self.x = WINDOW_WIDTH / 2
        self.y = y

    def move_left(self):
        if self.x >= 62:
            self.x -= 2

    def move_right(self):
        if self.x <= WINDOW_WIDTH - 62:
            self.x += 2

    def get_left_cords(self):

        return self.x-30, self.y

    def get_right_cords(self):
        return self.x+30, self.y

    def set_default(self):
        self.x = WINDOW_WIDTH / 2


def process_message(message, messages):
    """
    funbction gets message finds in it all words Right and Left and add them, every like another item, to the list
    :param message: message that client gets from the server
    :param messages: list to where function adds the messages
    :return: list with added words Left and Right
    """

    # searching for all times Left or Right is in the message
    matches = re.findall(r'(Left|Right)', message)

    # adding words we found to the list
    messages.extend(matches)

    return messages


def receive_messages(client_socket, messages):
    """
    function gets message, print it and add to the list
    :param client_socket: socket of the client
    :param messages: list with messages from the other client
    """
    while True:
        try:
            message = receive_all(client_socket).decode()
            if message[:4] == 'Left' or message[:5] == 'Right':
                process_message(message, messages)
                print(messages)
            else:
                messages.append(message)
            print(message)
        except Exception as err:
            print('received socket error ' + str(err))
            break


def get_direction(direction):
    """
    function defines start direction of the ball
    :param direction: number from 1 to 4
    :return: flags that are direction of the ball
    """

    flag_w = True
    flag_h = True

    if direction == '2':
        flag_w = True
        flag_h = False

    elif direction == '3':
        flag_w = False
        flag_h = False

    elif direction == '4':
        flag_w = False
        flag_h = True

    return flag_w, flag_h


def coordinate_of_ball(message):
    """
    function checks if the message is x coordinate of the ball (3 digits; from 100-650)
    :param message: message from the server
    :return: true if message is x coordinate and false in the other way
    """
    return (len(message) == 3) and (message[0] == '1' or message[0] == '2' or message[0] == '3' or
                                    message[0] == '4' or message[0] == '5' or message[0] == '6')


def looking_for_direction(messages):
    """
    function pops last item in the list until it is direction of the ball (num 1-4)
    :param messages: list with messages
    """
    while messages[-1] != '1' and messages[-1] != '2' and messages[-1] != '3' and \
            messages[-1] != '4' and messages[-1] != '':
        messages.pop(-1)


def main():

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # connecting socket and starting getting data from the server
        client_socket.connect((ip, port))

        exit_game = False

        data = ['']

        receive_thread = threading.Thread(target=receive_messages, args=(client_socket, data))
        receive_thread.start()

        while not exit_game:

            restart = False
            waiting_finish = False
            first_button_finish = False
            close_game = False

            # game window settings
            pygame.init()
            size = (WINDOW_WIDTH, WINDOW_HEIGHT)
            screen = pygame.display.set_mode(size)
            clock = pygame.time.Clock()
            pygame.display.set_caption('Game')

            # pictures
            win_screen = pygame.image.load(win_filename)
            lose_screen = pygame.image.load(lose_filename)
            gray_ball = pygame.image.load(gray_ball_filename)
            walls = pygame.image.load(walls_filename)
            loading = pygame.image.load(loading_filename)

            # buttons
            waiting_button_image = pygame.image.load(waiting_button_filename)
            again_button_image = pygame.image.load(play_again_filename)
            ready_button_image = pygame.image.load(ready_button_filename)

            first_button = waiting_button_image.get_rect()
            first_button.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)

            second_button = again_button_image.get_rect()
            second_button.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 4 * 3)

            # creating objects ball and platforms
            new_ball = Ball()
            high_platform = Platform(40)
            down_platform = Platform(WINDOW_HEIGHT - 40)

            first_button_pressed = False
            second_client = False

            while not waiting_finish:
                """
                client see waiting window until the server send message (direction of the ball)
                """
                for event in pygame.event.get():

                    if event.type == pygame.QUIT:
                        waiting_finish = True
                        first_button_finish = True
                        close_game = True
                        exit_game = True

                if data[-1] == 'break':
                    restart = True
                    data.pop(-1)

                if len(data) != 1:
                    waiting_finish = True
                screen.blit(loading, START_CORDS)
                pygame.display.flip()

            while not first_button_finish and not restart:
                """
                window with button until two users press on it.
                if one of the users press it, client sends to the server message 'ready'
                and then server resend it to the second client
                """
                for event in pygame.event.get():

                    if event.type == pygame.QUIT:
                        first_button_finish = True
                        close_game = True
                        exit_game = True

                    elif event.type == pygame.MOUSEBUTTONDOWN:

                        if first_button.collidepoint(event.pos):
                            first_button_pressed = True
                            client_socket.send("ready".encode())

                if data[-1] == 'break':
                    restart = True
                    data.pop(-1)

                if data[-1] == "ready":
                    second_client = True

                if second_client and first_button_pressed:
                    first_button_finish = True
                    data.pop(-1)

                screen.fill(BLACK)

                if first_button_pressed:
                    screen.blit(ready_button_image, first_button)
                else:
                    screen.blit(waiting_button_image, first_button)

                pygame.display.flip()

            while not close_game and not restart:
                """
                loop for playing again the game until one of the users closes it
                """

                second_client = False
                second_button_pressed = False

                flag_w = True
                flag_h = True

                start = True
                game_finish = False

                n = 0
                for message in data:
                    if coordinate_of_ball(message):
                        new_ball.set_coordinates(int(message))
                        data.pop(n)
                    n += 1

                high_platform.set_default()
                down_platform.set_default()

                times = 0
                speed = 0.5

                lose_flag = False
                win_flag = False

                looking_for_direction(data)

                while not game_finish and not restart:
                    """
                    code for the game
                    checks every touch of ball with other objects and defines if user lost or won
                    """
                    pick = False
                    for event in pygame.event.get():

                        if event.type == pygame.QUIT:
                            game_finish = True
                            close_game = True
                            win_flag = False
                            lose_flag = False
                            exit_game = True

                    if data[-1] == 'break':
                        restart = True
                        data.pop(-1)

                    if start:
                        direction = data[-1]
                        data.pop(-1)
                        flag_w, flag_h = get_direction(direction)
                        start = False
                        print(flag_w, flag_h)

                    # drawing objects
                    screen.blit(walls, (0, 0))
                    radius = new_ball.get_radius()

                    pygame.draw.line(screen, high_plat_color, (high_platform.get_left_cords()),
                                     (high_platform.get_right_cords()), width=10)
                    pygame.draw.line(screen, down_plat_color, (down_platform.get_left_cords()),
                                     (down_platform.get_right_cords()), width=10)
                    keys = pygame.key.get_pressed()

                    if data[-1] == "Right":
                        high_platform.move_left()
                        data.pop(-1)
                    elif data[-1] == "Left":
                        high_platform.move_right()
                        data.pop(-1)

                    if keys[pygame.K_a]:
                        down_platform.move_left()
                        client_socket.send("Left".encode())
                    elif keys[pygame.K_d]:
                        down_platform.move_right()
                        client_socket.send("Right".encode())

                    for i in range(80):
                        """
                        loop that checks if the ball touched one of the platforms
                        """
                        bx, by = new_ball.get_cords()
                        p1x, p1y = down_platform.get_left_cords()
                        p2x, p2y = high_platform.get_left_cords()
                        if (bx == p1x + i - 9 and by >= p1y - radius - 3) or \
                           (bx == p2x + i - 9 and by <= p2y + radius + 3):
                            pick = True

                    x, y = new_ball.get_cords()

                    if y >= WINDOW_HEIGHT - radius - 35:
                        game_finish = True
                        lose_flag = True

                    if y <= radius + 35:
                        game_finish = True
                        win_flag = True

                    if pick:
                        flag_w = flag_w
                        flag_h = not flag_h
                        flag_w, flag_h = new_ball.move(flag_w, flag_h, speed)
                        times += 1
                    else:
                        flag_w, flag_h = new_ball.move(flag_w, flag_h, speed)

                    if times == 5:
                        times += 1
                        speed += 0.25

                    if times == 11:
                        times += 1
                        speed += 0.5

                    # drawing ball
                    ball_x, ball_y = new_ball.get_cords()
                    screen.blit(gray_ball, (ball_x - radius, ball_y - radius))

                    pygame.display.flip()
                    clock.tick(REFRESH_RATE)

                while lose_flag and not restart:
                    """
                    lose screen also waiting until two users press the button
                    """
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            lose_flag = False
                            close_game = True
                            exit_game = True
                        elif event.type == pygame.MOUSEBUTTONDOWN:
                            if second_button.collidepoint(event.pos):
                                second_button_pressed = True
                                client_socket.send("ready".encode())

                    if data[-1] == 'break':
                        restart = True
                        data.pop(-1)

                    if data[-1] == "ready":
                        second_client = True
                        data.pop(-1)

                    if second_client and second_button_pressed:
                        lose_flag = False

                    screen.blit(lose_screen, START_CORDS)

                    if second_button_pressed:
                        screen.blit(ready_button_image, second_button)
                    else:
                        screen.blit(again_button_image, second_button)

                    pygame.display.flip()

                while win_flag and not restart:
                    """
                    win screen also waiting until two users press the button
                    """
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            win_flag = False
                            close_game = True
                            exit_game = True
                        elif event.type == pygame.MOUSEBUTTONDOWN:
                            if second_button.collidepoint(event.pos):
                                second_button_pressed = True
                                client_socket.send("ready".encode())

                    if data[-1] == 'break':
                        restart = True
                        data.pop(-1)

                    if data[-1] == "ready":
                        second_client = True
                        data.pop(-1)

                    if second_client and second_button_pressed:
                        win_flag = False

                    screen.blit(lose_screen, START_CORDS)

                    screen.blit(win_screen, START_CORDS)

                    if second_button_pressed:
                        screen.blit(ready_button_image, second_button)
                    else:
                        screen.blit(again_button_image, second_button)

                    pygame.display.flip()

                client_socket.send("start".encode())
                time.sleep(1)

            pygame.quit()

            # deleting everything from the list except empty string
            while data[-1] != '':
                data.pop(-1)

    except socket.error as err:
        """
        Send the name of error in error situation
        """
        print('received socket error ' + str(err))

    finally:
        """
        Close the socket anyway
        """
        client_socket.close()


if __name__ == "__main__":
    data = ['']
    assert process_message('LeftLeftRight', data) == ['', 'Left', 'Left', 'Right']
    assert process_message('abcLeft', data) == ['', 'Left', 'Left', 'Right', 'Left']
    assert process_message('abc', data) != ['', 'Left', 'Left', 'Right', 'Left', 'abc']
    assert get_direction('1') == (True, True)
    assert get_direction('2') != (False, False)
    assert coordinate_of_ball('270')
    assert not coordinate_of_ball('10')
    looking_for_direction(data)
    assert data != ['', 'Left', 'Left', 'Right', 'Left', 'abc']
    assert data == ['']
    main()
