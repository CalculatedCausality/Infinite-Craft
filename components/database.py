import sqlite3
from threading import Lock

from components.itemTester import ItemTester


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