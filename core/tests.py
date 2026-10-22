import json
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse


class WorkbenchPageTests(TestCase):
    def test_home_page_contains_editor_and_theme_controls(self):
        response = self.client.get(reverse("index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="code-input"')
        self.assertContains(response, 'id="theme-toggle"')
        self.assertContains(response, 'id="upload-file"')
        self.assertContains(response, 'id="history-list"')


class WorkbenchApiTests(TestCase):
    def test_explain_rejects_empty_code(self):
        response = self.client.post(
            reverse("api-explain"),
            data=json.dumps({"code": "  ", "problem": "Why does this fail?"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["ok"])

    @patch("core.views.rag.explain")
    def test_explain_returns_result_and_retrieved_sources(self, explain):
        explain.return_value = {
            "result": {"explanation": "The loop exceeds the list bounds."},
            "sources": [{"text": "Indexes start at zero.", "source": "guide.pdf", "page": 2, "score": .8}],
        }
        response = self.client.post(
            reverse("api-explain"),
            data=json.dumps({"code": "items[4]", "problem": "IndexError"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["sources"][0]["source"], "guide.pdf")

    @patch("core.views.rag.ingest", return_value=3)
    def test_upload_accepts_supported_text_files(self, ingest):
        upload = SimpleUploadedFile("notes.txt", b"Text about lists.", content_type="text/plain")
        response = self.client.post(reverse("api-upload"), {"file": upload})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["chunks"], 3)
        ingest.assert_called_once()

    def test_history_saves_and_restores_an_explanation(self):
        payload = {
            "code": "SELECT * FROM users;",
            "problem": "How should this be filtered?",
            "language": "sql",
            "result": {"explanation": "Add a WHERE clause."},
            "sources": [],
        }
        saved = self.client.post(
            reverse("api-history"), data=json.dumps(payload), content_type="application/json"
        )

        self.assertEqual(saved.status_code, 200)
        restored = self.client.get(reverse("api-history-detail", args=[saved.json()["id"]]))

        self.assertEqual(restored.status_code, 200)
        self.assertEqual(restored.json()["item"]["code"], payload["code"])
        self.assertEqual(restored.json()["item"]["language"], "sql")
