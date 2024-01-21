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
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(description='Video Frame Scrubber and Exporter.')
    parser.add_argument('input_path', nargs='?', help='Path to the video file or folder containing videos')
    return parser.parse_args()

def print_usage():
    """
    Print usage instructions for the script.
    """
    usage_text = """
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
    """
    print(usage_text)

def initialize_video(video_path):
    """
    Initialize the video capture and pygame screen.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Failed to load video: {video_path}")
        sys.exit(1)

    success, img = cap.read()
    height, width, _ = img.shape
    screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
    pygame.display.set_caption("Video Frame Scrubber")
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    return cap, screen, frame_count, width, height

def save_frames(first_frame, last_frame, video_path, save_folder, accident_occurred):
    """
    Save the first and last selected frames to a folder and record their timestamps.
    """
    cap = cv2.VideoCapture(video_path)
    timestamps = []
    for frame_number in [first_frame, last_frame]:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        success, img = cap.read()
        if success:
            frame_time = round(cap.get(cv2.CAP_PROP_POS_MSEC) / 1000, 1)
            frame_filename = os.path.join(save_folder, f"frame_{frame_number}.jpg")
            cv2.imwrite(frame_filename, img)
            accident_status = "Accident" if accident_occurred else "No Accident"
            timestamps.append((frame_number, frame_time, accident_status))
    cap.release()
    return timestamps

def display_frame_info(img, current_frame, first_frame, last_frame, accident_occurred, height, width, screen):
    """
    Display frame information on the screen and resize frame to fit the window.
    """
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
    """
    Prompt the user to select an output folder.
    """
    root = tk.Tk()
    root.withdraw()
    output_folder = filedialog.askdirectory(title="Select Output Folder")
    root.destroy()
    return output_folder

def process_video(video_path, base_output_folder):
    """
    Process a single video file.
    """
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    output_folder = os.path.join(base_output_folder, video_name)
    os.makedirs(output_folder, exist_ok=True)

    cap, screen, frame_count, width, height = initialize_video(video_path)
    first_frame = None
    last_frame = None
    accident_occurred = False
    current_frame = 0
    running = True
    fullscreen = False

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:  # Scroll up
                    current_frame = max(0, current_frame - 1)
                elif event.button == 5:  # Scroll down
                    current_frame = min(frame_count - 1, current_frame + 1)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_f:
                    first_frame = None if first_frame == current_frame else current_frame
                    if first_frame is None:
                        last_frame = None  # Unset last frame if first frame is unset
                elif event.key == pygame.K_l:
                    last_frame = None if last_frame == current_frame else current_frame
                elif event.key == pygame.K_COMMA:
                    current_frame = max(0, current_frame - 1)
                elif event.key == pygame.K_PERIOD:
                    current_frame = min(frame_count - 1, current_frame + 1)
                elif event.key == pygame.K_e:
                    if first_frame is not None and last_frame is not None:
                        timestamps = save_frames(first_frame, last_frame, video_path, output_folder, accident_occurred)
                        csv_filename = os.path.join(output_folder, video_name + "_timestamps.csv")
                        with open(csv_filename, "w", newline="") as f:
                            writer = csv.writer(f)
                            writer.writerow(["Frame ID", "Timestamp", "Accident Status"])
                            writer.writerows(timestamps)
                        pygame.quit()
                        cap.release()
                        return  # Exit the function after saving
                elif event.key == pygame.K_a:
                    accident_occurred = not accident_occurred
                elif event.key == pygame.K_F11:
                    fullscreen = not fullscreen
                    if fullscreen:
                        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                    else:
                        screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)

        if current_frame < frame_count:
            cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
            success, img = cap.read()
            if success:
                display_frame_info(img, current_frame, first_frame, last_frame, accident_occurred, height, width, screen)
                pygame.display.flip()

    pygame.quit()
    cap.release()

def main():
    args = parse_arguments()

    if os.path.isdir(args.input_path):
        output_folder = select_output_folder()
        if not output_folder:
            print("No output folder selected. Exiting.")
            sys.exit(1)

        video_files = glob.glob(os.path.join(args.input_path, "*.mp4"))  # Add other formats if needed
        for video_file in video_files:
            process_video(video_file, output_folder)

    elif os.path.isfile(args.input_path):
        process_video(args.input_path, os.path.dirname(args.input_path))

    else:
        print("Invalid input path. Please provide a valid video file or folder.")
        sys.exit(1)

if __name__ == "__main__":
    main()

