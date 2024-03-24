from components.database import Database
import concurrent.futures
import itertools


class BruteForce:

	@staticmethod
	def process_combinations(combinations):

		skippers = []
		results = []
		returner = 0

		for item1, item2 in combinations:

			# if any(skipper in item1 or skipper in item2 for skipper in skippers):
			# 	results.append(None)
			# 	continue


			returner += 1

			if returner > 50:
				results.append(None)
				return

			result = Database.process_item(item1, item2)
			if result:
				results.append(result)
		return results

	@staticmethod
	def brute_force(discovered_items):

		items_to_skip = set(Database.check_item_counts())
		discovered_items = (item for item in discovered_items if item not in items_to_skip)

		with concurrent.futures.ProcessPoolExecutor() as executor:
			chunk_size = 1000
			discovered_items_list = list(discovered_items)  # Convert set to list
			for i in range(0, len(discovered_items_list), chunk_size):
				combinations = itertools.combinations(discovered_items_list[i:i+chunk_size], 2)
				executor.map(BruteForce.process_combinations, [combinations])