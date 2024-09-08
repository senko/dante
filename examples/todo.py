import sys

from dante import Dante

db = Dante("todo.db")
collection = db["todos"]


def help():
    print("Usage: todo.py <command> [args...]")
    print("Commands:")
    print("  list")
    print("  add <todo>")
    print("  remove <todo>")
    print("  done <todo>")
    print("  undone <todo>")


def main():
    if len(sys.argv) < 2:
        help()
        sys.exit(-1)

    command = sys.argv[1]

    if command == "list":
        for i, todo in enumerate(collection):
            print(f"{i+1}. {todo['text']}{' (done)' if todo['done'] else ''}")

        return
    elif command == "help":
        help()
        return

    if len(sys.argv) < 3:
        print("Missing argument: todo")
        sys.exit(-1)

    todo = sys.argv[2]

    if command == "add":
        collection.insert({"text": todo, "done": False})
    elif command == "remove":
        collection.delete(text=todo)
    elif command == "done":
        collection.set({"done": True}, text=todo)
    elif command == "undone":
        collection.set({"done": False}, text=todo)
    else:
        print(f"Unknown command: {command} (try 'help' to see available commands)")
        sys.exit(-1)


main()
