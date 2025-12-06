import socket
import logging
import protocol  # הפרוטוקול

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.FileHandler('client_log.txt', mode='a', encoding='utf-8')]
)

def receive_response(sock):
    """מקבל תשובה מהשרת. מזהה אם מדובר בתמונה או טקסט."""
    peek = sock.recv(4, socket.MSG_PEEK)
    if not peek:
        return None

    size = int.from_bytes(peek, "big")
    if size > 1000:  # כנראה תמונה
        total = b""
        while len(total) < size + 4:
            chunk = sock.recv(4096)
            if not chunk:
                break
            total += chunk
        return total
    else:
        data1 = sock.recv(4096)
        return data1.decode()

def save_image(image_bytes, filename="received_screenshot.png"):
    with open(filename, "wb") as f:
        f.write(image_bytes)
    print(f"[CLIENT] Image saved as '{filename}'")
    logging.info(f"Image saved as '{filename}' ({len(image_bytes)} bytes)")

def send_command(sock, command):
    sock.sendall(command.encode())
    logging.info(f"Sent command: {command}")

def client_program(host="127.0.0.1", port=6741):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    print(f"[CLIENT] Connected to server {host}:{port}")
    logging.info(f"Connected to server {host}:{port}")

    try:
        while True:
            command = input("Enter command: ").strip()
            if not command:
                continue

            send_command(sock, command)

            if command.upper() == "SEND_PHOTO":
                payloader = receive_response(sock)
                if isinstance(payloader, bytes):
                    image_data = protocol.parse_photo_payload(payloader)
                    save_image(image_data)
                else:
                    stat, data2 = protocol.parse_response(payloader)
                    print(f"[CLIENT] Server response: {stat} - {data2}")
                    logging.info(f"Server response: {stat} - {data2}")
            else:
                response = receive_response(sock)
                stat, data2 = protocol.parse_response(response)
                if protocol.is_error(response):
                    print(f"[CLIENT] Error: {data2}")
                else:
                    print(f"[CLIENT] Response: {data2}")

            if command.upper() == "EXIT":
                logging.info("Exiting client program.")
                break

    except Exception as e:
        print(f"[CLIENT] Error: {e}")
        logging.error(f"Error: {e}")

    finally:
        sock.close()
        print("[CLIENT] Disconnected from server.")
        logging.info("Disconnected from server.")

if __name__ == "__main__":
    test_data = b"12345678"
    payload = protocol.build_photo_payload(test_data)
    extracted = protocol.parse_photo_payload(payload)
    assert extracted == test_data, "parse_photo_payload should correctly extract image bytes"
    resp = protocol.build_response(protocol.STATUS_OK, "Test data")
    status, data = protocol.parse_response(resp)
    assert status == protocol.STATUS_OK, "parse_response should parse status correctly"
    assert data == "Test data", "parse_response should parse data correctly"
    err_resp = protocol.build_error_response("error message")
    err_status, err_data = protocol.parse_response(err_resp)
    assert protocol.is_error(err_resp), "is_error should detect error"
    assert err_data == "error message", "extract_error_message should match"
    client_program()
