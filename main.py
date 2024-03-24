from components.bruteForce import BruteForce
from components.database import Database

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
			c.execute("SELECT item FROM items"))
			discovered_items = set(item[0] for item in c.fetchall())

		BruteForce.brute_force(discovered_items)

if __name__ == "__main__":
	main()