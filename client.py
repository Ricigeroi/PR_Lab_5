import base64
import json
import os
import socket
import threading

# Define the server IP and port
HOST = '127.0.0.1'
PORT = 12345

# Initialize and set up the client socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
client_socket.connect((HOST, PORT))
print(f"Connected to {HOST}:{PORT}")

# Function to send a connection message to the server with the user's name and desired chat room
def send_connect_message():
    client_name = input("Enter your username: ")
    room_name = input("Enter the room name: ")

    connect_message = {
        "message_type": "connect",
        "payload": {
            "name": client_name,
            "room": room_name
        }
    }

    client_socket.send(json.dumps(connect_message).encode('utf-8'))

    return client_name, room_name

# Function to send a chat message to the server
def send_message():
    message = {
        "message_type": "message",
        "payload": {
            "text": text
        }
    }
    client_socket.send(json.dumps(message).encode('utf-8'))

# Function to send a file to the server
def send_file(path, name):
    with open(path, "rb") as file:
        content = base64.b64encode(file.read()).decode('utf-8')

    upload_file_message = {
        "message_type": "upload",
        "payload": {
            "file_name": name,
            "file_content": content,
        }
    }

    client_socket.send(json.dumps(upload_file_message).encode('utf-8'))

# Function to save a file received from the server
def download_file(payload, client_name):
    name = payload.get("file_name")
    content = payload.get("file_content")

    if not os.path.exists(f"files_{client_name}"):
        os.makedirs(f"files_{client_name}")

    with open(os.path.join(f"files_{client_name}", name), "wb") as file:
        file.write(base64.b64decode(content))

    print(f"\nReceived file: {name}")

# Function to list files in a given local directory
def list_client_files(folder_path):
    files = []
    for filename in os.listdir(folder_path):
        if os.path.isfile(os.path.join(folder_path, filename)):
            files.append(filename)
    return files

# Function to display list of files on the server
def list_server_files(payload):
    server_files = payload.get("files", [])

    if server_files:
        print("\nAvailable server files:")
        for i, name in enumerate(server_files, start=1):
            print(f"{i}. {name}")
    else:
        print("\nNo files available on the server.")

# Function to request a list of files available on the server
def request_server_list():
    files_list_request = {
        "message_type": "server_files_list",
        "payload": {}
    }

    client_socket.send(json.dumps(files_list_request).encode('utf-8'))

# Function to request a specific file from the server
def request_server_file(name):
    download_file_request = {
        "message_type": "download_file",
        "payload": {
            "file_name": name
        }
    }
    client_socket.send(json.dumps(download_file_request).encode('utf-8'))

# Function to display a message from the server
def get_server_message(payload):
    message = payload.get("message")
    print(f"\n{message}")

# Function to display a chat message from another user in the chat room
def get_room_message(payload):
    message = payload.get("message")
    sender = payload.get("sender")
    print(f"\n{sender}: {message}")

# Function to get the file path for uploading to the server
def get_file_path():
    file_path = input("Enter the path to the file: ")
    if not file_path:
        print("Invalid file path.")
        return

    if not os.path.exists(file_path):
        print("File not found.")
        return

    return file_path

# Function to continuously listen for messages from the server
def receive_messages():
    while True:
        message = client_socket.recv(262144).decode('utf-8')

        if not message:
            break

        try:
            message_dict = json.loads(message)
            message_type = message_dict.get("message_type")
            payload = message_dict.get("payload")

            # Process received message based on its type
            if message_type == "file":
                download_file(payload, username)
            elif message_type == "server_files_list":
                list_server_files(payload)
            elif message_type == "connect_ack":
                get_server_message(payload)
            elif message_type == "notification":
                get_server_message(payload)
            elif message_type == "message":
                get_room_message(payload)

        except json.JSONDecodeError:
            print(f"\nReceived: {message}")

# Function to handle file upload
def create_upload():
    file_path = get_file_path()

    if not file_path:
        return

    file_name = os.path.basename(file_path)
    send_file(file_path, file_name)

# Start the thread to receive messages from the server
receive_thread = threading.Thread(target=receive_messages)
receive_thread.daemon = True
receive_thread.start()

# Connect to the server
username, room = send_connect_message()

# Main loop to send messages or files, or request files from the server
while True:
    text = input("Enter a message ('exit', 'u' - upload, 'l' - list or 'd' - download): ")

    if not text:
        continue

    if text.lower() == 'exit':
        break
    elif text.lower() == 'u':
        create_upload()
    elif text.lower() == 'l':
        request_server_list()
    elif text.lower() == 'd':
        file_name = input("Enter the name of the file to download: ")
        if not file_name:
            print("Invalid file name.")
            continue
        request_server_file(file_name)
    else:
        send_message()

# Close the connection
client_socket.close()
