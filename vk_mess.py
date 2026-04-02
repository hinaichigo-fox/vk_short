from config import *
import random
import vk_api
import time
import re
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_clip import *
from tiktok import *


def Auth(token, group_id):
	vk = vk_api.VkApi(token=group_token)
	api = vk.get_api()
	longpoll = VkBotLongPoll(vk, group_id=group_id)
	Polling(api, longpoll, group_id, token)

def send(api, id, text, attachment):
	api.messages.send(peer_id=id, message=text, attachment=attachment, random_id=0)

def send2(api, id, text):
	api.messages.send(peer_id=id, message=text, random_id=0)


processed_messages = set()

def Polling(api, longpoll, group_id, token):
	for event in longpoll.listen():
		if event.type != VkBotEventType.MESSAGE_NEW:
			continue
		message = event.obj['message']
		msg_id = message.get('id')
		if msg_id in processed_messages:
			continue
		processed_messages.add(msg_id)
		msg = message.get('text', '').lower()
		id = message["peer_id"]
		try:
			if id > 2000000000:
				if message['attachments'] and message['attachments'][0]['type'] == 'video' and message['attachments'][0]['video'].get('type') == 'short_video':
					#фильтр клипов
					description = False
					if msg == '!описание':
						description = True

					send2(api, id, "клип получен, начинаю обработку!")

					videos = f"{message['attachments'][0]['video']['owner_id']}_{message['attachments'][0]['video']['id']}"
					video_id = message['attachments'][0]['video']['id']
					owner_id = message['attachments'][0]['video']['owner_id']
					video_url = f"https://vk.com/video_ext.php?oid={owner_id}&id={video_id}"
					#получение основных ссылок для скачивания видосов

					try:
						#скачивание клипа и залив
						a = save_vk_klip(videos, video_url, description)
						send(api, id, "опубликовал клип", a["clip_id"])
					except Exception as err:
						print(err)
						send2(api, id, f"Не удалось загрузить клип. Ошибка: {err}")
				tiktok_pattern = r"(https?://(?:www\.)?tiktok\.com/@[^/]+/video/\d+)"
				#патерн тиктока. смс должно быть ток со ссылкой на тикток
				if "tiktok" in msg:
					match = re.search(tiktok_pattern, msg)
					if match:
						send2(api, id, "тикток получен, начинаю обработку!")
						clean_url = match.group(1)
						try:
							#скачивание тиктока
							a = save_tiktok(clean_url)
							send(api, id, "опубликовал клип", a["clip_id"])
						except Exception as err:
							print(err)
							send2(api, id, f"Не удалось загрузить клип. Ошибка: {err}")
				if msg == 'пинг':
					send2(api, id, 'понг')
			else:
				send2(api, id, 'не работаю в лс, только в чате')

		except Exception as err:
			print(err)
			send2(api, id, f"Не удалось обработать сообщение. Ошибка: {err}")
