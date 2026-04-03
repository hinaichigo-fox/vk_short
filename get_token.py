import asyncio
from clip_upload import get_web_token_from_cookies

token = asyncio.run(get_web_token_from_cookies("cookies.json"))
print(token)