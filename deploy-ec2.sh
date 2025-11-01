#!/bin/bash

# CC_MINI EC2 Quick Deploy Script
# This script automates the basic setup for deploying CC_MINI to EC2
# Run this after connecting to your EC2 instance

set -e

echo "🚀 Starting CC_MINI EC2 Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as ubuntu user
if [ "$USER" != "ubuntu" ]; then
    print_error "This script should be run as the ubuntu user"
    exit 1
fi

print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

print_status "Installing system dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    nginx \
    redis-server \
    docker.io \
    docker-compose \
    curl \
    unzip \
    htop \
    net-tools

print_status "Installing Node.js 18..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

print_status "Configuring services..."
sudo systemctl start redis-server
sudo systemctl enable redis-server
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu

print_status "Setting up Elasticsearch..."
mkdir -p /home/ubuntu/elasticsearch-data

# Pull Elasticsearch image
docker pull docker.elastic.co/elasticsearch/elasticsearch:8.11.0

# Run Elasticsearch container
docker run -d \
  --name cc-mini-elasticsearch \
  --restart unless-stopped \
  -p 9200:9200 \
  -p 9300:9300 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" \
  -v /home/ubuntu/elasticsearch-data:/usr/share/elasticsearch/data \
  docker.elastic.co/elasticsearch/elasticsearch:8.11.0

print_status "Waiting for Elasticsearch to start..."
sleep 30

# Test Elasticsearch
if curl -s http://localhost:9200/_cluster/health > /dev/null; then
    print_status "Elasticsearch is running successfully"
else
    print_warning "Elasticsearch may not be ready yet. Check with: curl http://localhost:9200/_cluster/health"
fi

print_status "Cloning application (if from GitHub)..."
echo "If your code is on GitHub, run:"
echo "git clone https://github.com/yourusername/CC_MINI.git"
echo "Otherwise, upload your code to /home/ubuntu/CC_MINI"

# Check if CC_MINI directory exists
if [ -d "/home/ubuntu/CC_MINI" ]; then
    cd /home/ubuntu/CC_MINI
    
    print_status "Setting up Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    
    if [ -f "requirements.txt" ]; then
        print_status "Installing Python dependencies..."
        pip install -r requirements.txt
    else
        print_warning "requirements.txt not found. Install manually later."
    fi
    
    # Create basic .env template
    if [ ! -f ".env" ]; then
        print_status "Creating .env template..."
        cat > .env << 'EOF'
# Database
USE_DYNAMODB=true
AWS_REGION=us-east-1

# S3 Configuration (replace with your bucket name)
AWS_S3_BUCKET_NAME=your-notesllm-bucket-name

# Redis
CELERY_BROKER_URL=redis://localhost:6379/0

# Elasticsearch
ELASTICSEARCH_URL=http://localhost:9200

# Security (replace with a strong secret key)
SECRET_KEY=your-super-secret-key-here-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# LLM (optional - get from Mistral AI)
# MISTRAL_API_KEY=your-mistral-api-key

# Application
DEBUG=false
CORS_ORIGINS=http://localhost:5173
EOF
        chmod 600 .env
        print_warning "Created .env template. Please edit /home/ubuntu/CC_MINI/.env with your actual values."
    fi
    
    # Setup frontend if directory exists
    if [ -d "CC_mini" ]; then
        print_status "Setting up frontend..."
        cd CC_mini
        npm install
        
        # Create frontend .env template
        if [ ! -f ".env" ]; then
            cat > .env << 'EOF'
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=CC Mini
EOF
            print_warning "Created frontend .env template. Update VITE_API_URL with your domain/IP."
        fi
        
        print_status "Building frontend..."
        npm run build
        cd ..
    fi
else
    print_warning "CC_MINI directory not found. Please clone or upload your code to /home/ubuntu/CC_MINI"
fi

print_status "Creating systemd service files..."

# API Service
sudo tee /etc/systemd/system/cc-mini-api.service << 'EOF'
[Unit]
Description=CC Mini API Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/CC_MINI
Environment=PATH=/home/ubuntu/CC_MINI/venv/bin
EnvironmentFile=/home/ubuntu/CC_MINI/.env
ExecStart=/home/ubuntu/CC_MINI/venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Celery Worker Service
sudo tee /etc/systemd/system/cc-mini-worker.service << 'EOF'
[Unit]
Description=CC Mini Celery Worker
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/CC_MINI
Environment=PATH=/home/ubuntu/CC_MINI/venv/bin
EnvironmentFile=/home/ubuntu/CC_MINI/.env
ExecStart=/home/ubuntu/CC_MINI/venv/bin/celery -A celery_worker worker --loglevel=info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

print_status "Configuring Nginx..."
sudo tee /etc/nginx/sites-available/cc-mini << 'EOF'
server {
    listen 80;
    server_name _;

    # Frontend (React build)
    location / {
        root /home/ubuntu/CC_MINI/CC_mini/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Direct API access (for development/testing)
    location /docs {
        proxy_pass http://localhost:8000/docs;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /health {
        proxy_pass http://localhost:8000/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # File upload size limit
    client_max_body_size 100M;
}
EOF

# Enable nginx site
sudo ln -sf /etc/nginx/sites-available/cc-mini /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
if sudo nginx -t; then
    print_status "Nginx configuration is valid"
else
    print_error "Nginx configuration has errors"
    exit 1
fi

print_status "Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable cc-mini-api
sudo systemctl enable cc-mini-worker
sudo systemctl start nginx
sudo systemctl enable nginx

echo ""
echo "🎉 Basic setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit /home/ubuntu/CC_MINI/.env with your AWS credentials and settings"
echo "2. Create DynamoDB tables (see EC2_DEPLOYMENT_COMPLETE.md)"
echo "3. Create S3 bucket (see S3_SETUP_GUIDE.md)"
echo "4. Update frontend .env with your domain/IP"
echo "5. Start the services:"
echo "   sudo systemctl start cc-mini-api"
echo "   sudo systemctl start cc-mini-worker"
echo ""
echo "Check service status:"
echo "   sudo systemctl status cc-mini-api"
echo "   sudo systemctl status cc-mini-worker"
echo "   sudo systemctl status nginx"
echo ""
echo "Test the deployment:"
echo "   curl http://localhost:8000/health"
echo "   curl http://localhost:9200/_cluster/health"
echo ""
print_status "Setup script completed successfully!"