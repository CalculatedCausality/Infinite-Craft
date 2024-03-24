import requests
import concurrent.futures
from components.config import Config
import time

class ItemTester:

	@classmethod
	def itemTester(cls, item1, item2):
		with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
			future = executor.submit(cls.testItem, item1, item2)
			return future.result()

	@staticmethod
	def testItem(item1, item2):
		params = {
			'first': item1,
			'second': item2,
		}

		with requests.Session() as session:
			while True:
				try:
					response = session.get('https://neal.fun/api/infinite-craft/pair', params=params, cookies=Config.cookies, headers=Config.headers, timeout=5)
					response.raise_for_status()
					data = response.json()
					break
				except Exception as e:

					if response.status_code == 500:
						time.sleep(10)
					print(e)

		return {
			'result': data['result'],
			'emoji': data['emoji'],
			'isNew': data['isNew']
		}