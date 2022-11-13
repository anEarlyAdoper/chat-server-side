import threading
from threading import *
import socket

# Now this Host is the IP address of the Server, over which it is running.
# I've user my localhost.
host = "127.0.0.1"
port = 5555  # Choose any random port which is not so common (like 80)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Bind the server to IP Address
server.bind((host, port))
# Start Listening Mode
server.listen()
# List to contain the Clients getting connected and nicknames
adminpass = "password"
clients = []
nicknames = []
addresses = []
role = []
#
semaphore = Semaphore()


# 1.Broadcasting Method
def broadcast(message):
    semaphore.acquire()
    for client in clients:
        client.send(message)
    semaphore.release()


def broadcastexcept(message, exceptt):
    semaphore.acquire()
    index = 0
    for client in clients:
        if nicknames[index] != exceptt:
            client.send(message)
        index = index + 1
    semaphore.release()


def unicast(message, towho):
    semaphore.acquire()
    index = 0
    for client in clients:
        if nicknames[index] == towho:
            client.send(message)
        index = index + 1
    semaphore.release()


# 2.Recieving Messages from client then broadcasting
def handle(client):
    while True:
        try:
            msg = message = client.recv(4096)
            if msg.decode().startswith('KICK'):
                if nicknames[clients.index(client)] == 'admin':
                    name_to_kick = msg.decode()[5:]
                    kick_user(name_to_kick)
                else:
                    client.send('Command Refused!'.encode())
                    kick_user('admin')

            elif msg.decode().startswith('YOURKEY'):
                if nicknames[clients.index(client)] != 'admin':
                    kick_user('admin')
                unicast(msg, str(msg.decode().split('.')[1]))

            elif msg.decode().startswith('GIVEMENUSERS'):
                if nicknames[clients.index(client)] != 'admin':
                    kick_user('admin')
                unicast(f'NUSERS.{len(clients)}'.encode(), 'admin')

            elif msg.decode().startswith('GIVEMEKEYS'):
                broadcastexcept('GIVEMEKEY'.encode(), 'admin')

            elif msg.decode().startswith('MYKEY'):
                unicast(msg, 'admin')

            elif msg.decode().startswith('BAN'):
                if nicknames[clients.index(client)] == 'admin':
                    name_to_ban = msg.decode()[4:]
                    kick_user(name_to_ban)
                    with open('bans.txt', 'a') as f:
                        f.write(f'{name_to_ban}\n')
                    print(f'{name_to_ban} was banned by the Admin!')
                else:
                    client.send('Command Refused!'.encode())
            else:
                broadcast(message)  # As soon as message recieved, broadcast it.

        except ConnectionError:
            semaphore.acquire()
            if client in clients:
                index = clients.index(client)
                # Index is used to remove client from list after getting diconnected
                clients.remove(client)
                nickname = nicknames[index]
                broadcastexcept(f'{nickname} left the Chat!'.encode(), nickname)
                nicknames.remove(nickname)
                break
            semaphore.release()


# Main Recieve method
def recieve():
    while True:
        client, address = server.accept()
        print(f"Connected with {str(address)}")
        # Ask the clients for Nicknames
        client.send('NICK'.encode())
        nickname = client.recv(4096).decode()
        # If the Client is an Admin promopt for the password.
        with open('bans.txt', 'r') as f:
            bans = f.readlines()

        if nickname + '\n' in bans:
            client.send('BAN'.encode())
            client.close()
            continue

        if nickname in nicknames:
            client.send('REPEATED'.encode())
            continue

        if nickname == 'admin':
            client.send('PASS'.encode())
            password = client.recv(4096).decode()
            # I know it is lame, but my focus is mainly for Chat system and not a Login System
            if password == adminpass:
                client.send('ACCEPTED'.encode())
            else:
                client.send('REFUSE'.encode())
                client.close()
                continue
            role.append("admin")
        else:
            client.send('USER'.encode())
            role.append("user")

        nicknames.append(nickname)
        clients.append(client)
        addresses.append(address)

        if nickname == 'admin':
            print(f'Nickname of the client is {nickname}, entered as admin')
            broadcastexcept(f'\n{nickname} joined the Chat as admin'.encode(), nickname)
            client.send('\nConnected to the Server as admin, when everyone connects, type /key!'.encode())
        else:
            print(f'Nickname of the client is {nickname}')
            broadcastexcept(f'\n{nickname} joined the Chat'.encode(), nickname)
            client.send('\nConnected to the Server!'.encode())

        # Handling Multiple Clients Simultaneously
        thread = threading.Thread(target=handle, args=(client,))
        thread.start()


def kick_user(name):
    semaphore.acquire()
    if name in nicknames:
        name_index = nicknames.index(name)
        client_to_kick = clients[name_index]
        clients.remove(client_to_kick)
        client_to_kick.send('You Were Kicked from Chat !'.encode())
        client_to_kick.close()
        nicknames.remove(name)
        broadcast(f'{name} was kicked from the server!'.encode())
    semaphore.release()


# Calling the main method
print('Server is Listening ...')
recieve()
