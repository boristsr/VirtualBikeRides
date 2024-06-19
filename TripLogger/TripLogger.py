# Copyright (C) 2024 Philip Edwards
import time
import json
import socket
import threading
import signal
import sys

def parse_json_into_pyobject(json_str):
    # Snippet from: https://stackoverflow.com/a/15882054
    from types import SimpleNamespace

    # Parse JSON into an object with attributes corresponding to dict keys.
    new_obj = json.loads(json_str, object_hook=lambda d: SimpleNamespace(**d))

    return new_obj

def load_config(config_path: str = 'config.json'):
    try:
        with open('config.json', 'r') as f:
            json_str = f.read()
            config = parse_json_into_pyobject(json_str)
    except:
        print("Failed to load config file.")
    return config

class Trip:
    def __init__(self) -> None:
        self.start_time = None
        self.end_time = None
        self.cycle_count = 0

    def start_trip(self):
        self.start_time = time.time()
        self.cycle_count = 0

    def increment_cycle_count(self, count: int = 1):
        if self.start_time is None:
            self.start_trip()
        self.cycle_count += count
    
    def end_trip(self):
        self.end_time = time.time()

    def log_trip(self):
        if self.start_time is None or self.cycle_count == 0:
            print("No trip data to log.")
            return
        # Write the trip data to a file
        # start time, end time, cycle count
        with open('trip_log.csv', 'a') as f:
            start_time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.start_time))
            end_time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.end_time))
            f.write(f"{start_time_str},{end_time_str},{self.cycle_count}\n")
            print(f"Logged trip: {end_time_str}, {self.cycle_count}")


class VirtualBike:
    def __init__(self) -> None:
        self.config_path = 'config.json'
        self.config = load_config(self.config_path)
        self.trip = Trip()
        self.running = True

        self.last_packet_received_time = 0.0
        self.last_processed_time = time.time()
        self.last_cycle_count_rcvd = 0
        self.last_cycle_count_processed = 0

    def udp_listener(self):
        # Create a UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Allow the address to be reused
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind to all interfaces on port 5050
        sock.bind((self.config.listen_ip, self.config.listen_port))
        
        print(f"Listening for UDP broadcasts on post {self.config.listen_port}...")
        
        while True:
            # Receive data and the address it came from
            data, addr = sock.recvfrom(1024)  # Buffer size is 1024 bytes
            #print(f"Received message: {data.decode()} from {addr}")
            data = data.decode()
            packet_type = data[:4]
            if packet_type != 'VBC:' and packet_type != 'VBR:':
                # Unrecognized packet type, skip it
                continue
            data = data[4:]
            #print(f"Received message: {data.decode()} from {addr}")
            packet_idx, cycles = data.split(',')
            packet_idx = int(packet_idx)
            cycles = int(cycles)
            curr_time = time.time()
            time_since_last_received = curr_time - self.last_packet_received_time
            #print("Time since last received: ", time_since_last_received)
            if time_since_last_received > self.config.packet_reset_time or packet_type == 'VBR:':
                # This was a reset packet
                #print("Resetting packet index")
                self.last_cycle_count_processed = cycles - 1
                self.last_message_idx = packet_idx
                self.last_cycle_count_rcvd = cycles
                self.last_packet_received_time = curr_time
            if packet_idx >= self.last_message_idx:
                print("Tick")
                self.last_packet_received_time = curr_time
                self.last_message_idx = packet_idx
                self.last_cycle_count_rcvd = cycles

    def start_udp_listener(self):
        # Create and start the UDP listening thread
        self.udp_thread = threading.Thread(target=self.udp_listener)
        self.udp_thread.daemon = True  # This ensures the thread will exit when the main program does
        self.udp_thread.start()

    def run_game(self):
        self.start_udp_listener()
        self.running = True
        while self.running:
            self.tick_game()
        
        # End the trip and log it
        print("Trip logging closing...")
        self.trip.end_trip()
        self.trip.log_trip()

    def tick_game(self):
        # Process any cycles that have been received
        cycles_to_process = self.last_cycle_count_rcvd - self.last_cycle_count_processed
        if cycles_to_process > 0:
            self.last_processed_time = time.time()
            self.trip.increment_cycle_count(cycles_to_process)
            self.last_cycle_count_processed = self.last_cycle_count_rcvd

        # Check if the trip hasn't been logged in a while
        if self.trip.start_time is not None:
            time_since_last_log = time.time() - self.last_processed_time
            if time_since_last_log > self.config.trip_quiet_time:
                print("Trip has been quiet for a while, logging...")
                self.trip.log_trip()
                self.trip = Trip()

        # Wait 1 second before the next tick
        time.sleep(1)

def signal_handler(sig, frame):
    vbike.running = False

signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    vbike = VirtualBike()
    vbike.run_game()
