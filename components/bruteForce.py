import concurrent.futures
import itertools
import os

from components.database import Database


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