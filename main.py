from components.database import Database
from components.bruteForce import BruteForce

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