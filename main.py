import json
import requests
import sqlite3
import itertools
import random
import concurrent.futures
from threading import Lock

class Config:
	cookies = {
		'__cf_bm': 'PoRiemJlVVskkxO18.7nWj3Q8JppplaSsCb8Jo_ce5o-1711091909-1.0.1.1-722kxsKFziRCQI.wiO4ZTtvkqphgBiKzyqLbax_uFoX2LWOmGJt1_7qkLR6GCZVwOqvxHCEcO2xwGw19R_3pHA',
		'cf_clearance': 'DbUPvKZ1eSDjTbe4Tt3g2zjz76Pvz19VS.nV3orGv1I-1711091910-1.0.1.1-Qmpzb_bgWKHlmpwAMxwZrGjlDfbbvRj5he_xxaI7pDYs0uVIBCYM7I.N.kagPhBmOp64.7mcDUObVpld5q_WrQ',
	}

	headers = {
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
		'Accept': '*/*',
		'Accept-Language': 'en-US,en;q=0.5',
		'Referer': 'https://neal.fun/infinite-craft/',
		'DNT': '1',
		'Alt-Used': 'neal.fun',
		'Connection': 'keep-alive',
		'Sec-Fetch-Dest': 'empty',
		'Sec-Fetch-Mode': 'cors',
		'Sec-Fetch-Site': 'same-origin',
		'Sec-GPC': '1',
	}

class Database:
	db_lock = Lock()

	@staticmethod
	def get_db_connection():
		conn = sqlite3.connect('infinite_craft.db', check_same_thread=False)
		c = conn.cursor()

		c.execute('''CREATE TABLE IF NOT EXISTS items
					 (item TEXT PRIMARY KEY, emoji TEXT)''')

		c.execute('''CREATE TABLE IF NOT EXISTS combinations
					 (item1 TEXT, item2 TEXT, result TEXT, isNew INTEGER,
					 PRIMARY KEY (item1, item2),
					 FOREIGN KEY (result) REFERENCES items (item))''')

		conn.commit()
		return conn

	def process_item(item1, item2):
		with Database.db_lock:
			conn = Database.get_db_connection()
			c = conn.cursor()

			c.execute("SELECT result FROM combinations WHERE item1 = ? AND item2 = ?", (item1, item2))
			if c.fetchone() is None:

				print(f"Trying combination: {item1} + {item2}")
				result = ItemTester.test_item(item1, item2)
				c.execute("INSERT OR IGNORE INTO items VALUES (?, ?)", (result['result'], result['emoji']))
				c.execute("INSERT INTO combinations VALUES (?, ?, ?, ?)", (item1, item2, result['result'], result['isNew']))
				conn.commit()
				conn.close()
				if result['isNew']:
					print(f"New item discovered: {result['result']} ({result['emoji']}) from {item1} + {item2}")
				return result['result'] if result['isNew'] else None
			conn.close()
		return None

class ItemTester:

	def test_item(item1, item2):
		with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
			future = executor.submit(ItemTester._test_item, item1, item2)
			return future.result()

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

class BruteForce:

	def brute_force():
		with Database.db_lock:
			conn = Database.get_db_connection()
			c = conn.cursor()
			c.execute("SELECT item FROM items WHERE item NOT IN (?, ?)", ('?', '???'))
			discoveredItems = [item[0] for item in c.fetchall()]
			conn.close()

		newItems = []
		prev_result = None
		same_result_count = 0

		# Generate all possible combinations of the items
		combinations = list(itertools.combinations(discoveredItems, 2))

		# Shuffle the combinations to try them in a random order
		random.shuffle(combinations)

		with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
			for item1, item2 in combinations:
				if same_result_count >= 20:
					same_result_count = 0
					continue
				future = executor.submit(Database.process_item, item1, item2)
				newItem = future.result()
				if newItem is not None:
					if newItem == prev_result:
						same_result_count += 1
					else:
						same_result_count = 0
					prev_result = newItem
					newItems.append(newItem)

		with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
			futures = [executor.submit(Database.process_item, newItem, item) for newItem in newItems for item in discoveredItems]

			for future in concurrent.futures.as_completed(futures):
				newItem = future.result()
				if newItem is not None:
					print(f"New item discovered: {newItem} from combination")

		return len(newItems)

def main():
	initialItems = ['cloud', 'earth', 'fire', 'lake', 'ocean', 'sea', 'steam', 'water', 'wind']

	with Database.db_lock:
		conn = Database.get_db_connection()
		c = conn.cursor()
		for item in initialItems:
			c.execute("INSERT OR IGNORE INTO items VALUES (?, '')", (item,))
		conn.commit()
		conn.close()

	print('Beginning')

	while True:
		newCount = BruteForce.brute_force()
		if newCount == 0:
			print("No new items discovered. Brute force complete.")
			break
		else:
			print(f"Discovered {newCount} new items. Continuing brute force...")

if __name__ == "__main__":
	main()