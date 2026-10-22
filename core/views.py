import json
import logging

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from . import rag
from .models import ExplanationHistory

logger = logging.getLogger(__name__)
MAX_UPLOAD_SIZE = 10 * 1024 * 1024


def index(request):
    return render(request, "index.html")


def _error(message, status):
    return JsonResponse({"ok": False, "error": message}, status=status)


@csrf_exempt
def upload(request):
    if request.method != "POST":
        return _error("Method not allowed.", 405)
    uploaded_file = request.FILES.get("file")
    if uploaded_file is None:
        return _error("A file is required in the 'file' field.", 400)
    if not uploaded_file.name.lower().endswith((".pdf", ".txt")):
        return _error("Only PDF and TXT files are allowed.", 400)
    if uploaded_file.size > MAX_UPLOAD_SIZE:
        return _error("File size must not exceed 10 MB.", 400)

    try:
        chunk_count = rag.ingest(uploaded_file)
    except Exception:
        logger.exception("Knowledge-base upload failed for %s", uploaded_file.name)
        return _error("The file could not be processed. Please try again.", 500)
    return JsonResponse({"ok": True, "filename": uploaded_file.name, "chunks": chunk_count})


@csrf_exempt
def explain(request):
    if request.method != "POST":
        return _error("Method not allowed.", 405)
    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return _error("Request body must contain valid JSON.", 400)
    if not isinstance(payload, dict):
        return _error("Request body must be a JSON object.", 400)

    code = payload.get("code")
    problem = payload.get("problem")
    if not isinstance(code, str) or not code.strip():
        return _error("Code must not be empty.", 400)
    if not isinstance(problem, str):
        return _error("Problem must be a string.", 400)

    try:
        response = rag.explain(code[:4000], problem)
    except Exception:
        logger.exception("Code explanation request failed")
        return _error("The explanation could not be generated. Please try again.", 500)
    return JsonResponse({
        "ok": True,
        "result": response["result"],
        "sources": response["sources"],
    })


@csrf_exempt
def files(request):
    if request.method != "GET":
        return _error("Method not allowed.", 405)
    try:
        sources = rag.list_sources()
    except Exception:
        logger.exception("Could not list knowledge-base files")
        return _error("The knowledge-base files could not be loaded.", 500)
    return JsonResponse({"ok": True, "files": sources})


@csrf_exempt
def history(request):
    if request.method == "GET":
        try:
            entries = ExplanationHistory.objects.only("id", "title", "language", "created_at")[:50]
            return JsonResponse({"ok": True, "history": [
                {"id": entry.id, "title": entry.title, "language": entry.language,
                 "created_at": entry.created_at.isoformat()}
                for entry in entries
            ]})
        except Exception:
            logger.exception("Could not load explanation history")
            return _error("Search history could not be loaded.", 500)

    if request.method == "POST":
        try:
            payload = json.loads(request.body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return _error("Request body must contain valid JSON.", 400)
        if not isinstance(payload, dict):
            return _error("Request body must be a JSON object.", 400)
        code = payload.get("code")
        problem = payload.get("problem", "")
        language = payload.get("language", "python")
        result = payload.get("result")
        sources = payload.get("sources", [])
        if not isinstance(code, str) or not code.strip() or not isinstance(problem, str):
            return _error("Code and problem must be valid text.", 400)
        if not isinstance(language, str) or not isinstance(result, dict) or not isinstance(sources, list):
            return _error("Explanation data is invalid.", 400)
        title = next((line.strip() for line in code.splitlines() if line.strip()), "Code explanation")[:120]
        try:
            entry = ExplanationHistory.objects.create(
                title=title, language=language[:24], code=code[:4000], problem=problem[:4000],
                result=result, sources=sources,
            )
            # Keep the newest 100 entries for this local application.
            stale_ids = list(ExplanationHistory.objects.order_by("-created_at").values_list("id", flat=True)[100:])
            if stale_ids:
                ExplanationHistory.objects.filter(id__in=stale_ids).delete()
        except Exception:
            logger.exception("Could not save explanation history")
            return _error("This explanation could not be saved to history.", 500)
        return JsonResponse({"ok": True, "id": entry.id, "created_at": timezone.localtime(entry.created_at).isoformat()})

    return _error("Method not allowed.", 405)


@csrf_exempt
def history_detail(request, entry_id):
    if request.method != "GET":
        return _error("Method not allowed.", 405)
    try:
        entry = ExplanationHistory.objects.get(pk=entry_id)
    except ExplanationHistory.DoesNotExist:
        return _error("That history item could not be found.", 404)
    except Exception:
        logger.exception("Could not load explanation history item %s", entry_id)
        return _error("Search history could not be loaded.", 500)
    return JsonResponse({"ok": True, "item": {
        "id": entry.id, "title": entry.title, "language": entry.language,
        "code": entry.code, "problem": entry.problem,
        "result": entry.result, "sources": entry.sources,
        "created_at": entry.created_at.isoformat(),
    }})
