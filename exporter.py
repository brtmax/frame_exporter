import cv2
import pygame
import sys
import os
import csv
import argparse
import tkinter as tk
from tkinter import filedialog

def parse_arguments():
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(description='Video Frame Scrubber and Exporter.')
    parser.add_argument('video_path', nargs='?', help='Path to the video file')
    parser.add_argument('--usage', action='store_true', help='Display usage instructions')
    return parser.parse_args()

def print_usage():
    """
    Print usage instructions for the script.
    """
    usage_text = """
    Usage Instructions:
    - Run the script with a video file path as an argument.
    - Use the mouse wheel to scroll through video frames.
    - Press 'f' to mark the first frame.
    - Press 'l' to mark the last frame.
    - Press ',' to move one frame back.
    - Press '.' to move one frame forward.
    - Press 'e' to export the selected frames and timestamps.
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
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Video Frame Scrubber")
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    return cap, screen, frame_count, width, height

def save_frames(start, end, video_path, save_folder):
    """
    Save the selected frames to a folder and record their timestamps.
    """
    cap = cv2.VideoCapture(video_path)
    timestamps = []
    cap.set(cv2.CAP_PROP_POS_FRAMES, start)
    for i in range(start, end + 1):
        success, img = cap.read()
        if success:
            frame_time = round(cap.get(cv2.CAP_PROP_POS_MSEC) / 1000, 1)  # Convert to seconds
            frame_filename = os.path.join(save_folder, f"frame_{i}.jpg")
            cv2.imwrite(frame_filename, img)
            timestamps.append((i, frame_time))
        else:
            break
    cap.release()
    return timestamps

def main():
    args = parse_arguments()

    if args.usage:
        print_usage()
        return

    if not args.video_path:
        print("Error: No video path provided.")
        sys.exit(1)

    video_path = args.video_path
    cap, screen, frame_count, width, height = initialize_video(video_path)

    first_frame = None
    last_frame = None
    current_frame = 0
    running = True

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
                    first_frame = current_frame
                elif event.key == pygame.K_l:
                    last_frame = current_frame
                elif event.key == pygame.K_COMMA:
                    current_frame = max(0, current_frame - 1)
                elif event.key == pygame.K_PERIOD:
                    current_frame = min(frame_count - 1, current_frame + 1)
                elif event.key == pygame.K_e:
                    if first_frame is not None and last_frame is not None:
                        # Use Tkinter to open file dialog
                        root = tk.Tk()
                        root.withdraw()  # Hides the main window
                        folder_selected = filedialog.askdirectory()
                        root.destroy()

                        if folder_selected:
                            save_folder = os.path.join(folder_selected, os.path.splitext(os.path.basename(video_path))[0])
                            os.makedirs(save_folder, exist_ok=True)
                            timestamps = save_frames(first_frame, last_frame, video_path, save_folder)
                            csv_filename = os.path.join(save_folder, "timestamps.csv")
                            with open(csv_filename, "w", newline="") as f:
                                writer = csv.writer(f)
                                writer.writerow(["Frame ID", "Timestamp"])
                                writer.writerows(timestamps)

        if current_frame < frame_count:
            cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
            success, img = cap.read()
            if success:
                # Display frame number and marked frames
                font = cv2.FONT_HERSHEY_SIMPLEX
                cv2.putText(img, f'Frame: {current_frame}', (10, height - 10), font, 1, (255, 255, 255), 2)
                if first_frame is not None:
                    cv2.putText(img, f'First Frame: {first_frame}', (10, 30), font, 1, (255, 255, 255), 2)
                if last_frame is not None:
                    cv2.putText(img, f'Last Frame: {last_frame}', (10, 60), font, 1, (255, 255, 255), 2)
                frame = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                frame = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
                screen.blit(frame, (0, 0))
                pygame.display.flip()

    pygame.quit()
    cap.release()

if __name__ == "__main__":
    main()
