from config import *
from vk_clip import *
from tiktok import *
import asyncio
from vkbottle.bot import Bot, Message, BotLabeler
from vkbottle import API, Text, LoopWrapper
from vkbottle.http import SingleAiohttpClient
from aiohttp import TCPConnector
import re
from loguru import logger
import config


logger.remove()
#logger.add(sys.stderr, level="ERROR")

labeler = BotLabeler()
processed_messages = set()

async def main(loop_wrapper: LoopWrapper):
	global bot
	bot = Bot(api=API(token=config.group_token, http_client=SingleAiohttpClient(connector=TCPConnector(verify_ssl=False))), loop_wrapper=loop_wrapper, labeler=labeler)
	print("Бот включен")
	await bot.run_polling()

async def run_tiktok_task(message, url, msg_id):
	try:
		result = await save_tiktok(url)
		await message.answer("опубликовал клип!", attachment=result["clip_id"])
	except Exception as e:
		await message.answer(f"Ошибка TikTok: {e}")
	finally:
		processed_messages.add(msg_id)

async def run_vk_task(message, videos, video_url, description_flag, msg_id):
	try:
		vk_clip = await save_vk_klip(videos, video_url, description_flag)
		await message.answer(
			text="опубликовал клип!",
			attachment=vk_clip["clip_id"]
		)
	except Exception as e:
		await message.answer(f"Ошибка VK клипа: {e}")
	finally:
		processed_messages.add(msg_id)

@labeler.chat_message()
async def chat(message: Message):
	tiktok_pattern = r"(https?://(?:www\.)?tiktok\.com/@[^/]+/video/\d+)"
	msg_id = message.conversation_message_id

	if msg_id in processed_messages:
		return

	text = message.text or ""
	match = re.search(tiktok_pattern, text)

	if match:
		clean_url = match.group(1)
		processed_messages.add(msg_id)
		asyncio.create_task(run_tiktok_task(message, clean_url, msg_id))
		return

	if message.attachments:
		for att in message.attachments:
			if att.type == "video" and att.video:
				video = att.video

				videos = f"{video.owner_id}_{video.id}"
				video_url = f"https://vk.com/video_ext.php?oid={video.owner_id}&id={video.id}"

				description_flag = "!описание" in text.lower()

				processed_messages.add(msg_id)

				asyncio.create_task(run_vk_task(message, videos, video_url, description_flag, msg_id))
				return

	print("не тикток и не клип")