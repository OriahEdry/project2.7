"""
author: Oriah Edry
Program name: project 2.7
Description: the protocol for this project
Date: 06/12/2025
"""

import logging

STATUS_OK = "OK"
STATUS_ERROR = "ERROR"
STATUS_NOT_FOUND = "NOT_FOUND"


def build_command(command, arg1="", arg2=""):
    parts = [command, arg1, arg2]
    while parts and parts[-1] == "":
        parts.pop()
    return "|".join(parts)


def build_response(status, data=""):
    return f"{status}|{data}"


def build_error_response(message):
    return build_response(STATUS_ERROR, message)


def is_error(response):
    status, _ = parse_response(response)
    return status == STATUS_ERROR


def extract_error_message(response):
    status, data = parse_response(response)
    if status == STATUS_ERROR:
        return data
    return None


def parse_response(response):
    if isinstance(response, bytes):
        return "BINARY", response
    elif isinstance(response, str):
        parts = response.split("|", 1)
        if len(parts) == 2:
            status, data = parts
        else:
            status, data = parts[0], ""
        return status, data
    else:
        logging.warning("Unknown response type")
        return STATUS_ERROR, "Unknown response type"


def build_photo_payload(image_bytes):
    size = len(image_bytes)
    return size.to_bytes(4, "big") + image_bytes


def parse_photo_payload(payload):
    size = int.from_bytes(payload[:4], "big")
    image_data = payload[4:4 + size]
    return image_data

