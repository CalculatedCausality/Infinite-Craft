import sqlite3

def get_db_connection():
	conn = sqlite3.connect('infinite_craft.db')
	return conn

def search_items(item, conn):
	c = conn.cursor()
	c.execute("SELECT DISTINCT item FROM (SELECT item1 AS item FROM combinations UNION SELECT item2 AS item FROM combinations UNION SELECT result AS item FROM combinations) WHERE item LIKE ?", (f"%{item}%",))
	items = c.fetchall()
	return [i[0] for i in items]

def find_combination(item, conn, processed=None):
	if processed is None:
		processed = set()

	if item in processed:
		return

	processed.add(item)

	c = conn.cursor()
	c.execute("SELECT item1, item2 FROM combinations WHERE result = ?", (item,))
	combination = c.fetchone()

	if combination is None:
		return None

	item1, item2 = combination
	print(f"To craft {item}, you need: {item1} and {item2}")

	if item1 != item:
		find_combination(item1, conn, processed)

	if item2 != item:
		find_combination(item2, conn, processed)

def main():
	conn = get_db_connection()

	while True:
		search_term = input("Enter the item you want to craft (or 'quit' to exit): ")

		if search_term.lower() == 'quit':
			break

		matching_items = search_items(search_term, conn)

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
		find_combination(desired_item, conn)
		print()

	conn.close()

if __name__ == "__main__":
	main()