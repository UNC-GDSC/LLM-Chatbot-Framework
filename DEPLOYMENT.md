# Deployment Guide

This guide covers various deployment options for the LLM Chatbot Framework.

## Table of Contents
- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Production Deployment](#production-deployment)
- [Cloud Platforms](#cloud-platforms)
- [Security Considerations](#security-considerations)

## Local Development

### Setup

1. Install Python 3.9+:
```bash
python --version  # Verify Python installation
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your settings
```

5. Run the application:
```bash
uvicorn app.main:app --reload --port 8000
```

Visit http://localhost:8000/docs for API documentation.

## Docker Deployment

### Using Docker Compose (Recommended)

1. Configure environment:
```bash
cp .env.example .env
# Edit .env with your settings
```

2. Build and run:
```bash
docker-compose up --build
```

3. Run in detached mode:
```bash
docker-compose up -d
```

4. View logs:
```bash
docker-compose logs -f app
```

5. Stop containers:
```bash
docker-compose down
```

### Using Docker Only

1. Build the image:
```bash
docker build -t llm-chatbot-framework .
```

2. Run the container:
```bash
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  --name chatbot-api \
  llm-chatbot-framework
```

## Production Deployment

### Prerequisites

- PostgreSQL database
- Redis (optional, for caching)
- Domain name with SSL certificate
- Reverse proxy (Nginx/Caddy)

### Environment Configuration

Create a production `.env` file:

```bash
# Application
ENVIRONMENT=production
DEBUG=False

# Security
SECRET_KEY=<generate-strong-secret-key>

# Database
DATABASE_URL=postgresql://user:password@db-host:5432/chatbot_db

# LLM Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Redis
REDIS_URL=redis://redis-host:6379/0

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Monitoring
ENABLE_METRICS=true
SENTRY_DSN=<your-sentry-dsn>
```

### Database Setup

1. Create PostgreSQL database:
```sql
CREATE DATABASE chatbot_db;
CREATE USER chatbot WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE chatbot_db TO chatbot;
```

2. Run migrations (if using Alembic):
```bash
alembic upgrade head
```

### Nginx Configuration

Create `/etc/nginx/sites-available/chatbot-api`:

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Enable and restart Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/chatbot-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### SSL/TLS with Let's Encrypt

```bash
sudo certbot --nginx -d api.yourdomain.com
```

### Systemd Service

Create `/etc/systemd/system/chatbot-api.service`:

```ini
[Unit]
Description=LLM Chatbot Framework
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/chatbot-framework
Environment="PATH=/opt/chatbot-framework/venv/bin"
ExecStart=/opt/chatbot-framework/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable chatbot-api
sudo systemctl start chatbot-api
sudo systemctl status chatbot-api
```

## Cloud Platforms

### AWS Deployment

#### Using ECS/Fargate

1. Build and push Docker image to ECR
2. Create ECS task definition
3. Configure Application Load Balancer
4. Create ECS service
5. Configure RDS for PostgreSQL
6. Configure ElastiCache for Redis

#### Using EC2

1. Launch EC2 instance
2. Install dependencies
3. Clone repository
4. Setup systemd service
5. Configure security groups
6. Setup RDS and ElastiCache

### Google Cloud Platform

#### Using Cloud Run

```bash
gcloud run deploy chatbot-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Azure

#### Using Azure Container Instances

```bash
az container create \
  --resource-group chatbot-rg \
  --name chatbot-api \
  --image <your-image> \
  --dns-name-label chatbot-api \
  --ports 8000
```

### Heroku

1. Create `Procfile`:
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

2. Deploy:
```bash
heroku create chatbot-api
heroku addons:create heroku-postgresql:hobby-dev
git push heroku main
```

### Railway

1. Connect GitHub repository
2. Add environment variables
3. Deploy automatically

## Security Considerations

### 1. Environment Variables
- Never commit `.env` file
- Use secrets management (AWS Secrets Manager, HashiCorp Vault)
- Rotate API keys regularly

### 2. Database Security
- Use strong passwords
- Enable SSL connections
- Restrict network access
- Regular backups

### 3. API Security
- Enable rate limiting
- Use HTTPS only
- Implement request validation
- Monitor for suspicious activity

### 4. Updates
- Keep dependencies updated
- Monitor security advisories
- Apply patches promptly

### 5. Monitoring
- Enable application monitoring
- Set up error tracking (Sentry)
- Configure alerts
- Review logs regularly

## Scaling Considerations

### Horizontal Scaling
- Use load balancer
- Deploy multiple instances
- Session management with Redis

### Database Scaling
- Use connection pooling
- Read replicas for queries
- Database caching

### Performance Optimization
- Enable response caching
- Use CDN for static assets
- Optimize database queries
- Monitor resource usage

## Backup and Recovery

### Database Backups
```bash
# PostgreSQL backup
pg_dump -h localhost -U chatbot chatbot_db > backup.sql

# Restore
psql -h localhost -U chatbot chatbot_db < backup.sql
```

### Automated Backups
- Configure automated database backups
- Store backups in secure location
- Test restore procedures regularly

## Health Checks

The application provides health check endpoints:
- `/health` - Basic health check
- `/metrics` - Prometheus metrics

Configure monitoring tools to check these endpoints regularly.

## Troubleshooting

### Common Issues

1. **Database connection errors**
   - Check DATABASE_URL
   - Verify database is running
   - Check network connectivity

2. **LLM API errors**
   - Verify API keys
   - Check rate limits
   - Monitor API status

3. **Performance issues**
   - Check database queries
   - Monitor resource usage
   - Review logs for errors

### Logs

View application logs:
```bash
# Docker
docker-compose logs -f app

# Systemd
journalctl -u chatbot-api -f
```
