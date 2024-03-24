from threading import Lock
import sqlite3
from components.itemTester import ItemTester


class Database:
	db_lock = Lock()
	connection_pool = None

	@staticmethod
	def check_item_counts():
		with Database.db_lock:
			conn = Database.getDbConnections()
			c = conn.cursor()
			c.execute("""
				SELECT input_item, MAX(count) as max_count
				FROM combination_counts
				GROUP BY input_item
				HAVING max_count > 10
			""")
			results = c.fetchall()
			return [item[0] for item in results]

	def initConnectionPool():
		Database.connection_pool = sqlite3.connect('infinite_craft.db', check_same_thread=False)
		c = Database.connection_pool.cursor()
		c.execute('''CREATE TABLE IF NOT EXISTS items
					 (item TEXT PRIMARY KEY, emoji TEXT)''')
		c.execute('''CREATE TABLE IF NOT EXISTS combinations
					 (item1 TEXT, item2 TEXT, result TEXT, isNew INTEGER,
					 PRIMARY KEY (item1, item2),
					 FOREIGN KEY (result) REFERENCES items (item))''')
		c.execute('''CREATE TABLE IF NOT EXISTS combination_counts
					(input_item TEXT, result_item TEXT, count INTEGER,
					PRIMARY KEY (input_item, result_item),
					FOREIGN KEY (input_item) REFERENCES items (item),
					FOREIGN KEY (result_item) REFERENCES items (item))''')  # Updated structure for combination_counts
		Database.connection_pool.commit()

	def getDbConnections():
		return Database.connection_pool

	@staticmethod
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
			result = c.fetchone()
			if result is None:
				# print(f"Trying combination: {item1} + {item2}")
				result = ItemTester.itemTester(item1, item2)

				# Insert the item into the items table, ignoring if it already exists
				c.execute("INSERT OR IGNORE INTO items VALUES (?, ?)", (result['result'], result['emoji']))
				if c.rowcount == 1:
					print(f"Item added to database: {result['result']} ({result['emoji']}) from {item1} + {item2}")

				c.execute("INSERT INTO combinations VALUES (?, ?, ?, ?)", (item1, item2, result['result'], result['isNew']))

				if result['isNew']:
					print(f"New item discovered: {result['result']} ({result['emoji']}) from {item1} + {item2}")

				# Update combination counts
				c.execute("INSERT OR IGNORE INTO combination_counts (input_item, result_item, count) VALUES (?, ?, 0)", (item1, result['result']))
				c.execute("UPDATE combination_counts SET count = count + 1 WHERE input_item = ? AND result_item = ?", (item1, result['result']))
				c.execute("INSERT OR IGNORE INTO combination_counts (input_item, result_item, count) VALUES (?, ?, 0)", (item2, result['result']))
				c.execute("UPDATE combination_counts SET count = count + 1 WHERE input_item = ? AND result_item = ?", (item2, result['result']))

				conn.commit()
				return result['result'] if result['isNew'] else None
		return None
