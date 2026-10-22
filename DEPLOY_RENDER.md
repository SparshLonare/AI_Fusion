# Deploy Codehelper to Render Free

The root `render.yaml` configures a free Render web service. It indexes the
bundled `kb_seed/` PDFs during the build, then collects static files and runs
database migrations when the service starts.

## Deploy

1. In Render, choose **New → Blueprint** and connect the GitHub repository
   `SparshLonare/AI_Fusion` on the `master` branch. Keep the default Blueprint
   path (`render.yaml`).
2. Enter your `GEMINI_API_KEY` when prompted. Render generates `SECRET_KEY`.
   Keep the Gemini key in Render's secret settings; do not add it to GitHub.
3. Confirm the service plan is **Free**, review the Blueprint, and choose
   **Apply**. The build installs dependencies, calls Gemini to embed the bundled
   PDFs, and collects static files.
4. Watch the service's deploy logs. When the deployment finishes, open the
   `onrender.com` URL Render shows for the service.

## Free-tier limits

Render Free services sleep after 15 minutes without traffic and may take about
a minute to wake. Their filesystem is temporary: uploaded/indexed documents
and SQLite search history can disappear after a restart, sleep, or redeploy.
The bundled PDFs are seeded again by each build, but user uploads and search
history are not durable. Free web services do not provide Dashboard Shell
access, which is why the seed command runs during the build.

Seeding calls Gemini's embedding API on every build. Render hosting may be
free, but Gemini API usage is separate and subject to Google's quota and billing.
