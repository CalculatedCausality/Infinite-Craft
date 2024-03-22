import json
import requests
import sqlite3
import concurrent.futures
from threading import Lock

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

initialItems = ['cloud', 'earth', 'fire', 'lake', 'ocean', 'sea', 'steam', 'water', 'wind']

db_lock = Lock()

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

def testItem(item1, item2):
	params = {
		'first': item1,
		'second': item2,
	}

	response = requests.get('https://neal.fun/api/infinite-craft/pair', params=params, cookies=cookies, headers=headers)
	response = json.loads(response.text)

	return {
		'result': response['result'],
		'emoji': response['emoji'],
		'isNew': response['isNew']
	}

def processItem(item1, item2):
	with db_lock:
		conn = get_db_connection()
		c = conn.cursor()

		c.execute("SELECT result FROM combinations WHERE item1 = ? AND item2 = ?", (item1, item2))
		if c.fetchone() is None:
			result = testItem(item1, item2)
			c.execute("INSERT OR IGNORE INTO items VALUES (?, ?)", (result['result'], result['emoji']))
			c.execute("INSERT INTO combinations VALUES (?, ?, ?, ?)", (item1, item2, result['result'], result['isNew']))
			conn.commit()
			conn.close()
			if result['isNew']:
				print(f"New item discovered: {result['result']} ({result['emoji']}) from {item1} + {item2}")
			return result['result'] if result['isNew'] else None
		conn.close()
	return None

def bruteForce():

	with db_lock:
		conn = get_db_connection()
		c = conn.cursor()
		c.execute("SELECT item FROM items")
		discoveredItems = [item[0] for item in c.fetchall()]
		conn.close()

	newItems = []

	with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
		futures = []
		for item1 in discoveredItems:
			for item2 in discoveredItems:
				futures.append(executor.submit(processItem, item1, item2))

		for future in concurrent.futures.as_completed(futures):
			newItem = future.result()
			if newItem is not None:
				newItems.append(newItem)

	with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
		futures = []
		for newItem in newItems:
			for item in discoveredItems:
				futures.append(executor.submit(processItem, newItem, item))

		for future in concurrent.futures.as_completed(futures):
			newItem = future.result()
			if newItem is not None:
				print(f"New item discovered: {newItem} from combination")

	return len(newItems)

with db_lock:
	conn = get_db_connection()
	c = conn.cursor()
	for item in initialItems:
		c.execute("INSERT OR IGNORE INTO items VALUES (?, '')", (item,))
	conn.commit()
	conn.close()

print('Beginning')

while True:
	newCount = bruteForce()
	if newCount == 0:
		print("No new items discovered. Brute force complete.")
		break
	else:
		print(f"Discovered {newCount} new items. Continuing brute force...")
