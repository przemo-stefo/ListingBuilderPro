#!/usr/bin/env python3
# /Users/shawn/Projects/ListingBuilderPro/listing_builder/ytdlp_server.py
# Purpose: FastAPI server to get YouTube video transcripts/subtitles
# NOT for: Production use without proper API keys

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import subprocess
import tempfile
import os
import uuid
import re
import json

app = FastAPI(title="YouTube Transcript Server")

YTDLP_PATH = "/Users/shawn/Library/Python/3.9/bin/yt-dlp"

class TranscriptRequest(BaseModel):
    url: str
    lang: str = "en"

class DownloadRequest(BaseModel):
    url: str
    format: str = "mp3"

def extract_video_id(url: str) -> str:
    """Extract video ID from various YouTube URL formats"""
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

@app.get("/health")
def health():
    return {"status": "ok", "ytdlp": os.path.exists(YTDLP_PATH)}

@app.post("/transcript")
async def get_transcript(request: TranscriptRequest):
    """Get video transcript/subtitles using yt-dlp"""

    if not request.url:
        raise HTTPException(status_code=400, detail="URL is required")

    video_id = extract_video_id(request.url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    temp_dir = tempfile.mkdtemp(prefix="yt_transcript_")

    try:
        # Try to get auto-generated captions
        cmd = [
            YTDLP_PATH,
            "--skip-download",
            "--write-auto-sub",
            "--sub-lang", request.lang,
            "--sub-format", "vtt",
            "-o", os.path.join(temp_dir, "%(id)s.%(ext)s"),
            request.url
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        # Find the subtitle file
        vtt_files = [f for f in os.listdir(temp_dir) if f.endswith('.vtt')]

        if not vtt_files:
            # Try manual subtitles
            cmd[3] = "--write-sub"
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            vtt_files = [f for f in os.listdir(temp_dir) if f.endswith('.vtt')]

        if not vtt_files:
            # No subtitles available - return video info instead
            info_cmd = [
                YTDLP_PATH,
                "--skip-download",
                "--print", "%(title)s",
                "--print", "%(description)s",
                request.url
            ]
            info_result = subprocess.run(info_cmd, capture_output=True, text=True, timeout=30)
            lines = info_result.stdout.strip().split('\n')

            return JSONResponse({
                "success": True,
                "videoId": video_id,
                "transcript": "",
                "title": lines[0] if len(lines) > 0 else "",
                "description": lines[1] if len(lines) > 1 else "",
                "source": "no_subtitles",
                "message": "No subtitles available for this video"
            })

        # Parse VTT file to extract text
        vtt_path = os.path.join(temp_dir, vtt_files[0])
        transcript_text = parse_vtt(vtt_path)

        # Get video title
        info_cmd = [
            YTDLP_PATH,
            "--skip-download",
            "--print", "%(title)s",
            request.url
        ]
        info_result = subprocess.run(info_cmd, capture_output=True, text=True, timeout=30)
        title = info_result.stdout.strip()

        return JSONResponse({
            "success": True,
            "videoId": video_id,
            "transcript": transcript_text,
            "title": title,
            "source": "subtitles",
            "language": request.lang
        })

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Timeout getting transcript")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

def parse_vtt(vtt_path: str) -> str:
    """Parse VTT file and extract clean text"""
    with open(vtt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove WEBVTT header and timing lines
    lines = content.split('\n')
    text_lines = []

    for line in lines:
        line = line.strip()
        # Skip empty lines, WEBVTT header, and timestamp lines
        if not line or line.startswith('WEBVTT') or '-->' in line or line.startswith('Kind:') or line.startswith('Language:'):
            continue
        # Skip position/styling tags
        if re.match(r'^\d+$', line) or line.startswith('align:') or line.startswith('position:'):
            continue
        # Remove HTML-like tags
        line = re.sub(r'<[^>]+>', '', line)
        if line:
            text_lines.append(line)

    # Remove duplicates (auto-generated often has dupes)
    seen = set()
    unique_lines = []
    for line in text_lines:
        if line not in seen:
            seen.add(line)
            unique_lines.append(line)

    return ' '.join(unique_lines)

@app.post("/download")
async def download_audio(request: DownloadRequest):
    """Try to download audio - note: YouTube often blocks this"""

    if not request.url:
        raise HTTPException(status_code=400, detail="URL is required")

    temp_dir = tempfile.mkdtemp(prefix="ytdlp_")
    file_id = str(uuid.uuid4())[:8]
    output_template = os.path.join(temp_dir, f"audio_{file_id}.%(ext)s")

    try:
        cmd = [
            YTDLP_PATH,
            "-x",
            "--audio-format", request.format,
            "--audio-quality", "0",
            # Try different clients
            "--extractor-args", "youtube:player_client=ios",
            "-o", output_template,
            request.url
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode != 0:
            # If download fails, suggest using transcript instead
            raise HTTPException(
                status_code=503,
                detail=f"Audio download blocked by YouTube. Use /transcript endpoint instead. Error: {result.stderr[-500:]}"
            )

        files = os.listdir(temp_dir)
        if not files:
            raise HTTPException(status_code=500, detail="No output file created")

        actual_file = os.path.join(temp_dir, files[0])
        return FileResponse(
            actual_file,
            media_type="audio/mpeg",
            filename=f"audio_{file_id}.mp3"
        )

    except subprocess.TimeoutExpired:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=504, detail="Download timeout")
    except HTTPException:
        raise
    except Exception as e:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765)
