from components.database import Database
import concurrent.futures
import itertools
import random

class BruteForce:

	@staticmethod
	def process_combinations(combinations):

		skippers = []
		results = []

		for item1, item2 in combinations:

			if any(skipper in item1 or skipper in item2 for skipper in skippers):
				results.append(None)
				continue

			result = Database.process_item(item1, item2)
			results.append(result)
		return results

	@staticmethod
	def brute_force(discovered_items):
		items_to_skip = set(Database.check_item_counts())
		discovered_items = (item for item in discovered_items if item not in items_to_skip)

		item1_counts = dict()

		with concurrent.futures.ProcessPoolExecutor() as executor:
			chunk_size = 1000
			discovered_items_list = list(discovered_items)  # Convert set to list
			random.shuffle(discovered_items_list)  # Shuffle the list
			for i in range(0, len(discovered_items_list), chunk_size):
				combinations = []
				for item1, item2 in itertools.combinations(discovered_items_list[i:i+chunk_size], 2):
					if item1_counts.get(item1, 0) < 20:
						combinations.append((item1, item2))
						item1_counts[item1] = item1_counts.get(item1, 0) + 1
				executor.map(BruteForce.process_combinations, [combinations])