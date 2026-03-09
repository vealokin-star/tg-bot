import asyncio
import os
import uuid
import logging

logger = logging.getLogger(__name__)

DOWNLOAD_DIR = "downloads"


class Downloader:
    def __init__(self):
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    async def download(self, url: str, platform: str) -> dict:
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
        """Download TikTok video or photo slideshow."""
        output_template = os.path.join(output_dir, "%(id)s_%(autonumber)s.%(ext)s")

        await self._run_yt_dlp([
            url,
            "-o", output_template,
            "--no-playlist",
            # Best video with original aspect ratio — no remux that breaks dimensions
            "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
            "--merge-output-format", "mp4",
            "--no-part",
        ])

        files = sorted(os.listdir(output_dir))
        video_files = [os.path.join(output_dir, f) for f in files if f.endswith(".mp4")]
        photo_files = [os.path.join(output_dir, f) for f in files if f.endswith((".jpg", ".jpeg", ".png", ".webp"))]

        # TikTok photo slideshow
        if photo_files and not video_files:
            return {"type": "photo", "paths": photo_files}

        # Mixed (some TikTok slideshows have both)
        if photo_files and video_files:
            return {"type": "photos_and_videos", "paths": photo_files + video_files}

        # Regular video
        if video_files:
            return {"type": "video", "path": video_files[0], "paths": video_files}

        raise RuntimeError("No media files downloaded")

    async def _download_instagram(self, url: str, output_dir: str) -> dict:
        """Download Instagram Reels only."""
        if "/reel/" not in url and "/reels/" not in url:
            raise RuntimeError("Only Instagram Reels are supported.")

        output_template = os.path.join(output_dir, "%(id)s.%(ext)s")

        await self._run_yt_dlp([
            url,
            "-o", output_template,
            "--no-playlist",
            "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
            "--merge-output-format", "mp4",
            "--no-part",
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

    def cleanup(self, paths: list):
        if not paths:
            return
        for path in paths:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                    parent = os.path.dirname(path)
                    if os.path.isdir(parent) and not os.listdir(parent):
                        os.rmdir(parent)
                except Exception as e:
                    logger.warning(f"Cleanup error for {path}: {e}")
