import concurrent.futures
import itertools
import json
import os
import sqlite3
from threading import Lock

import requests


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

	def initConnectionPool():
		Database.connection_pool = sqlite3.connect('infinite_craft.db', check_same_thread=False)
		c = Database.connection_pool.cursor()
		c.execute('''CREATE TABLE IF NOT EXISTS items
					 (item TEXT PRIMARY KEY, emoji TEXT)''')
		c.execute('''CREATE TABLE IF NOT EXISTS combinations
					 (item1 TEXT, item2 TEXT, result TEXT, isNew INTEGER,
					 PRIMARY KEY (item1, item2),
					 FOREIGN KEY (result) REFERENCES items (item))''')
		Database.connection_pool.commit()

	def getDbConnections():
		return Database.connection_pool

	def process_item(item1, item2):
		with Database.db_lock:
			conn = Database.getDbConnections()
			if conn is None:
				Database.initConnectionPool()
				conn = Database.getDbConnections()
			if conn is None:
				return None
			c = conn.cursor()
			c.execute("SELECT result FROM combinations WHERE item1 = ? AND item2 = ?", (item1, item2))
			if c.fetchone() is None:
				print(f"Trying combination: {item1} + {item2}")
				result = ItemTester.itemTester(item1, item2)
				c.execute("INSERT OR IGNORE INTO items VALUES (?, ?)", (result['result'], result['emoji']))
				c.execute("INSERT INTO combinations VALUES (?, ?, ?, ?)", (item1, item2, result['result'], result['isNew']))
				conn.commit()
				if result['isNew']:
					print(f"New item discovered: {result['result']} ({result['emoji']}) from {item1} + {item2}")
				return result['result'] if result['isNew'] else None
		return None

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

		response = requests.get('https://neal.fun/api/infinite-craft/pair', params=params, cookies=Config.cookies, headers=Config.headers)
		response = json.loads(response.text)

		return {
			'result': response['result'],
			'emoji': response['emoji'],
			'isNew': response['isNew']
		}

class BruteForce:
	@staticmethod
	def process_combinations(combinations):
		results = []
		for item1, item2 in combinations:
			result = Database.process_item(item1, item2)
			if result:
				results.append(result)
		return results

	@staticmethod
	def brute_force(discovered_items):
		new_items = set()
		with concurrent.futures.ProcessPoolExecutor() as executor:
			chunk_size = 1000
			discovered_items_list = list(discovered_items)  # Convert set to list
			for i in range(0, len(discovered_items_list), chunk_size):
				combinations = itertools.combinations(discovered_items_list[i:i+chunk_size], 2)
				results = executor.map(BruteForce.process_combinations, [combinations])
				for result in results:
					new_items.update(result)

		return new_items

def main():
	Database.initConnectionPool()

	initial_items = ['cloud', 'earth', 'fire', 'lake', 'ocean', 'sea', 'steam', 'water', 'wind']

	with Database.db_lock:
		conn = Database.getDbConnections()
		c = conn.cursor()
		for item in initial_items:
			c.execute("INSERT OR IGNORE INTO items VALUES (?, '')", (item,))
		conn.commit()

	print('Beginning')

	while True:
		with Database.db_lock:
			conn = Database.getDbConnections()
			c = conn.cursor()
			c.execute("SELECT item FROM items WHERE item NOT IN (?, ?)", ('?', '???'))
			discovered_items = set(item[0] for item in c.fetchall())

		new_items = BruteForce.brute_force(discovered_items)
		if not new_items:
			print("No new items discovered. Brute force complete.")
			break
		else:
			print(f"Discovered {len(new_items)} new items. Continuing brute force...")

if __name__ == "__main__":
	main()