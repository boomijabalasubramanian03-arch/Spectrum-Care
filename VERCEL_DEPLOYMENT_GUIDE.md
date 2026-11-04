# VERCEL DEPLOYMENT GUIDE — SPECTRUM CARE (CHROMA CONTEXT)

This guide walks you through deploying **Spectrum Care (Chroma Context)** to Vercel step by step.

---

## Architecture Overview on Vercel

- **Frontend**: Built with **React 18 + Vite**, fully optimized for Vercel's global Edge CDN, client-side routing (SPA), and instant SSL.
- **Backend**: Because the computer vision backend utilizes PyTorch, Ultralytics YOLOv8, and OpenCV (which exceed Vercel's 250 MB serverless package limit), the recommended and professional approach is:
  1. **Deploy Frontend on Vercel** (Free, instant global URL).
  2. **Connect to Backend API**:
     - **For Viva / College Demo**: Use **`ngrok`** or **`localtunnel`** to expose your local running FastAPI server to the internet with HTTPS.
     - **For 24/7 Cloud Hosting**: Deploy the backend container on **Render.com** (Free Docker service) or **Railway**, and set the backend URL in Vercel.

---

## Method 1: Deploying via Vercel Web Dashboard (Recommended)

### Step 1: Push Code to GitHub
1. Create a GitHub repository (e.g., `spectrum-care` or `chroma-context`).
2. Commit and push your project to GitHub.

### Step 2: Import into Vercel
1. Log in to [vercel.com](https://vercel.com) (sign in with your GitHub account).
2. Click **"Add New..."** $\to$ **"Project"**.
3. Select your GitHub repository and click **"Import"**.

### Step 3: Configure Build & Output Settings
In the Vercel project configuration screen:
- **Framework Preset**: `Vite`
- **Root Directory**: Click `Edit` and select `frontend` (or leave default if deploying directly from frontend folder).
- **Build Command**: `npm run build`
- **Output Directory**: `dist`
- **Install Command**: `npm install`

### Step 4: Environment Variables (Connect Backend)
Under **Environment Variables**, add:
- **Name**: `VITE_API_URL`
- **Value**: Your backend API URL:
  - Example for Live Demo: `https://xxxx.ngrok-free.app`
  - Example for Cloud: `https://spectrum-care-api.onrender.com`
  - *(If left blank, it uses relative routes)*

### Step 5: Click "Deploy"
Vercel will build your React application in ~45 seconds and give you a live production URL (e.g., `https://spectrum-care.vercel.app`).

---

## Method 2: Deploying via Vercel CLI (Fast Terminal Deployment)

If you prefer terminal commands:

1. Install Vercel CLI globally:
   ```bash
   npm install -g vercel
   ```
2. Navigate to the frontend directory:
   ```bash
   cd C:\Users\Welcome\Downloads\chroma-context-project-corrected-v0.5\project\frontend
   ```
3. Run the deploy command:
   ```bash
   vercel
   ```
4. Follow the interactive prompts:
   - *Set up and deploy?* **Y**
   - *Which scope?* (Select your account)
   - *Link to existing project?* **N**
   - *Project name?* `spectrum-care`
   - *In which directory is your code located?* `./`
5. To deploy directly to production:
   ```bash
   vercel --prod
   ```

---

## Exposing Your Local Backend for College Demo (Using Ngrok)

When demonstrating your Vercel live URL to examiners:
1. Start your local FastAPI backend:
   ```powershell
   cd backend
   .\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
2. In a second terminal, start ngrok:
   ```bash
   ngrok http 8000
   ```
3. Copy the HTTPS forwarding address (e.g., `https://7a3b-xxx.ngrok-free.app`).
4. In your Vercel Dashboard $\to$ **Settings** $\to$ **Environment Variables**:
   - Add/Update: `VITE_API_URL` = `https://7a3b-xxx.ngrok-free.app`
   - Redeploy the latest deployment.
5. Your Vercel frontend is now live on the internet and communicating directly with your deep learning vision backend!
