import random
import os
import yt_dlp
from config import *
from clip_upload import *
from unik import *

def save_tiktok(videos):
	proxies = [proxy]
	save_path = GLOBAL_PATH / "tiktok"
	save_path.mkdir(parents=True, exist_ok=True)
	ydl_opts = {
		'outtmpl': str(save_path /'%(id)s.%(ext)s'),
		'format': 'best',
		'merge_output_format': 'mp4',
		'proxy': random.choice(proxies),  # случайный прокси
		'nocheckcertificate': True,
		'ffmpeg_location': r'C:\ffmpeg\bin',
	}

	with yt_dlp.YoutubeDL(ydl_opts) as ydl:
		info = ydl.extract_info(videos, download=True)
		file_path = ydl.prepare_filename(info)
		new_video = process_video_ffmpeg(file_path)
		tiktok = publish_vk_clip(cookies_path="cookies.json", group_id=group_id, video_path=new_video, description=CONFIG_DESCRIPTION, wallpost=1)
		os.remove(new_video)
		return tiktok