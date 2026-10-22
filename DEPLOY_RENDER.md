# Deploying Codehelper to Render

The repository includes a Render Blueprint in `render.yaml`. It configures a
Django web service, WhiteNoise static-file serving, startup migrations, and a
persistent disk mounted at `/var/data` for the SQLite history and ChromaDB data.

## Deploy

1. In Render, create a **New Blueprint Instance** and connect
   `SparshLonare/AI_Fusion`.
2. Review the service and disk plan and apply the Blueprint. A persistent disk
   requires a paid Render web service; Render's default filesystem is ephemeral,
   so uploaded/indexed documents and SQLite history would otherwise be lost on
   restarts or deploys.
3. Set `GEMINI_API_KEY` in the service's Environment settings. Keep it private;
   do not add it to this repository.
4. After the first deploy is live, open the service Shell and run
   `python manage.py seed_kb` to index the bundled PDF references. This calls
   Gemini's embedding API. New uploads are then stored on the persistent disk.

The Blueprint generates `SECRET_KEY`, sets production `DEBUG=false`, runs
database migrations at startup, and collects static files during the build.
The build uses temporary paths because Render disks are only mounted at runtime.
