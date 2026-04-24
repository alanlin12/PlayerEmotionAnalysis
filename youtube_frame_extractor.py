import subprocess
import json
import cv2
import numpy as np
from PIL import Image
import io
import os
import platform
import argparse

def get_stream_url(youtube_url):
    """Extract direct video stream URL using yt-dlp"""
    cmd = [
        'yt-dlp',
        '-f', 'best[height<=480]',  # Max resolution: 480p
        '-g',  # Get URL only, don't download
        youtube_url
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip()

def get_video_duration(stream_url):
    """Get video duration using ffprobe"""
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1:nokey=1',
        stream_url
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())

def extract_frames(stream_url, num_frames=100):
    """Extract evenly spaced frames from stream"""
    duration = get_video_duration(stream_url)
    timestamps = np.linspace(0, duration, num_frames, endpoint=False)
    
    frames = []
    for ts in timestamps:
        # ffmpeg seeks to timestamp and extracts 1 frame
        cmd = [
            'ffmpeg',
            '-ss', str(ts),  # Seek to timestamp
            '-i', stream_url,
            '-frames:v', '1',  # Extract 1 frame
            '-f', 'image2pipe',  # Pipe output
            '-pix_fmt', 'rgb24',
            '-vf', 'scale=640:480',  # Optional: resize
            'pipe:'
        ]
        
        result = subprocess.run(cmd, capture_output=True)
        img = Image.open(io.BytesIO(result.stdout))
        frames.append(np.array(img))
    
    return frames

parser = argparse.ArgumentParser(
    description='Extract frames from a YouTube video and uploads them to a specified directory.')

parser.add_argument('--url', type=str, help='The URL of the YouTube video to extract frames from.')
parser.add_argument('--dir', type=str, help='The directory to write the frames to.')
args = parser.parse_args()

# Ensures url is a youtube url
if not args.url or ('youtube.com' not in args.url and 'youtu.be' not in args.url):
    print("Please provide a valid YouTube URL using the --url argument.")
    exit(1)

# Extract stream URL and frames
try:
    url = get_stream_url(args.url)
except Exception as e:
    print(f"Error extracting stream URL: {e}")
    exit(1)
frames = extract_frames(url, num_frames=100)

# Get video key for directory naming
if 'youtube.com' in args.url:
    video_key = args.url.split('v=')[-1].split('&')[0]
else:
    video_key = args.url.split('/')[-1].split('?')[0]

# Save frames as images in directory
if args.dir:
    path = os.path.join(args.dir, video_key)
else:
    path = video_key

os.makedirs(path, exist_ok=True)
for i, frame in enumerate(frames):
    cv2.imwrite(os.path.join(path, f'frame_{i:03d}.jpg'), cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))