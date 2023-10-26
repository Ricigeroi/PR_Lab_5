# PR_Lab_5

## Overview
This repository contains a simple client-server chat application implemented in Python. The application allows users to connect to a chat room, send and receive messages, and upload or download files.

## Features
- **Client-Server Architecture**: The application follows a client-server model where multiple clients can connect to a server and communicate in a chat room.
- **File Sharing**: Clients can upload files to the server and download files from the server.
- **Dynamic Chat Rooms**: Users can specify the chat room they wish to join or create a new one.
- **Notifications**: The application provides notifications for user activities such as joining or leaving a chat room.

## Files
- [client.py](https://github.com/Ricigeroi/PR_Lab_5/blob/master/client.py): Contains the implementation of the client-side logic. It allows users to connect to a server, send/receive messages, and handle file uploads/downloads.
- [server.py](https://github.com/Ricigeroi/PR_Lab_5/blob/master/server.py): Contains the server-side logic. It listens for incoming client connections, manages chat rooms, and handles client requests.

## Usage
1. Start the server by running `server.py`.
2. Start the client by running `client.py`.
3. Follow the prompts to enter your username and desired chat room.
4. Use the provided commands to send messages, upload files, list available files, or download files.
