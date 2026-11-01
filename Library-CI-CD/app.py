"""A small in-memory Library Management System built with Flask."""

from flask import Flask, jsonify, request

app = Flask(__name__)

# In-memory data keeps this project simple; it resets when the app restarts.
books = [
    {"id": 1, "title": "The Hobbit", "author": "J.R.R. Tolkien"},
    {"id": 2, "title": "Pride and Prejudice", "author": "Jane Austen"},
]
next_book_id = 3


@app.route("/", methods=["GET"])
def home():
    """Show a short welcome page."""
    return (
        "<h1>Library Management System</h1>"
        "<p>Use <code>/api/books</code> to browse the library.</p>"
    )


@app.route("/api/books", methods=["GET"])
def list_books():
    """Return all books as JSON."""
    return jsonify(books), 200


@app.route("/api/books", methods=["POST"])
def add_book():
    """Add a book from a JSON body containing a title and author."""
    global next_book_id

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400

    title = data.get("title")
    author = data.get("author")
    if not isinstance(title, str) or not title.strip():
        return jsonify({"error": "A non-empty title is required."}), 400
    if not isinstance(author, str) or not author.strip():
        return jsonify({"error": "A non-empty author is required."}), 400

    book = {
        "id": next_book_id,
        "title": title.strip(),
        "author": author.strip(),
    }
    books.append(book)
    next_book_id += 1
    return jsonify(book), 201


@app.route("/api/books/<int:book_id>", methods=["DELETE"])
def delete_book(book_id):
    """Delete the book with the requested ID."""
    for book in books:
        if book["id"] == book_id:
            books.remove(book)
            return "", 204
    return jsonify({"error": "Book not found."}), 404


if __name__ == "__main__":
    # Keep this exact startup line visible in application logs.
    print("SERVICERUNNING", flush=True)
    app.run(
        host="0.0.0.0",
        port=8000,
        debug=False,
    )
