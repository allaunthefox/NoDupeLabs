import os
import subprocess
from pathlib import Path
from nodupe.utils.ffmpeg_progress import run_ffmpeg_with_progress

SOURCE_DIR = Path("nsfw_test_set")
DEST_DIR = Path("nsfw_test_set/converted")

def convert_video(input_path, output_path):
    if output_path.exists():
        print(f"Skipping {output_path}, already exists.")
        return

    print(f"Converting {input_path} -> {output_path}")
    # Basic ffmpeg conversion. 
    # -y to overwrite
    # -strict -2 might be needed for some codecs in older ffmpeg, but usually fine now.
    # Choose codec/format based on output extension to maximize compatibility
    ext = output_path.suffix.lower()
    if ext == '.mp4':
        # H.264 baseline profile for wide compatibility; yuv420p pixel format
        cmd = [
            'ffmpeg', '-y', '-v', 'error', '-i', str(input_path),
            '-c:v', 'libx264', '-preset', 'medium', '-crf', '23', '-pix_fmt', 'yuv420p',
            '-c:a', 'aac', '-b:a', '128k', str(output_path)
        ]
    elif ext == '.webm':
        # VP9/Opus for webm
        cmd = [
            'ffmpeg', '-y', '-v', 'error', '-i', str(input_path),
            '-c:v', 'libvpx-vp9', '-b:v', '1M', '-crf', '30', '-c:a', 'libopus', '-b:a', '64k',
            str(output_path)
        ]
    elif ext == '.mkv':
        # Matroska container with H.264 video
        cmd = [
            'ffmpeg', '-y', '-v', 'error', '-i', str(input_path),
            '-c:v', 'libx264', '-preset', 'medium', '-crf', '23', '-c:a', 'aac', '-b:a', '128k',
            str(output_path)
        ]
    elif ext == '.avi':
        # Legacy avi with mpeg4 codec
        cmd = [
            'ffmpeg', '-y', '-v', 'error', '-i', str(input_path),
            '-c:v', 'mpeg4', '-qscale:v', '3', '-c:a', 'mp3', '-b:a', '128k', str(output_path)
        ]
    else:
        # default fallback - let ffmpeg choose
        cmd = ['ffmpeg', '-y', '-v', 'error', '-i', str(input_path), str(output_path)]
    
    ok = run_ffmpeg_with_progress(cmd, expected_duration=None)
    if not ok:
        print(f"Error converting {input_path}: ffmpeg failed or not present")

def main():
    if not DEST_DIR.exists():
        DEST_DIR.mkdir(parents=True)

    # Find all video files
    video_extensions = {".mp4", ".webm", ".gif", ".mkv", ".mov", ".avi"}
    
    for root, dirs, files in os.walk(SOURCE_DIR):
        # Skip the converted directory itself to avoid loops if we run multiple times
        if "converted" in root:
            continue

        for file in files:
            file_path = Path(root) / file
            if file_path.suffix.lower() in video_extensions:
                print(f"Found video: {file_path}")
                
                # Define conversions
                conversions = []
                
                # If it's a gif, convert to mp4 and webm
                if file_path.suffix.lower() == ".gif":
                    conversions.append(DEST_DIR / f"{file_path.stem}_converted.mp4")
                    conversions.append(DEST_DIR / f"{file_path.stem}_converted.webm")
                
                # If it's a video, convert to a few common containers
                else:
                    # To MP4 (if not already)
                    if file_path.suffix.lower() != ".mp4":
                        conversions.append(DEST_DIR / f"{file_path.stem}_converted.mp4")
                    
                    # To WebM (if not already)
                    if file_path.suffix.lower() != ".webm":
                        conversions.append(DEST_DIR / f"{file_path.stem}_converted.webm")
                        
                    # To MKV
                    if file_path.suffix.lower() != ".mkv":
                        conversions.append(DEST_DIR / f"{file_path.stem}_converted.mkv")
                    
                    # To AVI (just for variety)
                    if file_path.suffix.lower() != ".avi":
                        conversions.append(DEST_DIR / f"{file_path.stem}_converted.avi")

                for dest in conversions:
                    convert_video(file_path, dest)

if __name__ == "__main__":
    main()
