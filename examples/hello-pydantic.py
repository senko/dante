from dante import Dante
from pydantic import BaseModel


class Message(BaseModel):
    name: str
    text: str


# Open the database and get the collection for messages
db = Dante("mydatabase.db")
collection = db[Message]

# Insert a model to the database
obj = Message(name="Dante", text="Hello world!")
collection.insert(obj)

# Find a model with the specified attribute(s)
result = collection.find_one(name="Dante")
print(result.text)

# Find a model in the collection with the attribute name=Dante
# and update (overwrite) it with the new model data
result.name = "Virgil"
collection.update(result, name="Dante")
