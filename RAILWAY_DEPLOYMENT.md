# Railway Deployment Guide

This guide will help you deploy your Credit Card Parser application on Railway with separate frontend and backend services.

## Prerequisites

1. Railway account (sign up at [railway.app](https://railway.app))
2. MongoDB database (you can use Railway's MongoDB addon or external MongoDB Atlas)
3. Environment variables configured

## Deployment Steps

### 1. Backend Service Deployment

1. **Create a new Railway project:**
   - Go to Railway dashboard
   - Click "New Project"
   - Choose "Deploy from GitHub repo" (or upload your code)

2. **Configure Backend Service:**
   - **IMPORTANT**: Set the root directory to `backend` folder
   - Railway will automatically detect the `backend/Dockerfile`
   - Set the following environment variables:
     ```
     MONGODB_URI=your_mongodb_connection_string
     PORT=8000
     ```

3. **Deploy:**
   - Railway will automatically build and deploy your backend
   - Note the generated URL (e.g., `https://your-backend-name.railway.app`)

### 2. Frontend Service Deployment

1. **Create another Railway service:**
   - In the same project, click "New Service"
   - Choose "Deploy from GitHub repo"
   - **IMPORTANT**: Set the root directory to `frontend` folder
   - Railway will detect the `frontend/Dockerfile`

2. **Configure Frontend Service:**
   - Set environment variables:
     ```
     REACT_APP_API_URL=https://your-backend-name.railway.app
     ```

3. **Deploy:**
   - Railway will build and deploy your frontend
   - Note the generated URL (e.g., `https://your-frontend-name.railway.app`)

### 3. Alternative: Deploy from Root Directory

If you want to deploy from the root directory, you need to:

1. **For Backend Service:**
   - Set root directory to project root
   - Set build context to `backend/`
   - Railway will use `backend/Dockerfile`

2. **For Frontend Service:**
   - Set root directory to project root  
   - Set build context to `frontend/`
   - Railway will use `frontend/Dockerfile`

### 3. Environment Variables

#### Backend Environment Variables:
```
MONGODB_URI=mongodb://username:password@host:port/database
FRONTEND_ORIGIN=https://your-frontend-domain.railway.app
PORT=8000
```

#### Frontend Environment Variables:
```
REACT_APP_API_URL=https://your-backend-domain.railway.app
```

### 4. Database Setup

1. **Using Railway MongoDB Addon:**
   - In your Railway project, click "New"
   - Select "Database" → "MongoDB"
   - Railway will provide the connection string automatically

2. **Using External MongoDB:**
   - Use MongoDB Atlas or your own MongoDB instance
   - Set the `MONGODB_URI` environment variable with your connection string

### 5. Custom Domains (Optional)

1. **Backend Custom Domain:**
   - Go to your backend service settings
   - Click "Domains" → "Custom Domain"
   - Add your domain and configure DNS

2. **Frontend Custom Domain:**
   - Go to your frontend service settings
   - Click "Domains" → "Custom Domain"
   - Add your domain and configure DNS

## File Structure for Railway

```
creditcard_parser/
├── backend/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── railway.json
│   ├── requirements.txt
│   ├── main.py
│   ├── parser.py
│   └── database_mongodb.py
├── frontend/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── railway.json
│   ├── nginx.conf
│   ├── package.json
│   └── src/
└── RAILWAY_DEPLOYMENT.md
```

## Troubleshooting

### Common Issues:

1. **Build Failures:**
   - Check Dockerfile syntax
   - Ensure all dependencies are in requirements.txt/package.json
   - Check Railway build logs

2. **Connection Issues:**
   - Verify environment variables are set correctly
   - Check CORS settings in backend
   - Ensure MongoDB connection string is correct

3. **Health Check Failures:**
   - Verify health check endpoints are working
   - Check if services are binding to correct ports
   - Review Railway service logs

### Useful Commands:

```bash
# Test backend locally
cd backend
docker build -t creditcard-backend .
docker run -p 8000:8000 -e MONGODB_URI=your_uri creditcard-backend

# Test frontend locally
cd frontend
docker build -t creditcard-frontend .
docker run -p 80:80 creditcard-frontend
```

## Monitoring

1. **Railway Dashboard:**
   - Monitor service health
   - View logs and metrics
   - Check resource usage

2. **Application Logs:**
   - Access logs through Railway dashboard
   - Set up log aggregation if needed

## Scaling

1. **Horizontal Scaling:**
   - Railway automatically handles load balancing
   - Add more instances in service settings

2. **Vertical Scaling:**
   - Upgrade service plan for more resources
   - Monitor performance metrics

## Security Considerations

1. **Environment Variables:**
   - Never commit sensitive data to git
   - Use Railway's environment variable management

2. **CORS Configuration:**
   - Set specific origins in backend CORS settings
   - Avoid using wildcard (*) in production

3. **Database Security:**
   - Use strong passwords
   - Enable MongoDB authentication
   - Consider IP whitelisting

## Support

- Railway Documentation: [docs.railway.app](https://docs.railway.app)
- Railway Discord: [discord.gg/railway](https://discord.gg/railway)
- GitHub Issues: Create issues in your repository
