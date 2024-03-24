import requests
import json
import concurrent.futures
from components.config import Config


class ItemTester:

	def itemTester(item1, item2):
		with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
			future = executor.submit(ItemTester.testItem, item1, item2)
			return future.result()


	def testItem(item1, item2):
		params = {
			'first': item1,
			'second': item2,
		}

		while True:
			try:
				response = requests.get('https://neal.fun/api/infinite-craft/pair', params=params, cookies=Config.cookies, headers=Config.headers)
				response = json.loads(response.text)
				break
			except Exception as e:
				print(e)

		return {
			'result': response['result'],
			'emoji': response['emoji'],
			'isNew': response['isNew']
		}