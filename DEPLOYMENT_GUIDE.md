# LEGOFIT Website Deployment Guide

## Overview
Your application consists of:
- **Flask server** (port 8050): Static HTML pages
- **Dash server** (port 8051): Interactive data visualizations
- **Integration**: Flask redirects to Dash for data pages

## Deployment Options

### Option 1: Railway (Recommended for Beginners)

#### Why Railway?
- Easy setup with GitHub integration
- Automatic deployments
- Good for Python applications
- Free tier available

#### Step-by-Step Deployment:

1. **Prepare Your Code**
   ```bash
   # Create a Procfile for Railway
   echo "web: python start_servers.py" > Procfile
   ```

2. **Create Railway Account**
   - Go to https://railway.app
   - Sign up with GitHub
   - Connect your repository

3. **Deploy**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository
   - Railway will automatically detect Python and install dependencies

4. **Configure Environment**
   - In Railway dashboard, go to Variables
   - Add any environment variables if needed

5. **Access Your Site**
   - Railway provides a URL like `https://your-app-name.railway.app`

#### Railway Configuration Files Needed:

**Procfile:**
```
web: python start_servers.py
```

**railway.json (optional):**
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python start_servers.py",
    "healthcheckPath": "/",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

---

### Option 2: Heroku

#### Why Heroku?
- Very popular platform
- Lots of documentation
- Easy to use

#### Step-by-Step Deployment:

1. **Install Heroku CLI**
   ```bash
   # On macOS
   brew install heroku/brew/heroku
   
   # Or download from https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Create Heroku App**
   ```bash
   heroku login
   heroku create your-legofit-app
   ```

3. **Create Required Files**

   **Procfile:**
   ```
   web: python start_servers.py
   ```

   **runtime.txt:**
   ```
   python-3.11.0
   ```

4. **Deploy**
   ```bash
   git add .
   git commit -m "Deploy to Heroku"
   git push heroku main
   ```

5. **Open Your App**
   ```bash
   heroku open
   ```

---

### Option 3: DigitalOcean App Platform

#### Why DigitalOcean?
- Good performance
- Reasonable pricing
- Easy scaling

#### Step-by-Step Deployment:

1. **Create DigitalOcean Account**
   - Go to https://cloud.digitalocean.com
   - Sign up and verify email

2. **Create App**
   - Go to Apps section
   - Click "Create App"
   - Connect your GitHub repository

3. **Configure App**
   - **Source**: Your GitHub repo
   - **Type**: Web Service
   - **Build Command**: `pip install -r requirements.txt`
   - **Run Command**: `python start_servers.py`

4. **Deploy**
   - Click "Create Resources"
   - Wait for deployment to complete

---

## Important Configuration Changes Needed

### 1. Update URLs for Production

You need to update hardcoded localhost URLs in your code:

**In `dash_app.py` (lines 11, 22, 24, 26, 30, 31, 44, 51, 52, 59, 60, 67, 68, 75, 76, 82, 83, 244, 346, 352, 358, 364, 390, 396, 402, 408, 414, 440, 447):**

Replace all instances of `http://localhost:8050` with your production URL.

**In `main.py` (lines 84, 88):**

Replace `http://localhost:8051` with your production URL.

### 2. Environment Variables

Create a `.env` file for local development:
```
FLASK_ENV=development
DASH_ENV=development
```

For production, set these in your hosting platform:
```
FLASK_ENV=production
DASH_ENV=production
```

### 3. Update Requirements

Your `requirements.txt` should include:
```
dash>=2.14,<3
dash-bootstrap-components>=1.6,<2
pandas>=2.0,<3
plotly>=5.18,<6
numpy>=1.24,<2
scikit-learn>=1.3,<2
flask>=2.3,<3
gunicorn>=21.0,<22
```

### 4. Production Server Configuration

For production, you might want to use a production WSGI server like Gunicorn:

**Create `wsgi.py`:**
```python
from main import server as application

if __name__ == "__main__":
    application.run()
```

**Update Procfile:**
```
web: gunicorn wsgi:application --bind 0.0.0.0:$PORT
```

---

## Testing Your Deployment

### Local Testing
1. Test your application locally:
   ```bash
   python start_servers.py
   ```
2. Visit http://localhost:8050
3. Test all navigation links
4. Test data pages (explorer, optimized)

### Production Testing
1. Check all static pages load correctly
2. Test navigation between pages
3. Test data visualization pages
4. Check all images and assets load
5. Test on different devices/browsers

---

## Troubleshooting Common Issues

### 1. Port Issues
- Production platforms assign ports dynamically
- Use environment variables for ports:
  ```python
  import os
  port = int(os.environ.get('PORT', 8050))
  ```

### 2. Static Files Not Loading
- Ensure all static file routes are correct
- Check file permissions
- Verify file paths are relative to project root

### 3. Dash Pages Not Working
- Check that both servers are running
- Verify redirect URLs are correct
- Test Dash server independently

### 4. Database/Data Issues
- Ensure all data files are included in deployment
- Check file paths in your code
- Verify data files are accessible

---

## Cost Comparison

| Platform | Free Tier | Paid Plans | Best For |
|----------|-----------|------------|----------|
| Railway | Yes (limited) | $5/month | Beginners |
| Heroku | No | $7/month | Popular choice |
| DigitalOcean | No | $5/month | Performance |
| AWS | Yes (limited) | Variable | Enterprise |

---

## Next Steps

1. **Choose your platform** (I recommend Railway for beginners)
2. **Update your code** with production URLs
3. **Test locally** with production settings
4. **Deploy** following the platform-specific steps
5. **Test thoroughly** in production
6. **Set up monitoring** and backups

---

## Support

If you encounter issues:
1. Check platform-specific documentation
2. Look at deployment logs
3. Test components individually
4. Consider starting with a simpler deployment and adding complexity gradually

Remember: Start with Railway - it's the easiest option for your first deployment!
