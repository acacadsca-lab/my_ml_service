## 🌐 Deployment

The project is configured for Onrender deployment:

1. **Create a Render account and connect your repository**
   - Go to [render.com](https://render.com)
   - Sign up and connect your GitHub account
   - Authorize Render to access your repositories

2. **Create a new Web Service**
   - Click "New +" and select "Web Service"
   - Select your repository: `acacadsca-lab/lakshminarayanangsworksonai`
   - Choose the branch: `main`

3. **Configure the Web Service**
   - **Name**: Give your service a name (e.g., `ai-chat-service`)
   - **Runtime**: Select `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn aichatprojectfinal.wsgi:application`
   - **Instance Type**: Choose based on your needs (free tier available)

4. **Set Environment Variables**
   - In the Render dashboard, go to your service's "Environment" tab
   - Add the following environment variables:
     ```
     DEBUG=False
     SECRET_KEY=your-secret-key-here
     DATABASE_URL=postgresql://user:password@your-render-db-url
     ALLOWED_HOSTS=your-app-name.onrender.com
     ```

5. **Connect Database**
   - Create a PostgreSQL database in Render
   - Copy the internal database URL
   - Paste it as the `DATABASE_URL` environment variable

6. **Deploy**
   - Click "Create Web Service"
   - Render will automatically deploy on every push to the main branch
   - Monitor the deployment in the "Logs" tab

7. **Run Migrations**
   - After deployment, go to the "Shell" tab
   - Run: `python aichatprojectfinal/manage.py migrate`
   - Collect static files: `python aichatprojectfinal/manage.py collectstatic --noinput`