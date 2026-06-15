# Deployment Guide — Deploying to Railway

This guide outlines how to deploy the AI Interview System (FastAPI backend + Vite React frontend) as two separate services on Railway from your GitHub repository.

---

## 1. Prerequisites on Railway

1. Sign in to your [Railway Dashboard](https://railway.app/).
2. Click **New Project** -> **Deploy from GitHub repo**.
3. Select your repository: `AIMI`.
4. Railway will create a default service. You will configure this first service as the **Backend**, and then add a second service for the **Frontend**.

---

## 2. Deploying the Backend Service

Configure the first service in your Railway project to serve the FastAPI backend.

### Railway Settings
In your Railway dashboard, select the service and click the **Settings** tab:
1. **Service Name**: Rename it to `backend` (e.g. results in `backend-production.up.railway.app`).
2. **Root Directory**: Set this to `/backend`. This tells Railway to compile only the backend folder using the Python buildpack.
3. **Start Command**: Set the custom deploy start command to:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

### Persistent Volume (SQLite Database & Recordings)
Because the backend uses a local SQLite database file (`interview_system.db`) and saves video files under `recordings/`, you must attach a persistent volume so data is not wiped out on new deployments or restarts.
1. In the backend service dashboard, go to the **Volumes** tab.
2. Click **Add Volume**.
3. Name it `sqlite-data` (or similar).
4. Set the Mount Path to `/app` (since the root directory is `/backend`, the container mounts your code into `/app`). This will persist `interview_system.db` and the `recordings` directory.

### Environment Variables (Variables Tab)
Add the following keys:
- `PORT`: (Set automatically by Railway).
- `JWT_SECRET`: Generate a secure random string (e.g., `your-secure-production-jwt-key`).
- `GEMINI_API_KEY`: Your Google Gemini API key (`AIzaSy...`).
- `OPENAI_API_KEY`: Your OpenAI API key (if needed).
- `CORS_ORIGINS`: Set this to your frontend's Railway URL once it's created (e.g., `https://aimi-frontend.up.railway.app`).

---

## 3. Deploying the Frontend Service

Add a second service to your Railway project to serve the static Vite React frontend.

### Adding the Service
1. Click **+ New** on the Railway dashboard canvas.
2. Select **GitHub Repo** and choose `AIMI` again.
3. Railway will create a new service.

### Railway Settings
Select the new service and click the **Settings** tab:
1. **Service Name**: Rename it to `frontend` (e.g., `aimi-frontend.up.railway.app`).
2. **Root Directory**: Set this to `/frontend`.
3. **Build Command**: Set to `npm run build`.
4. **Start Command**: Set to serve the compiled static files:
   ```bash
   npx serve -s dist -l $PORT
   ```
   *(Railway automatically downloads `serve` and hosts your production static files via this command).*

### Environment Variables (Variables Tab)
Vite injects environment variables **at build time**. You must set the API url *before* the build triggers:
- `VITE_API_URL`: Set this to the public URL of your backend service followed by `/api` (e.g., `https://backend-production.up.railway.app/api`).

---

## 4. Production Verification Flow

1. Trigger the builds by clicking **Deploy** on both services.
2. Once the backend builds, grab its generated domain URL and update the frontend's `VITE_API_URL` environment variable.
3. Update the backend's `CORS_ORIGINS` environment variable to include the frontend's domain URL.
4. Verify by accessing your frontend domain. You should see the public Landing Page render. Clicking "Log In" or "Sign Up" should successfully communicate with the backend.
