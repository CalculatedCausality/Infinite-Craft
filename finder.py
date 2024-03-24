import sqlite3
import networkx as nx
import matplotlib.pyplot as plt

class ItemFinder:
	def __init__(self, db_path='infinite_craft.db'):
		self.conn = sqlite3.connect(db_path)

	def search_items(self, item):
		c = self.conn.cursor()
		c.execute("SELECT DISTINCT item FROM (SELECT item1 AS item FROM combinations UNION SELECT item2 AS item FROM combinations UNION SELECT result AS item FROM combinations) WHERE item LIKE ?", (f"%{item}%",))
		items = c.fetchall()
		return [i[0] for i in items]

	def find_combination(self, item, processed=None, G=None):
		if processed is None:
			processed = set()
		if G is None:
			G = nx.DiGraph()

		if item in processed:
			return G

		processed.add(item)

		c = self.conn.cursor()
		c.execute("SELECT item1, item2 FROM combinations WHERE result = ?", (item,))
		combination = c.fetchone()

		if combination is None:
			return None

		item1, item2 = combination
		G.add_edge(item1, item)
		G.add_edge(item2, item)
		print(f"To craft {item}, you need: {item1} and {item2}")

		if item1 != item:
			self.find_combination(item1, processed, G)

		if item2 != item:
			self.find_combination(item2, processed, G)

		return G

	def draw_graph(self, G, item):
		pos = nx.spring_layout(G)
		nx.draw(G, pos, with_labels=True, node_color='lightblue', edge_color='gray')
		plt.title(f"Crafting paths for {item}")
		plt.show()

	def run(self):
		while True:
			search_term = input("Enter the item you want to craft (or 'quit' to exit): ")

			if search_term.lower() == 'quit':
				break

			matching_items = self.search_items(search_term)

			if not matching_items:
				print("No matching items found.")
				continue

			print("Matching items:")
			for i, item in enumerate(matching_items, start=1):
				print(f"{i}. {item}")

			while True:
				try:
					selection = int(input("Enter the number of the desired item: "))
					if 1 <= selection <= len(matching_items):
						desired_item = matching_items[selection - 1]
						break
					else:
						print("Invalid selection. Please try again.")
				except ValueError:
					print("Invalid input. Please enter a number.")

			print(f"Selected item: {desired_item}\n")
			G = self.find_combination(desired_item)
			self.draw_graph(G, desired_item)
			print()

		self.conn.close()

if __name__ == "__main__":
	finder = ItemFinder()
	finder.run()