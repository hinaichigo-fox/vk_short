import multitasking
from vk_mess import *

@multitasking.task
def recursion(token, group_id):
	while True:
		try:
			Auth(token, group_id)
		except Exception as err:
			print(err)

recursion(group_token, group_id)