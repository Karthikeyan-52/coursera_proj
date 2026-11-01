"""Unit tests for the Flask Library Management System API."""

import unittest

import app as library_app


class LibraryApiTests(unittest.TestCase):
    """Check the main page and book API behavior."""

    def setUp(self):
        self.original_books = list(library_app.books)
        self.original_next_id = library_app.next_book_id
        library_app.books[:] = [
            {"id": 1, "title": "The Hobbit", "author": "J.R.R. Tolkien"},
        ]
        library_app.next_book_id = 2
        self.client = library_app.app.test_client()

    def tearDown(self):
        library_app.books[:] = self.original_books
        library_app.next_book_id = self.original_next_id

    def test_home_page_returns_welcome_content(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Library Management System", response.data)

    def test_list_books_returns_json(self):
        response = self.client.get("/api/books")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()[0]["title"], "The Hobbit")

    def test_add_book_returns_created_book(self):
        response = self.client.post(
            "/api/books",
            json={"title": "Dune", "author": "Frank Herbert"},
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.get_json(),
            {"id": 2, "title": "Dune", "author": "Frank Herbert"},
        )
        self.assertEqual(len(library_app.books), 2)

    def test_add_book_rejects_missing_title(self):
        response = self.client.post(
            "/api/books",
            json={"author": "Frank Herbert"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_add_book_rejects_non_json_body(self):
        response = self.client.post("/api/books", data="not json")

        self.assertEqual(response.status_code, 400)

    def test_delete_book_returns_no_content(self):
        response = self.client.delete("/api/books/1")

        self.assertEqual(response.status_code, 204)
        self.assertEqual(library_app.books, [])

    def test_delete_unknown_book_returns_not_found(self):
        response = self.client.delete("/api/books/999")

        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
