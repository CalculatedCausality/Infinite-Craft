from components.bruteForce import BruteForce
from components.database import Database

def initialize_items(items):
	with Database.db_lock, Database.getDbConnections() as conn:
		c = conn.cursor()
		for item in items:
			c.execute("INSERT OR IGNORE INTO items VALUES (?, '')", (item,))

def main():
	Database.initConnectionPool()

	initial_items = ['cloud', 'earth', 'fire', 'lake', 'ocean', 'sea', 'steam', 'water', 'wind']
	initialize_items(initial_items)

	print('Beginning')

	while True:
		with Database.db_lock, Database.getDbConnections() as conn:
			c = conn.cursor()
			c.execute("SELECT item FROM items")
			discovered_items = set(item[0] for item in c.fetchall())

		BruteForce.brute_force(discovered_items)

if __name__ == "__main__":
	main()