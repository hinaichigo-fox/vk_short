import json
from playwright.sync_api import sync_playwright

PROFILE_PATH = r"/путь/к/профилю/браузера" #можеет не заполнять и так работает

with sync_playwright() as p:
	context = p.chromium.launch_persistent_context(
		user_data_dir=PROFILE_PATH,
		headless=False
	)

	page = context.new_page()
	page.goto("https://vk.com/", wait_until="domcontentloaded")
	input("Если VK открыт и аккаунт авторизован, нажми Enter...")

	cookies = context.cookies()
	with open("cookies.json", "w", encoding="utf-8") as f:
		json.dump(cookies, f, ensure_ascii=False, indent=2)

	context.close()
	print("Сохранено в cookies.json")