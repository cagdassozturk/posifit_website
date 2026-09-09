# POSIFIT Production Deployment Guide
## For 25-30 Concurrent Users + Custom Domain (renovation.legofit.eu)

## 🎯 **Requirements Analysis**
- **Concurrent Users**: 25-30 simultaneous users
- **Domain**: renovation.legofit.eu
- **Performance**: No feature breaking under load
- **Architecture**: Flask (static) + Dash (data) hybrid application

## 🏆 **Recommended Hosting Options**

### **Option 1: Hostinger VPS (Your Friend's Suggestion)**
**Best for**: Integrated domain + hosting, cost-effective

#### **Hostinger VPS Plans for Your Needs:**
- **VPS 1**: $3.99/month - 1 vCPU, 1GB RAM, 20GB SSD
- **VPS 2**: $7.99/month - 1 vCPU, 2GB RAM, 40GB SSD ⭐ **RECOMMENDED**
- **VPS 3**: $11.99/month - 2 vCPU, 4GB RAM, 80GB SSD

#### **Why VPS 2 is Perfect for You:**
- ✅ Handles 25-30 concurrent users
- ✅ 2GB RAM for Dash visualizations
- ✅ Root access for Python environment
- ✅ Built-in domain registration
- ✅ Cost-effective ($7.99/month)

#### **Step-by-Step Hostinger Deployment:**

1. **Purchase Hostinger VPS 2 Plan**
   - Go to https://www.hostinger.com/vps-hosting
   - Select VPS 2 plan
   - Choose your server location (Europe recommended)

2. **Register Domain**
   - Domain `renovation.legofit.eu` should already be configured
   - Ensure DNS points to your VPS IP address

3. **Server Setup**
   ```bash
   # Connect to your VPS via SSH
   ssh root@your-server-ip
   
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install Python and dependencies
   sudo apt install python3 python3-pip python3-venv nginx git
   
   # Install Node.js (for some Dash components)
   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
   sudo apt-get install -y nodejs
   ```

4. **Deploy Your Application**
   ```bash
   # Clone your repository
   git clone https://github.com/yourusername/legofit-website.git
   cd legofit-website
   
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   pip install gunicorn supervisor
   ```

5. **Configure Production Server**
   ```bash
   # Create production configuration
   sudo nano /etc/supervisor/conf.d/legofit.conf
   ```
   
   **Supervisor Configuration:**
   ```ini
   [program:legofit-flask]
   command=/root/legofit-website/venv/bin/gunicorn --bind 0.0.0.0:8050 --workers 3 --timeout 120 main:server
   directory=/root/legofit-website
   user=root
   autostart=true
   autorestart=true
   stderr_logfile=/var/log/legofit-flask.err.log
   stdout_logfile=/var/log/legofit-flask.out.log

   [program:legofit-dash]
   command=/root/legofit-website/venv/bin/python dash_app.py
   directory=/root/legofit-website
   user=root
   autostart=true
   autorestart=true
   stderr_logfile=/var/log/legofit-dash.err.log
   stdout_logfile=/var/log/legofit-dash.out.log
   ```

6. **Configure Nginx Reverse Proxy**
   ```bash
   sudo nano /etc/nginx/sites-available/renovation.legofit.eu
   ```
   
   **Nginx Configuration:**
   ```nginx
   server {
       listen 80;
       server_name renovation.legofit.eu www.renovation.legofit.eu;
       
       # Static files
       location /static/ {
           alias /root/legofit-website/static/;
           expires 1y;
           add_header Cache-Control "public, immutable";
       }
       
       location /assets/ {
           alias /root/legofit-website/assets/;
           expires 1y;
           add_header Cache-Control "public, immutable";
       }
       
       # Dash app (data pages)
       location /pilot_lux_explorer {
           proxy_pass http://127.0.0.1:8051;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           proxy_read_timeout 300;
           proxy_connect_timeout 300;
           proxy_send_timeout 300;
       }
       
       location /pilot_lux_optimized {
           proxy_pass http://127.0.0.1:8051;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           proxy_read_timeout 300;
           proxy_connect_timeout 300;
           proxy_send_timeout 300;
       }
       
       # Flask app (static pages)
       location / {
           proxy_pass http://127.0.0.1:8050;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

7. **Enable Site and Start Services**
   ```bash
   # Enable Nginx site
   sudo ln -s /etc/nginx/sites-available/renovation.legofit.eu /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   
   # Start your applications
   sudo supervisorctl reread
   sudo supervisorctl update
   sudo supervisorctl start all
   ```

8. **SSL Certificate (Free with Let's Encrypt)**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d renovation.legofit.eu -d www.renovation.legofit.eu
   ```

