import threading
import socket
# Now this Host is the IP address of the Server, over which it is running.
# I've user my localhost.
host = "127.0.0.1"
port = 5555 # Choose any random port which is not so common (like 80)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#Bind the server to IP Address
server.bind((host, port))
#Start Listening Mode
server.listen()
#List to contain the Clients getting connected and nicknames
adminpass = "password"
clients = []
nicknames = []
addresses = []
role = []

# 1.Broadcasting Method
def broadcast(message):
    for client in clients:
        client.send(message)

def broadcastexcept(message, exceptt):
    index = 0
    for client in clients:
        if nicknames[index] != exceptt:
            client.send(message)
        index = index + 1

def unicast(message, towho):
    index = 0
    for client in clients:
        if nicknames[index] == towho:
            client.send(message)
        index = index + 1

# 2.Recieving Messages from client then broadcasting
def handle(client):
    while True:
        try:
            msg = message = client.recv(4096)
            if msg.decode('utf-8').startswith('KICK'):
                if nicknames[clients.index(client)] == 'admin':
                    name_to_kick = msg.decode('utf-8')[5:]
                    kick_user(name_to_kick)
                else:
                    client.send('Command Refused!'.encode('utf-8'))
                    kick_user('admin')

            elif msg.decode('utf-8').startswith('YOURKEY'):
                if nicknames[clients.index(client)] != 'admin':
                    kick_user('admin')
                unicast(msg, str(msg.decode('utf-8').split('.')[1]))

            elif msg.decode('utf-8').startswith('GIVEMENUSERS'):
                if nicknames[clients.index(client)] != 'admin':
                    kick_user('admin')
                unicast(f'NUSERS.{len(clients)}'.encode(), 'admin')

            elif msg.decode('utf-8').startswith('GIVEMEKEYS'):
                broadcastexcept('GIVEMEKEY'.encode(), 'admin')

            elif msg.decode('utf-8').startswith('MYKEY'):
                unicast(msg, 'admin')

            elif msg.decode('utf-8').startswith('BAN'):
                if nicknames[clients.index(client)] == 'admin':
                    name_to_ban = msg.decode('utf-8')[4:]
                    kick_user(name_to_ban)
                    with open('bans.txt','a') as f:
                        f.write(f'{name_to_ban}\n')
                    print(f'{name_to_ban} was banned by the Admin!')
                else:
                    client.send('Command Refused!'.encode('utf-8'))
            else:
                broadcast(message)   # As soon as message recieved, broadcast it.

        except:
            if client in clients:
                index = clients.index(client)
                #Index is used to remove client from list after getting diconnected
                client.remove(client)
                client.close
                nickname = nicknames[index]
                broadcast(f'{nickname} left the Chat!'.encode('utf-8'))
                nicknames.remove(nickname)
                break
# Main Recieve method
def recieve():
    while True:
        client, address = server.accept()
        print(f"Connected with {str(address)}")
        # Ask the clients for Nicknames
        client.send('NICK'.encode('utf-8'))
        nickname = client.recv(4096).decode('utf-8')
        # If the Client is an Admin promopt for the password.
        with open('bans.txt', 'r') as f:
            bans = f.readlines()

        if nickname+'\n' in bans:
            client.send('BAN'.encode('utf-8'))
            client.close()
            continue

        if nickname in nicknames:
            client.send('REPEATED'.encode('utf-8'))
            continue

        if nickname == 'admin':
            client.send('PASS'.encode('utf-8'))
            password = client.recv(4096).decode('utf-8')
            # I know it is lame, but my focus is mainly for Chat system and not a Login System
            if password == adminpass:
                client.send('ACCEPTED'.encode('utf-8'))
            else:
                client.send('REFUSE'.encode('utf-8'))
                client.close()
                continue
            role.append("admin")
        else:
            client.send('USER'.encode('utf-8'))
            role.append("user")

        nicknames.append(nickname)
        clients.append(client)
        addresses.append(address)

        if nickname == 'admin':
            print(f'Nickname of the client is {nickname}, entered as admin')
            broadcastexcept(f'\n{nickname} joined the Chat as admin'.encode('utf-8'), nickname)
            client.send('\nConnected to the Server as admin, when everyone connects, type /key!'.encode('utf-8'))
        else:
            print(f'Nickname of the client is {nickname}')
            broadcastexcept(f'\n{nickname} joined the Chat'.encode('utf-8'), nickname)
            client.send('\nConnected to the Server!'.encode('utf-8'))

        # Handling Multiple Clients Simultaneously
        thread = threading.Thread(target=handle, args=(client,))
        thread.start()

def kick_user(name):
    if name in nicknames:
        name_index = nicknames.index(name)
        client_to_kick = clients[name_index]
        clients.remove(client_to_kick)
        client_to_kick.send('You Were Kicked from Chat !'.encode('utf-8'))
        client_to_kick.close()
        nicknames.remove(name)
        broadcast(f'{name} was kicked from the server!'.encode('utf-8'))


#Calling the main method
print('Server is Listening ...')
recieve()