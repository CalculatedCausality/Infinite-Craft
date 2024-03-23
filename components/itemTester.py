import concurrent.futures
import json

import requests

from components.config import Config


class ItemTester:
	@staticmethod
	def test_item(items):
		with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
			futures = {executor.submit(ItemTester._test_item, item1, item2): (item1, item2) for item1, item2 in items}
			return {fut.result(): items[fut] for fut in concurrent.futures.as_completed(futures)}

	@staticmethod
	def _test_item(item1, item2):
		params = {
			'first': item1,
			'second': item2,
		}

		response = requests.get('https://neal.fun/api/infinite-craft/pair', params=params, cookies=Config.cookies, headers=Config.headers)
		response = json.loads(response.text)

		return {
			'result': response['result'],
			'emoji': response['emoji'],
			'isNew': response['isNew']
		}