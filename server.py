"""
author: Oriah Edry
Program name: project 2.7
Description: the server
Date: 06/12/2025
"""
import socket
import glob
import os
import shutil
import subprocess
import pyautogui
import logging
import shlex
import protocol

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.FileHandler('server_log.txt', mode='a', encoding='utf-8')]
)

def create_server_socket(host='127.0.0.1', port=6741):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(1)
    print(f"[SERVER] Listening on {host}:{port}")
    logging.info(f"[SERVER] Listening on {host}:{port}")
    return server_socket

def file_searcher(path):
    try:
        files = glob.glob(rf'{path}\*.*')
        return protocol.build_response(protocol.STATUS_OK, ",".join(files))
    except Exception as e:
        return protocol.build_error_response(str(e))

def file_deleter(path):
    try:
        os.remove(path)
        return protocol.build_response(protocol.STATUS_OK, "True")
    except FileNotFoundError:
        return protocol.build_error_response(f"File '{path}' not found")
    except PermissionError:
        return protocol.build_error_response(f"No permission to delete '{path}'")
    except Exception as e:
        return protocol.build_error_response(str(e))

def file_copy(src, dst):
    try:
        shutil.copy(src, dst)
        return protocol.build_response(protocol.STATUS_OK, "True")
    except FileNotFoundError:
        return protocol.build_error_response(f"Source '{src}' not found")
    except PermissionError:
        return protocol.build_error_response(f"No permission to copy to '{dst}'")
    except Exception as e:
        return protocol.build_error_response(str(e))

def execute_app(app_name):
    exe_path = rf"C:\Windows\System32\{app_name}"
    try:
        subprocess.Popen(exe_path)
        return protocol.build_response(protocol.STATUS_OK, "True")
    except FileNotFoundError:
        return protocol.build_error_response(f"Executable '{exe_path}' not found")
    except PermissionError:
        return protocol.build_error_response(f"No permission to execute '{exe_path}'")
    except Exception as e:
        return protocol.build_error_response(str(e))

def screenshot():
    try:
        img_path = "screen.png"
        image = pyautogui.screenshot()
        image.save(img_path)
        return protocol.build_response(protocol.STATUS_OK, "True")
    except Exception as e:
        return protocol.build_error_response(str(e))

def send_photo():
    img_path = "screen.png"
    try:
        with open(img_path, "rb") as image_file:
            data = image_file.read()
        payloader = protocol.build_photo_payload(data)
        return payloader
    except FileNotFoundError:
        return protocol.build_error_response(f"File '{img_path}' not found")
    except Exception as e:
        return protocol.build_error_response(str(e))

def handle_client(client_socket, client_address):
    print(f"[SERVER] Connected to {client_address}")
    logging.info(f"Connected to {client_address}")

    try:
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            try:
                command_str = data.decode().strip()
            except UnicodeDecodeError:
                client_socket.sendall(protocol.build_error_response("Invalid encoding").encode())
                continue

            logging.info(f"Received command: {command_str}")

            try:
                parts = shlex.split(command_str)
            except ValueError:
                client_socket.sendall(protocol.build_error_response("Invalid command format").encode())
                continue

            cmd = parts[0].upper()
            arg1 = parts[1] if len(parts) > 1 else ""
            arg2 = parts[2] if len(parts) > 2 else ""

            if cmd == "DIR":
                response = file_searcher(arg1)
            elif cmd == "DELETE":
                response = file_deleter(arg1)
            elif cmd == "COPY":
                response = file_copy(arg1, arg2)
            elif cmd == "EXECUTE":
                response = execute_app(arg1)
            elif cmd == "TAKE" and arg1.upper() == "SCREENSHOT":
                response = screenshot()
            elif cmd == "SEND_PHOTO":
                response = send_photo()
            elif cmd == "EXIT":
                break
            else:
                response = protocol.build_error_response("Unknown command")

            # שליחה
            if isinstance(response, bytes):
                client_socket.sendall(response)
            else:
                client_socket.sendall(response.encode())

    except Exception as e:
        logging.error(f"Error handling client {client_address}: {e}")
    finally:
        client_socket.close()
        logging.info(f"Client disconnected: {client_address}")
        print(f"[SERVER] Client disconnected: {client_address}")

def start_server(host='127.0.0.1', port=6741):
    server_socket = create_server_socket(host, port)
    while True:
        print("[SERVER] Waiting for a client...")
        logging.info("Waiting for a client...")
        client_socket, client_address = server_socket.accept()
        handle_client(client_socket, client_address)
        print("[SERVER] Ready for next client")
        logging.info("Ready for next client")


if __name__ == "__main__":
    start_server()
    assert isinstance(file_searcher("C:\\"), str), "DIR should return a response string"

    test_file = "test_file.txt"
    with open(test_file, "w") as f:
        f.write("hello")
    assert file_deleter(test_file).startswith(protocol.STATUS_OK), "DELETE should return OK for existing file"

    with open("src.txt", "w") as f:
        f.write("source")
    dst_file = "dst.txt"
    assert file_copy("src.txt", dst_file).startswith(protocol.STATUS_OK), "COPY should return OK"

    os.remove("src.txt")
    os.remove(dst_file)
    assert execute_app("notepad.exe").startswith(protocol.STATUS_OK), "EXECUTE should return OK"

    assert screenshot().startswith(protocol.STATUS_OK), "Screenshot should return OK"

    pyautogui.screenshot().save("screen.png")
    payload = send_photo()
    assert isinstance(payload, bytes), "send_photo should return bytes"

    os.remove("screen.png")
