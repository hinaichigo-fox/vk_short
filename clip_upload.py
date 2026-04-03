import os
import re
import json
import uuid
import asyncio
import aiohttp

from urllib.parse import urlparse, parse_qs
from playwright.async_api import async_playwright


API_URL = "https://api.vk.com/method"
API_VERSION = "5.275"
CLIENT_ID = "6287487"


class VKClipsError(Exception):
	pass


def extract_token_from_text(text: str) -> str | None:
	match = re.search(r"(vk1\.a\.[A-Za-z0-9_\-\.]+)", text)
	return match.group(1) if match else None


async def get_web_token_from_cookies(cookies_path: str, wait_seconds: int = 15) -> str:
	with open(cookies_path, "r", encoding="utf-8") as f:
		cookies = json.load(f)

	found_token = None

	async with async_playwright() as p:
		browser = await p.chromium.launch(headless=True)
		context = await browser.new_context()
		await context.add_cookies(cookies)

		page = await context.new_page()

		async def on_request(request):
			nonlocal found_token

			if found_token:
				return

			url = request.url
			if "api.vk.com/method/" not in url:
				return

			post_data = request.post_data or ""
			token = extract_token_from_text(post_data)
			if token:
				found_token = token

		page.on("request", on_request)

		await page.goto("https://vk.com/", wait_until="domcontentloaded")
		await asyncio.sleep(2)

		if not found_token:
			html = await page.content()
			found_token = extract_token_from_text(html)

		if not found_token:
			await page.goto("https://vk.com/clips", wait_until="domcontentloaded")

		start = asyncio.get_running_loop().time()
		while not found_token and asyncio.get_running_loop().time() - start < wait_seconds:
			await asyncio.sleep(1)

		await browser.close()

	if not found_token:
		raise VKClipsError(
			"Не удалось вытащить web access_token из сессии. "
			"Проверь cookies.json или попробуй открыть VK-клипы вручную в браузере и снять свежие cookies."
		)

	return found_token


async def vk_method(
	session: aiohttp.ClientSession,
	method: str,
	params: dict,
	timeout: int = 60
) -> dict:
	async with session.post(
		f"{API_URL}/{method}",
		params={
			"v": API_VERSION,
			"client_id": CLIENT_ID,
		},
		data=params,
		headers={
			"Origin": "https://vk.com",
			"Referer": "https://vk.com/",
			"Content-Type": "application/x-www-form-urlencoded",
			"User-Agent": (
				"Mozilla/5.0 (X11; Linux x86_64) "
				"AppleWebKit/537.36 (KHTML, like Gecko) "
				"Chrome/140.0.0.0 Safari/537.36"
			),
		},
		timeout=aiohttp.ClientTimeout(total=timeout),
	) as resp:
		resp.raise_for_status()
		data = await resp.json()

	if "error" in data:
		raise VKClipsError(f"{method} error: {data['error']}")

	return data["response"]


async def upload_file_in_chunks(
	session: aiohttp.ClientSession,
	upload_url: str,
	file_path: str,
	chunk_size: int = 4 * 1024 * 1024
) -> None:
	file_size = os.path.getsize(file_path)
	filename = os.path.basename(file_path)
	session_id = uuid.uuid4().hex[:16]

	with open(file_path, "rb") as f:
		start = 0

		while start < file_size:
			f.seek(start)
			chunk = f.read(chunk_size)
			end = start + len(chunk) - 1

			headers = {
				"Accept": "*/*",
				"Origin": "https://vk.com",
				"Referer": "https://vk.com/",
				"User-Agent": (
					"Mozilla/5.0 (X11; Linux x86_64) "
					"AppleWebKit/537.36 (KHTML, like Gecko) "
					"Chrome/140.0.0.0 Safari/537.36"
				),
				"Content-Type": "video/mp4",
				"Content-Range": f"bytes {start}-{end}/{file_size}",
				"Content-Disposition": f'attachment; filename="{filename}"',
				"Session-ID": session_id,
				"X-Uploading-Mode": "parallel",
			}

			async with session.post(
				upload_url,
				data=chunk,
				headers=headers,
				timeout=aiohttp.ClientTimeout(total=300),
			) as resp:
				text = await resp.text()
				print("STATUS:", resp.status)
				print("TEXT:", text[:500])
				resp.raise_for_status()

			start += len(chunk)


