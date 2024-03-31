import cv2
import pygame
import sys
import os
import csv
import argparse
import tkinter as tk
from tkinter import filedialog
import glob

def parse_arguments():
    parser = argparse.ArgumentParser(description='Video Frame Exporter.')
    parser.add_argument('input_path', nargs='?', help='Path to the video file or folder containing videos')
    parser.add_argument('--usage', action='store_true', help='Display usage instructions')

    args = parser.parse_args()
    return args

def print_usage():
    print("""
    Usage Instructions:
    - Run the script with a video file path or a folder path as an argument.
    - Use the mouse wheel to scroll through video frames.
    - Press 'f' to mark the first frame. Press again to unmark.
    - Press 'l' to mark the last frame. Press again to unmark.
    - Press ',' to move one frame back.
    - Press '.' to move one frame forward.
    - Press 'e' to export the selected frames and timestamps.
    - Press 'a' to toggle if an accident occurred in the video.
    - Press 'F11' to toggle full-screen mode.
    - Press 'n' to skip to the next video.
    - Press 'SPACE' to pause and unpause the video.
    """)

def initialize_video(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        sys.exit("Failed to load video: {video_path}")
    success, img = cap.read()
    height, width, _ = img.shape
    screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
    pygame.display.set_caption("Video Frame Scrubber")
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    return cap, screen, frame_count, width, height

def save_frames(first_frame, last_frame, video_path, save_folder, accident_occurred):
    cap = cv2.VideoCapture(video_path)
    timestamps = []
    for frame_number in [first_frame, last_frame]:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        success, img = cap.read()
        if success:
            frame_time_ms = cap.get(cv2.CAP_PROP_POS_MSEC)
            frame_filename = os.path.join(save_folder, f"frame_{frame_number}.jpg")
            cv2.imwrite(frame_filename, img)
            accident_status = "Accident" if accident_occurred else "No Accident"
            timestamps.append((frame_number, frame_time_ms, accident_status))
    cap.release()
    return timestamps

def display_frame_info(img, current_frame, first_frame, last_frame, accident_occurred, height, width, screen):
    font = cv2.FONT_HERSHEY_SIMPLEX
    window_size = screen.get_size()
    resized_img = cv2.resize(img, window_size, interpolation=cv2.INTER_AREA)
    cv2.putText(resized_img, f'Frame: {current_frame}', (10, 30), font, 1, (255, 255, 255), 2)
    if first_frame is not None:
        cv2.putText(resized_img, f'First Frame: {first_frame}', (10, 60), font, 1, (255, 255, 255), 2)
    if last_frame is not None:
        cv2.putText(resized_img, f'Last Frame: {last_frame}', (10, 90), font, 1, (255, 255, 255), 2)
    if accident_occurred:
        cv2.putText(resized_img, 'Accident Occurred', (10, 120), font, 1, (0, 0, 255), 2)
    frame = cv2.cvtColor(resized_img, cv2.COLOR_BGR2RGB)
    frame = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
    screen.blit(frame, (0, 0))

def select_output_folder():
    root = tk.Tk()
    root.withdraw()
    output_folder = filedialog.askdirectory(title="Select Output Folder")
    root.destroy()
    return output_folder

def write_csv(event, csv_filename):
    with open(csv_filename, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(event)

def process_video(video_path, base_output_folder, video_info_list):
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    output_folder = os.path.join(base_output_folder, video_name)
    os.makedirs(output_folder, exist_ok=True)

    cap, screen, frame_count, width, height = initialize_video(video_path)
    first_frame, last_frame, accident_occurred = None, None, False
    current_frame, running, fullscreen, paused = 0, True, False, False
    events = []  # List to store video events

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    current_frame = max(0, current_frame - 1)
                elif event.button == 5:
                    current_frame = min(frame_count - 1, current_frame + 1)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_f:
                    first_frame = None if first_frame == current_frame else current_frame
                    last_frame = None if first_frame is None else last_frame
                elif event.key == pygame.K_l:
                    last_frame = None if last_frame == current_frame else current_frame
                elif event.key in (pygame.K_COMMA, pygame.K_PERIOD):
                    current_frame = max(0, min(frame_count - 1, current_frame - 1 if event.key == pygame.K_COMMA else current_frame + 1))
                elif event.key == pygame.K_e:
                    if first_frame is not None and last_frame is not None:
                        timestamps = save_frames(first_frame, last_frame, video_path, output_folder, accident_occurred)
                        first_frame_ms, last_frame_ms = round(timestamps[0][1], 3), round(timestamps[1][1], 3)
                        time_difference_ms = round(last_frame_ms - first_frame_ms, 3)
                        event_data = (first_frame, first_frame_ms, last_frame, last_frame_ms, time_difference_ms, accident_occurred)

                        csv_filename = os.path.join(output_folder, f"{video_name}_output.csv")
                        with open(csv_filename, "w", newline="") as f:
                            writer = csv.writer(f)
                            writer.writerow(['First ID', 'Timestamp', 'Last ID', 'Timestamp', 'Time Difference', 'Accident'])
                        write_csv(event_data, csv_filename)
                        first_frame, last_frame = None, None
                        accident_occurred = False
                        cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
                        success, img = cap.read()
                        if success:
                            display_frame_info(img, current_frame, first_frame, last_frame, accident_occurred, height, width, screen)
                            pygame.display.flip()
                elif event.key == pygame.K_a:
                    accident_occurred = not accident_occurred
                elif event.key == pygame.K_F11:
                    fullscreen = not fullscreen
                    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN) if fullscreen else pygame.display.set_mode((width, height), pygame.RESIZABLE)
                elif event.key == pygame.K_n:
                    first_frame, last_frame, events, running = None, None, [], False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                    pygame.time.set_timer(pygame.USEREVENT, 100) if paused else pygame.time.set_timer(pygame.USEREVENT, 0)

        if current_frame < frame_count:
            cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
            success, img = cap.read()
            if success:
                display_frame_info(img, current_frame, first_frame, last_frame, accident_occurred, height, width, screen)
                pygame.display.flip()
            current_frame = min(frame_count - 1, current_frame + 1) if not paused else current_frame

    pygame.quit()
    cap.release()

def main():
    print_usage()
    args = parse_arguments()
    if os.path.isdir(args.input_path):
        video_info_list = []
        video_files = glob.glob(os.path.join(args.input_path, "*.mp4"))
        for video_file in video_files:
            process_video(video_file, args.input_path, video_info_list)
    elif os.path.isfile(args.input_path):
        video_info_list = []
        process_video(args.input_path, os.path.dirname(args.input_path), video_info_list)
    else:
        sys.exit("Invalid input path. Please provide a valid video file or folder.")

if __name__ == "__main__":
    main()
