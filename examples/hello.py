from dante import Dante

# Create 'mydatabase.db' in current directory and open it
# (you can omit the database name to create a temporary in-memory database.)
db = Dante("mydatabase.db")

# Use 'mycollection' collection (also known as a "table")
collection = db["mycollection"]

# Insert a dictionary to the database
data = {"name": "Dante", "text": "Hello World!"}
collection.insert(data)

# Find a dictionary with the specified attribute(s)
result = collection.find_one(name="Dante")
print(result["text"])

new_data = {"name": "Virgil", "text": "Hello World!"}
collection.update(new_data, name="Dante")
