import vk_mess
from vkbottle import LoopWrapper
import asyncio

if __name__ == "__main__":
	vk_mess.loop_wrapper = LoopWrapper()
	vk_mess.loop_wrapper.on_startup.append(vk_mess.main(vk_mess.loop_wrapper))
	vk_mess.loop_wrapper.run()