---

### **Option 2: DigitalOcean (Alternative)**
**Best for**: Better performance, more control

#### **DigitalOcean Droplet for Your Needs:**
- **Basic Droplet**: $6/month - 1 vCPU, 1GB RAM, 25GB SSD
- **Basic Droplet**: $12/month - 1 vCPU, 2GB RAM, 50GB SSD ⭐ **RECOMMENDED**

#### **Why DigitalOcean is Great:**
- ✅ Excellent performance
- ✅ Great documentation
- ✅ Easy scaling
- ✅ $12/month for 2GB RAM
- ✅ Built-in monitoring

#### **Deployment Steps:**
1. Create DigitalOcean account
2. Create droplet (Ubuntu 22.04)
3. Follow similar setup as Hostinger
4. Use DigitalOcean's domain management

---

### **Option 3: Railway (Easiest)**
**Best for**: No server management, automatic scaling

#### **Railway Configuration for 25-30 Users:**
- **Hobby Plan**: $5/month - Good for development
- **Pro Plan**: $20/month - Better for production ⭐ **RECOMMENDED**

#### **Why Railway Pro:**
- ✅ Automatic scaling
- ✅ No server management
- ✅ Built-in monitoring
- ✅ Easy domain connection
- ✅ Handles 25-30 users easily

---

## 🔧 **Production Optimizations for 25-30 Users**

### **1. Update Your Code for Production**

**Create `production_config.py`:**
```python
import os

# Production settings
PRODUCTION = os.environ.get('PRODUCTION', 'false').lower() == 'true'
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:8050')
DASH_URL = os.environ.get('DASH_URL', 'http://localhost:8051')

if PRODUCTION:
    # Production URLs
    FLASK_URL = BASE_URL
    DASH_URL = BASE_URL  # Same domain, different paths
else:
    # Development URLs
    FLASK_URL = "http://localhost:8050"
    DASH_URL = "http://localhost:8051"
```

### **2. Update Your Main Files**

**Update `main.py` for production:**
```python
# Replace hardcoded URLs with environment variables
@server.route('/pilot_lux_explorer')
def pilot_lux_explorer_redirect():
    dash_url = os.environ.get('DASH_URL', 'http://localhost:8051')
    return redirect(f'{dash_url}/pilot_lux_explorer')
```

**Update `dash_app.py` for production:**
```python
# Replace all localhost URLs with environment variables
base_url = os.environ.get('BASE_URL', 'http://localhost:8050')
```

### **3. Database Optimization (If Needed)**
```python
# Add connection pooling for concurrent users
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    'your_database_url',
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)
```

### **4. Caching for Performance**
```python
# Add Redis caching for better performance
import redis
from flask_caching import Cache

cache = Cache(app, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://localhost:6379'
})
```

---

## 💰 **Cost Comparison for 25-30 Users**

| Platform | Monthly Cost | Domain Cost | Total/Month | Setup Difficulty |
|----------|--------------|-------------|-------------|------------------|
| **Hostinger VPS** | $7.99 | $1.25 | **$9.24** | Medium |
| DigitalOcean | $12.00 | $1.25 | **$13.25** | Medium |
| Railway Pro | $20.00 | $1.25 | **$21.25** | Easy |
| AWS EC2 | $15-30 | $1.25 | **$16.25-31.25** | Hard |

---

## 🎯 **My Recommendation for You**

**Go with Hostinger VPS 2 ($7.99/month)** because:

1. ✅ **Cost-effective**: Only $9.24/month total
2. ✅ **Integrated**: Domain + hosting in one place
3. ✅ **Sufficient power**: 2GB RAM handles 25-30 users
4. ✅ **Your friend's suggestion**: You trust their recommendation
5. ✅ **Easy domain setup**: Built-in domain management

### **Next Steps:**
1. **Purchase Hostinger VPS 2** ($7.99/month)
2. **Register domain** `legofit-explorer.com` ($1.25/month)
3. **Follow the Hostinger setup guide** above
4. **Test with 25-30 users** to ensure performance

Would you like me to help you with any specific part of the Hostinger setup, or do you have questions about the other options?
