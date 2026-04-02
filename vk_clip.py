import requests
import yt_dlp
import os
from pathlib import Path
from config import *
from clip_upload import *
from unik import *

def save_vk_klip(videos, video_url, description_flag=False):
	resp = requests.get(
		"https://api.vk.com/method/video.get",
		params={
			"access_token": user_token,
			"videos": videos,
			"v": "5.199"
		},
		timeout=60
	)

	resp.raise_for_status()
	data = resp.json()

	if "error" in data:
		raise Exception(f"video.get error: {data['error']}")

	if "response" not in data:
		raise Exception(f"video.get bad response: {data}")

	items = data["response"].get("items", [])
	if not items:
		raise Exception(f"video.get: видео не найдено: {videos}")
	
	print(video_url)

	if description_flag:
		description = items[0].get("description") or CONFIG_DESCRIPTION
	else:
		description = CONFIG_DESCRIPTION

	save_path = GLOBAL_PATH / "vk_clip"
	save_path.mkdir(parents=True, exist_ok=True)

	ydl_opts = {
		'outtmpl': str(save_path / '%(id)s.%(ext)s'),
		'format': 'bestvideo+bestaudio/best',
		'merge_output_format': 'mp4',
		'nocheckcertificate': True,
		'quiet': True,
		'ffmpeg_location': r'C:\ffmpeg\bin', #или свой путь до ffmpeg
	}

	with yt_dlp.YoutubeDL(ydl_opts) as ydl:
		info = ydl.extract_info(video_url, download=True)
		file_path = ydl.prepare_filename(info)
		new_video = process_video_ffmpeg(file_path)
		vk_klip = publish_vk_clip(
			cookies_path="cookies.json",
			group_id=group_id,
			video_path=new_video,
			description=description,
			wallpost=1
		)
		os.remove(new_video)
		return vk_klip