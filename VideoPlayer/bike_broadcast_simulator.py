# Copyright (C) 2024 Philip Edwards
import time
import math
import socket

# The IP to broadcast to. This is typically the same as your
# local IP, but with the last number set to 255
BROADCAST_IP = "10.1.50.255"
BROADCAST_PORT = 20203

def send_packets_endlessly():
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Allow the address to be reused
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Enable broadcasting mode
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    # Bind to all interfaces on port 5050
    sock.bind(('', BROADCAST_PORT))
    # Initialize the packet index and count
    packet_idx = 200
    count = 0

    while True:
        print("Broadcasting message...")
        time.sleep(1.0)
        count += 1
        packet_idx += 1
        # Broadcast udp packet
        sock.sendto(f"VBC:{packet_idx},{count}".encode(), (BROADCAST_IP, BROADCAST_PORT))

if __name__ == "__main__":
    send_packets_endlessly()