async def wait_until_ready(
	session: aiohttp.ClientSession,
	access_token: str,
	owner_id: int,
	video_id: int,
	video_hash: str,
	timeout: int = 600
) -> dict:
	start = asyncio.get_running_loop().time()
	last_resp = None

	while True:
		if asyncio.get_running_loop().time() - start > timeout:
			raise VKClipsError("Клип слишком долго кодируется")

		last_resp = await vk_method(
			session,
			"shortVideo.encodeProgress",
			{
				"video_id": video_id,
				"owner_id": owner_id,
				"hash": video_hash,
				"access_token": access_token,
			},
		)

		percents = last_resp.get("percents", 0)
		is_ready = last_resp.get("is_ready", False)
		print(f"encoding: {percents}% | ready={is_ready}")

		if is_ready:
			return last_resp

		await asyncio.sleep(3)


async def publish_vk_clip(
	cookies_path: str,
	group_id: int,
	video_path: str,
	description: str = "",
	wallpost: int = 1,
	can_make_duet: int = 1,
	privacy_view: str = "all",
	privacy_comment: str = "all",
):
	access_token = await get_web_token_from_cookies(cookies_path)
	print("web token captured")

	file_size = os.path.getsize(video_path)

	async with aiohttp.ClientSession() as session:
		create_resp = await vk_method(
			session,
			"shortVideo.create",
			{
				"group_id": group_id,
				"file_size": file_size,
				"access_token": access_token,
			},
		)

		owner_id = create_resp["owner_id"]
		video_id = create_resp["video_id"]
		upload_url = create_resp["upload_url"]

		print("create ok")
		print("owner_id =", owner_id)
		print("video_id =", video_id)

		parsed = urlparse(upload_url)
		query = parse_qs(parsed.query)
		video_hash = query.get("vkVideoHash", [None])[0]

		if not video_hash:
			raise VKClipsError("Не найден vkVideoHash в upload_url")

		await upload_file_in_chunks(session, upload_url, video_path)

		progress_resp = await wait_until_ready(
			session=session,
			access_token=access_token,
			owner_id=owner_id,
			video_id=video_id,
			video_hash=video_hash,
		)

		all_thumbs = progress_resp.get("all_thumbs", [])
		thumb_id = all_thumbs[0]["thumb_full_id"] if all_thumbs else None

		edit_params = {
			"video_id": video_id,
			"owner_id": owner_id,
			"description": description,
			"privacy_view": privacy_view,
			"can_make_duet": can_make_duet,
			"privacy_comment": privacy_comment,
			"audio_raw_id": "",
			"ord_info": json.dumps({"is_ads": False, "advertisers": []}, ensure_ascii=False),
			"access_token": access_token,
		}

		if thumb_id:
			edit_params["thumb_id"] = thumb_id

		edit_resp = await vk_method(session, "shortVideo.edit", edit_params)
		print("edit ok")

		publish_resp = await vk_method(
			session,
			"shortVideo.publish",
			{
				"video_id": video_id,
				"owner_id": owner_id,
				"wallpost": wallpost,
				"publish_date": 0,
				"license_agree": 1,
				"ref": "club_clips_button",
				"access_token": access_token,
			},
		)

	clip_id = f'clip{publish_resp["video"]["owner_id"]}_{publish_resp["video"]["id"]}'
	print("publish ok")

	return {
		"create": create_resp,
		"edit": edit_resp,
		"clip_id": clip_id,
		"publish": publish_resp,
	}