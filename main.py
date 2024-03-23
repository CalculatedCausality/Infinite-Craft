import json
import requests
import sqlite3
import itertools
import random
import concurrent.futures
from threading import Lock
import os

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
	connection_pool = None

	@staticmethod
	def initialize_connection_pool():
		Database.connection_pool = sqlite3.connect('infinite_craft.db', check_same_thread=False)
		c = Database.connection_pool.cursor()
		c.execute('''CREATE TABLE IF NOT EXISTS items
					 (item TEXT PRIMARY KEY, emoji TEXT)''')
		c.execute('''CREATE TABLE IF NOT EXISTS combinations
					 (item1 TEXT, item2 TEXT, result TEXT, isNew INTEGER,
					 PRIMARY KEY (item1, item2),
					 FOREIGN KEY (result) REFERENCES items (item))''')
		Database.connection_pool.commit()

	@staticmethod
	def get_db_connection():
		return Database.connection_pool

	@staticmethod
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
				if result['isNew']:
					print(f"New item discovered: {result['result']} ({result['emoji']}) from {item1} + {item2}")
				return result['result'] if result['isNew'] else None
		return None

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

class BruteForce:
	@staticmethod
	def brute_force():
		with Database.db_lock:
			conn = Database.get_db_connection()
			c = conn.cursor()
			c.execute("SELECT item FROM items WHERE item NOT IN (?, ?)", ('?', '???'))
			discovered_items = set(item[0] for item in c.fetchall())

		new_items = []
		prev_result = None
		same_result_count = 0

		def process_combination(item1, item2):
			nonlocal prev_result, same_result_count, new_items
			if same_result_count >= 20:
				same_result_count = 0
				return
			new_item = Database.process_item(item1, item2)
			if new_item is not None:
				if new_item == prev_result:
					same_result_count += 1
				else:
					same_result_count = 0
				prev_result = new_item
				new_items.append(new_item)

		max_workers = min(32, (os.cpu_count() or 1) + 4)
		with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
			futures = []
			# Sort combinations by total number of characters in items
			combinations = sorted(itertools.combinations(discovered_items, 2), key=lambda x: len(x[0]) + len(x[1]))
			for item1, item2 in combinations:
				futures.append(executor.submit(process_combination, item1, item2))
			concurrent.futures.wait(futures)

		with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
			futures = []
			for new_item in new_items:
				for item in discovered_items:
					futures.append(executor.submit(Database.process_item, new_item, item))
			for future in concurrent.futures.as_completed(futures):
				new_item = future.result()
				if new_item is not None:
					print(f"New item discovered: {new_item} from combination")

		return len(new_items)

def main():
	Database.initialize_connection_pool()

	initial_items = ['cloud', 'earth', 'fire', 'lake', 'ocean', 'sea', 'steam', 'water', 'wind']

	with Database.db_lock:
		conn = Database.get_db_connection()
		c = conn.cursor()
		for item in initial_items:
			c.execute("INSERT OR IGNORE INTO items VALUES (?, '')", (item,))
		conn.commit()

	print('Beginning')

	while True:
		new_count = BruteForce.brute_force()
		if new_count == 0:
			print("No new items discovered. Brute force complete.")
			break
		else:
			print(f"Discovered {new_count} new items. Continuing brute force...")

if __name__ == "__main__":
	main()