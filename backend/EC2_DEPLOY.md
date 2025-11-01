EC2 Deployment guide for NotesLLM

This guide covers deploying the backend API + worker to an EC2 instance.

1. Instance & IAM

- Choose Amazon Linux 2 or Ubuntu 22.04 LTS AMI
- Create an IAM role for the instance with policies:
  - `AmazonDynamoDBFullAccess` (or scoped to specific tables)
  - `AmazonEC2ContainerRegistryReadOnly` (if using ECR)
  - `AmazonS3ReadOnlyAccess` (if using S3 for artifacts)
- Attach role to EC2 instance

2. Security Group

- Allow inbound TCP 22 (SSH) from admin IP
- Allow inbound TCP 8000 (API) from your trusted sources or ELB
- Allow inbound Redis/Elasticsearch only if colocated and needed

3. Install runtime

```bash
# Ubuntu example
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-pip git
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

4. Systemd services (uvicorn + Celery)

- Create service unit for uvicorn: `/etc/systemd/system/notesllm-api.service`

```
[Unit]
Description=NotesLLM API
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/app
EnvironmentFile=/home/ubuntu/app/.env
ExecStart=/home/ubuntu/venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

- Create service unit for Celery worker: `/etc/systemd/system/notesllm-celery.service`

```
[Unit]
Description=NotesLLM Celery Worker
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/app
EnvironmentFile=/home/ubuntu/app/.env
ExecStart=/home/ubuntu/venv/bin/celery -A celery_worker worker --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
```

5. Environment & Secrets

- Use EC2 IAM role for Dynamo credentials; for other secrets set them in `/home/ubuntu/app/.env`
- Required env vars (examples):
  - `USE_DYNAMODB=true`
  - `AWS_REGION=us-east-1`
  - `MONGO_URI` (if migrating)
  - `CELERY_BROKER_URL=redis://localhost:6379/0`
  - `ELASTICSEARCH_URL=http://localhost:9200`
  - `SECRET_KEY` etc.

6. Docker alternative

- Build a Docker image and run with `docker-compose` on EC2, or push to ECR and run via ECS/EC2.

7. Monitoring

- Use CloudWatch for logs, set up alarms for CPU/memory, and ensure backups for DynamoDB.

8. Notes

- For production, provision Elasticsearch as a managed service (OpenSearch Service) rather than co-locating.
