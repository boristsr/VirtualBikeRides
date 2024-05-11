# Copyright (C) 2024 Philip Edwards
import cv2
import pygame
import numpy as np
import time
import sys
import json
import socket
import threading
import tkinter as tk
from tkinter import filedialog

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

class VirtualBike:
    def __init__(self) -> None:
        self.config_path = 'config.json'
        self.config = load_config(self.config_path)

        # Initialize playback speed
        self.target_playback_speed = self.config.min_playback_speed
        self.current_playback_speed = self.config.min_playback_speed

        self.last_message_idx = -1
        self.last_cycle_count_rcvd = 0
        self.last_cycle_count_processed = 0
        self.last_packet_received_time = 0.0

        # Set the display dimensions
        self.screen_width, self.screen_height = 1280, 720
        self.render_width, self.render_height = 1280, 720
        self.is_fullscreen = True

        self.should_draw_fps = False
        self.game_running = True

        # the number of ticks when the last frame was drawn (not the video frame processed)
        self.last_frame_ticks: int = 0

        # The time the last video frame was presented. In seconds
        self.last_frame_present_time: float = 0.0

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)

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
                #print("Tick")
                self.last_packet_received_time = curr_time
                self.last_message_idx = packet_idx
                self.last_cycle_count_rcvd = cycles

    def start_udp_listener(self):
        # Create and start the UDP listening thread
        self.udp_thread = threading.Thread(target=self.udp_listener)
        self.udp_thread.daemon = True  # This ensures the thread will exit when the main program does
        self.udp_thread.start()

    def draw_speed_indicator(self, surf: pygame.Surface):
        # Draw a circle on the right side of the screen
        clamped_speed = max(min(self.current_playback_speed, self.config.max_playback_speed), self.config.min_playback_speed)
        circle_pct = 1.0 - (clamped_speed / self.config.max_playback_speed)
        # Draw a filled circle
        pygame.draw.circle(surf, (0, 255, 0), (self.render_width - 50, self.render_height / 2), 20)
        pygame.draw.circle(surf, (255, 0, 0), (self.render_width - 50, 50 + 620 * circle_pct), 20)

    def draw_fps(self, surf: pygame.Surface):
        if not self.should_draw_fps:
            return
        current_frame_ticks = pygame.time.get_ticks()
        frame_delta = pygame.time.get_ticks() - self.last_frame_ticks
        self.last_frame_ticks = current_frame_ticks
        fps = 1000.0 / frame_delta
        fps_text = f"FPS: {fps:.2f}"
        font = pygame.font.Font(None, 36)
        text = font.render(fps_text, True, (255, 255, 255))
        surf.blit(text, (10, 10))

    def handle_events(self):
        # Check for key presses
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.game_running = False
            elif event.type == pygame.VIDEORESIZE:
                # Handle window resize event
                self.screen_width, self.screen_height = event.size
                self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
                self.output_surface = None

            if event.type == pygame.KEYDOWN:
                #print(event.key)
                if event.key == pygame.K_ESCAPE:
                    self.game_running = False
                elif event.key == pygame.K_q:
                    self.game_running = False
                elif event.key == pygame.K_p:
                    self.should_draw_fps = not self.should_draw_fps
                elif event.key == pygame.K_f:
                    self.toggle_fullscreen()
                elif event.key == pygame.K_KP_PLUS or event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                    self.target_playback_speed += 0.25
                elif event.key == pygame.K_KP_MINUS or event.key == pygame.K_MINUS:
                    self.target_playback_speed -= 0.25
                    if self.target_playback_speed < 0.1:
                        self.target_playback_speed = 0.1

    def tick_game(self):
        curr_framedelay = 1.0 / (self.video_fps * self.current_playback_speed)
        next_frametime = self.last_frame_present_time + curr_framedelay
        curr_time = time.time()
        #print(f"Time: {time.time()}, next_frametime: {next_frametime}")
        if curr_time >= next_frametime:
            # Read a frame from the video
            # TODO: Reuse frame buffer to avoid allocations
            ret, frame = self.video_decoder.read()
            if not ret:
                # If the frame is not read, the video has ended
                self.game_running = False
                return

            # Convert the frame to a Pygame surface
            # make sure to transpose array and swizzle from BGR to RGB
            # copy frame to video_surface so a new surface isn't allocated
            pygame.pixelcopy.array_to_surface(self.video_surface, frame.swapaxes(0, 1)[:, :, ::-1])

            # Update the last frame present time with the target frame time
            self.last_frame_present_time = next_frametime
            # Get the target frame length and add that to the next target frame time
            curr_framedelay = 1.0 / (self.video_fps * self.current_playback_speed)

        self.frame_surface.blit(self.video_surface, (0, 0))
        self.draw_speed_indicator(self.frame_surface)
        # draw the current FPS
        self.draw_fps(self.frame_surface)
        # Scale the framebuffer to fit the window
        if self.output_surface is None:
            self.output_surface = pygame.Surface((self.screen_width, self.screen_height))
        pygame.transform.smoothscale(self.frame_surface, (self.screen_width, self.screen_height), self.output_surface)
        # Display the frame_surface
        self.screen.blit(self.output_surface, (0, 0))

        pygame.display.update()

        current_frame_time = time.time()
        delta_seconds = current_frame_time - self.last_frame_time
        #print(delta_seconds)
        # decay the target speed
        self.target_playback_speed -= self.target_playback_speed * self.config.target_playback_speed_decay * delta_seconds
        self.last_frame_time = current_frame_time
        
        # Process any cycles that have been received
        cycles_to_process = self.last_cycle_count_rcvd - self.last_cycle_count_processed
        for i in range(cycles_to_process):
            #print("Processing cycle")
            self.last_cycle_count_processed += 1
            self.target_playback_speed += 0.25

        # clamp target playback speed to 0.001 and 2.0
        self.target_playback_speed = max(min(self.target_playback_speed, self.config.max_playback_speed), self.config.min_playback_speed)

        # Adjust the current playback speed towards the target playback speed
        playback_speed_delta = self.target_playback_speed - self.current_playback_speed
        self.current_playback_speed += playback_speed_delta * (self.config.current_playback_speed_adjust * delta_seconds)
        if self.current_playback_speed < self.config.min_playback_speed:
            self.current_playback_speed = self.config.min_playback_speed

        self.handle_events()

    def run_game(self):
        self.next_frametime = time.time()
        self.last_frame_time = time.time()
        self.last_frame_present_time = time.time()

        self.start_udp_listener()
        # just to make sure we have a valid last_frame_ticks
        self.last_frame_ticks = pygame.time.get_ticks()-10

        # TODO: Move this to after video load so it can allocate the appropriate size for the surface
        self.video_surface = pygame.surfarray.make_surface(np.zeros((1280, 720, 3), dtype=np.uint8))
        self.frame_surface = pygame.surfarray.make_surface(np.zeros((1280, 720, 3), dtype=np.uint8))
        self.output_surface = pygame.Surface((self.screen_width, self.screen_height))

        root = tk.Tk()
        root.withdraw()  # Hide the root window
        file_path = filedialog.askopenfilename(initialdir=self.config.video_dir, title='Select a video file')

        if file_path != () and file_path != "":
            print(file_path)
        else:
            print("No file selected.")
            sys.exit(0)

        # Create a video capture object
        self.video_decoder = cv2.VideoCapture(file_path)
        self.video_fps = self.video_decoder.get(cv2.CAP_PROP_FPS)
        print(self.video_fps)

        # Initialize Pygame
        pygame.init()
        # Set the window title
        pygame.display.set_caption("Virtual Bike")

        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.FULLSCREEN)

        while self.game_running:
            self.tick_game()

        # Release the video capture object
        self.video_decoder.release()
        # Close the Pygame window
        pygame.quit()


if __name__ == "__main__":
    vbike = VirtualBike()
    vbike.run_game()
