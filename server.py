import base64
import json
import os
import socket
import threading

# Defining the IP and Port for the server to listen on
HOST = '127.0.0.1'
PORT = 12345

# Initializing the server socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen()
print(f"Server is listening on {HOST}:{PORT}")

# Dictionaries to manage clients, rooms, and user information
clients = {}
rooms = {}
users = {}


# Function to create a directory if it doesn't exist
def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)


# Function to list files available in a server room
def list_server_files(client_socket):
    create_directory("files")
    room_name = clients.get(client_socket)
    room_dir = os.path.join("files", room_name)
    files = []
    if os.path.exists(room_dir):
        for filename in os.listdir(room_dir):
            if os.path.isfile(os.path.join(room_dir, filename)):
                files.append(filename)
    return files


# Function to handle file uploads from clients
def handle_file_upload(payload, client_socket):
    file_name = payload.get("file_name")
    room_name = clients.get(client_socket)
    file_content = payload.get("file_content")
    sender = users[client_socket]
    if not room_name:
        return
    create_directory("files")
    room_dir = os.path.join("files", room_name)
    create_directory(room_dir)
    with open(os.path.join(room_dir, file_name), "wb") as file:
        file.write(base64.b64decode(file_content))
    message_user = f"{sender} uploaded the file: {file_name}"
    if room_name in rooms:
        for client in rooms[room_name]:
            if client != client_socket:
                client.send(message_user.encode('utf-8'))


# Function to send a file to a client
def send_file_to_client(file_name, file_content, client_socket):
    file_message = {
        "message_type": "file",
        "payload": {
            "file_name": file_name,
            "file_content": file_content,
        }
    }
    client_socket.send(json.dumps(file_message).encode('utf-8'))


# Function to send a file to a client for download
def send_download_file(payload, client_socket):
    create_directory("files")
    room_name = clients.get(client_socket)
    if not room_name:
        client_socket.send("File not found".encode('utf-8'))
        return
    file_name = payload.get("file_name")
    room_dir = os.path.join("files", room_name)
    create_directory(room_dir)
    if os.path.exists(os.path.join(room_dir, file_name)):
        with open(os.path.join(room_dir, file_name), "rb") as file:
            file_content = base64.b64encode(file.read()).decode('utf-8')
            send_file_to_client(file_name, file_content, client_socket)
    else:
        client_socket.send("File not found".encode('utf-8'))


# Function to send a list of files available in the server room to a client
def send_server_list(client_socket):
    server_files = list_server_files(client_socket)
    if not server_files or len(server_files) == 0:
        client_socket.send("No files found".encode('utf-8'))
        return
    files_list_message = {
        "message_type": "server_files_list",
        "payload": {
            "files": server_files
        }
    }
    client_socket.send(json.dumps(files_list_message).encode('utf-8'))


# Function to send a message to all clients in a room except the sender
def send_message_broadcast(payload, client_socket):
    text = payload.get("text")
    room = clients.get(client_socket)
    sender = users[client_socket]
    message = {
        "message_type": "message",
        "payload": {
            "sender": sender,
            "room": room,
            "message": text
        }
    }
    if room in rooms:
        for client in rooms[room]:
            if client != client_socket:
                client.send(json.dumps(message).encode('utf-8'))


# Function to send a notification to all clients in a room about a new connection
def send_connection_broadcast(payload, client_socket):
    client_name = payload.get("name")
    room_name = payload.get("room")
    if room_name not in rooms:
        rooms[room_name] = []
    rooms[room_name].append(client_socket)
    clients[client_socket] = room_name
    users[client_socket] = client_name
    notification_message = f"{client_name} has joined the room."
    for client in rooms[room_name]:
        if client != client_socket:
            send_notification(client, notification_message)


# Function to send a connection acknowledgment to a client
def send_connection_message():
    message = "Connected to the room."
    connect_ack_message = {
        "message_type": "connect_ack",
        "payload": {
            "message": message
        }
    }
    client_socket.send(json.dumps(connect_ack_message).encode('utf-8'))


# Function to send a general notification to a client
def send_notification(client_socket, notification_message):
    notification = {
        "message_type": "notification",
        "payload": {
            "message": notification_message
        }
    }
    client_socket.send(json.dumps(notification).encode('utf-8'))


# Function to handle each client's requests
def handle_client(client_socket, client_address):
    print(f"Accepted connection from {client_address}")
    try:
        while True:
            message = client_socket.recv(262144).decode('utf-8')
            if not message:
                break
            print(f"Received from {client_address}: {message}")
            try:
                message_dict = json.loads(message)
                message_type = message_dict.get("message_type")
                payload = message_dict.get("payload")
                if message_type == "connect":
                    send_connection_broadcast(payload, client_socket)
                elif message_type == "message":
                    send_message_broadcast(payload, client_socket)
                elif message_type == "upload":
                    handle_file_upload(payload, client_socket)
                elif message_type == "server_files_list":
                    send_server_list(client_socket)
                elif message_type == "download_file":
                    send_download_file(payload, client_socket)
            except json.JSONDecodeError:
                pass
    except Exception as e:
        print(f"Error handling client {client_address}: {e}")
    finally:
        room_name = clients.get(client_socket)
        if room_name:
            rooms[room_name].remove(client_socket)
            username = users[client_socket]
            notification_message = f"{username} has left the room."
            del clients[client_socket]
            del users[client_socket]
            for client in rooms[room_name]:
                send_notification(client, notification_message)
        client_socket.close()


# Main loop to accept new client connections
while True:
    client_socket, client_address = server_socket.accept()
    clients[client_socket] = None
    client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
    client_thread.start()
