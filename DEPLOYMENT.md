# 🚀 Deployment Guide

This guide explains how to deploy the TradeLocker API to different platforms.

## 📋 **Prerequisites**

1. **Docker** installed on your system
2. **TradeLocker credentials** configured
3. **API key** for securing endpoints

## 🐳 **Docker Deployment**

### **Local Docker**
```bash
# Build and run locally
docker-compose up --build

# Or use the provided script
./run_local.sh
```

### **Docker Hub**
```bash
# Build the image
docker build -t tradelocker-api .

# Tag for Docker Hub
docker tag tradelocker-api yourusername/tradelocker-api:latest

# Push to Docker Hub
docker push yourusername/tradelocker-api:latest
```

## ☁️ **Cloud Platform Deployment**

### **AWS App Runner**
1. Create a new App Runner service
2. Connect your GitHub repository
3. Configure environment variables:
   - `TRADELOCKER_USERNAME`
   - `TRADELOCKER_PASSWORD`
   - `TRADELOCKER_SERVER`
   - `API_KEY`
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`

### **Google Cloud Run**
```bash
# Build and deploy to Cloud Run
gcloud run deploy tradelocker-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars TRADELOCKER_USERNAME=your_username,TRADELOCKER_PASSWORD=your_password,TRADELOCKER_SERVER=your_server,API_KEY=your_api_key
```

### **Azure Container Instances**
```bash
# Build and push to Azure Container Registry
az acr build --registry yourregistry --image tradelocker-api .

# Deploy to Container Instances
az container create \
  --resource-group your-rg \
  --name tradelocker-api \
  --image yourregistry.azurecr.io/tradelocker-api:latest \
  --ports 8000 \
  --environment-variables TRADELOCKER_USERNAME=your_username TRADELOCKER_PASSWORD=your_password TRADELOCKER_SERVER=your_server API_KEY=your_api_key
```

### **DigitalOcean App Platform**
1. Create a new App in DigitalOcean
2. Connect your GitHub repository
3. Configure environment variables
4. Set build command: `pip install -r requirements.txt`
5. Set run command: `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`

### **Heroku**
```bash
# Create Heroku app
heroku create your-tradelocker-api

# Set environment variables
heroku config:set TRADELOCKER_USERNAME=your_username
heroku config:set TRADELOCKER_PASSWORD=your_password
heroku config:set TRADELOCKER_SERVER=your_server
heroku config:set API_KEY=your_api_key

# Deploy
git push heroku main
```

## 🔧 **Environment Variables**

Required environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `TRADELOCKER_USERNAME` | Your TradeLocker username | `your_username` |
| `TRADELOCKER_PASSWORD` | Your TradeLocker password | `your_password` |
| `TRADELOCKER_SERVER` | Your TradeLocker server | `your_server` |
| `TRADELOCKER_ENVIRONMENT` | TradeLocker environment URL | `https://demo.tradelocker.com` |
| `API_KEY` | API key for authentication | `your-secret-api-key-here` |

## 🔐 **Security Considerations**

1. **Never commit credentials** to version control
2. **Use environment variables** for sensitive data
3. **Rotate API keys** regularly
4. **Use HTTPS** in production
5. **Implement rate limiting** if needed

## 📊 **Monitoring**

### **Health Checks**
```bash
# Test health endpoint
curl https://your-api-url/health
```

### **Logs**
- Check container logs: `docker logs container_name`
- Monitor application logs in your cloud platform
- Set up alerting for errors

### **Metrics**
- Monitor response times
- Track API usage
- Monitor error rates

## 🔄 **CI/CD Pipeline**

### **GitHub Actions Example**
```yaml
name: Deploy to Cloud

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Build and push to registry
        run: |
          docker build -t your-registry/tradelocker-api:${{ github.sha }} .
          docker push your-registry/tradelocker-api:${{ github.sha }}
      
      - name: Deploy to cloud platform
        run: |
          # Your deployment commands here
```

## 🚨 **Troubleshooting**

### **Common Issues**

1. **Connection refused**
   - Check if the API is running
   - Verify port configuration
   - Check firewall settings

2. **Authentication errors**
   - Verify TradeLocker credentials
   - Check API key configuration
   - Ensure environment variables are set

3. **Container won't start**
   - Check Docker logs
   - Verify Dockerfile configuration
   - Ensure all dependencies are installed

### **Debug Commands**
```bash
# Check container status
docker ps

# View logs
docker logs container_name

# Test API locally
curl http://localhost:8000/health

# Check environment variables
docker exec container_name env
```

## 📚 **Next Steps**

1. **Set up monitoring** and alerting
2. **Configure SSL/TLS** certificates
3. **Implement rate limiting**
4. **Set up backup strategies**
5. **Create disaster recovery plan**

For more information, see the main [README.md](README.md) file. 