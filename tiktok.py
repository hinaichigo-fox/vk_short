import asyncio
import random
import os

import yt_dlp

from config import *
from clip_upload import publish_vk_clip
from unik import process_video_ffmpeg


async def save_tiktok(videos):
	proxy_candidates = [proxy] if proxy else [None]

	save_path = GLOBAL_PATH / "tiktok"
	save_path.mkdir(parents=True, exist_ok=True)

	ydl_opts = {
		"outtmpl": str(save_path / "%(id)s.%(ext)s"),
		"format": "best",
		"merge_output_format": "mp4",
		"proxy": random.choice(proxy_candidates),
		"nocheckcertificate": True,
		"ffmpeg_location": r"C:\ffmpeg\bin",
		"quiet": True,
	}

	def download_video():
		with yt_dlp.YoutubeDL(ydl_opts) as ydl:
			info = ydl.extract_info(videos, download=True)
			return ydl.prepare_filename(info)

	file_path = await asyncio.to_thread(download_video)
	new_video = await process_video_ffmpeg(file_path)

	try:
		tiktok = await publish_vk_clip(
			cookies_path="cookies.json",
			group_id=group_id,
			video_path=new_video,
			description=CONFIG_DESCRIPTION,
			wallpost=1
		)
		return tiktok
	finally:
		if os.path.exists(new_video):
			await asyncio.to_thread(os.remove, new_video)