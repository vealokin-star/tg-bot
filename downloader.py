import asyncio
import os
import uuid
import logging
from typing import Optional

logger = logging.getLogger(__name__)

DOWNLOAD_DIR = "downloads"


class Downloader:
    def __init__(self):
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    async def download(self, url: str, platform: str) -> dict:
        """Download media from TikTok or Instagram."""
        session_id = uuid.uuid4().hex
        output_dir = os.path.join(DOWNLOAD_DIR, session_id)
        os.makedirs(output_dir, exist_ok=True)

        if platform == "tiktok":
            return await self._download_tiktok(url, output_dir)
        elif platform == "instagram":
            return await self._download_instagram(url, output_dir)
        else:
            raise ValueError(f"Unknown platform: {platform}")

    async def _run_yt_dlp(self, args: list) -> tuple:
        """Run yt-dlp as subprocess."""
        cmd = ["yt-dlp"] + args
        logger.info(f"Running: {' '.join(cmd)}")

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            error = stderr.decode().strip()
            logger.error(f"yt-dlp error: {error}")
            raise RuntimeError(f"yt-dlp failed: {error[:300]}")

        return stdout.decode(), stderr.decode()

    async def _download_tiktok(self, url: str, output_dir: str) -> dict:
        """Download TikTok video without watermark."""
        output_template = os.path.join(output_dir, "%(id)s.%(ext)s")

        await self._run_yt_dlp([
            url,
            "-o", output_template,
            "--no-playlist",
            "--merge-output-format", "mp4",
            # Use h264 codec for better Telegram compatibility
            "--remux-video", "mp4",
        ])

        files = os.listdir(output_dir)
        video_files = [f for f in files if f.endswith(".mp4")]

        if not video_files:
            raise RuntimeError("No video file downloaded")

        return {
            "type": "video",
            "path": os.path.join(output_dir, video_files[0]),
            "paths": [os.path.join(output_dir, f) for f in video_files]
        }

    async def _download_instagram(self, url: str, output_dir: str) -> dict:
        """Download Instagram post, reel, or story."""
        output_template = os.path.join(output_dir, "%(id)s_%(autonumber)s.%(ext)s")

        await self._run_yt_dlp([
            url,
            "-o", output_template,
            "--no-playlist",
            "--merge-output-format", "mp4",
        ])

        files = sorted(os.listdir(output_dir))
        video_files = [os.path.join(output_dir, f) for f in files if f.endswith((".mp4", ".mov"))]
        photo_files = [os.path.join(output_dir, f) for f in files if f.endswith((".jpg", ".jpeg", ".png", ".webp"))]

        if video_files and not photo_files:
            if len(video_files) == 1:
                return {"type": "video", "path": video_files[0], "paths": video_files}
            else:
                return {"type": "photos_and_videos", "paths": video_files}
        elif photo_files and not video_files:
            return {"type": "photo", "paths": photo_files}
        elif video_files or photo_files:
            return {"type": "photos_and_videos", "paths": video_files + photo_files}
        else:
            raise RuntimeError("No media files downloaded")

    def cleanup(self, paths: list):
        """Delete downloaded temp files."""
        if not paths:
            return
        for path in paths:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                    # Remove parent dir if empty
                    parent = os.path.dirname(path)
                    if os.path.isdir(parent) and not os.listdir(parent):
                        os.rmdir(parent)
                except Exception as e:
                    logger.warning(f"Cleanup error for {path}: {e}")
