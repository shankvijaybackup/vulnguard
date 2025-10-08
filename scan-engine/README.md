# VulnGuard Scan Engine

This directory contains the foundational components for the VulnGuard scan engine, as outlined in the Product Requirements Document (PRD). It uses Docker to create a self-contained, scriptable vulnerability scanner powered by OWASP ZAP.

## Components

- **Dockerfile**: Defines the Docker image that bundles OWASP ZAP with a Python environment and our custom scanning script.
- **scanner_worker.py**: The Python script that automates the ZAP scan process. It accepts a target URL, performs a spider and an active scan, and generates a JSON report.
- **requirements.txt**: Lists the necessary Python libraries for the worker script.

## Prerequisites

- Docker installed and running on your local machine.

## How to Build and Run

Follow these steps from within the vulnguard directory in your terminal.

### 1. Build the Docker Image

First, build the Docker image for the scanner. This command will package ZAP and all the necessary scripts and dependencies into an image named `vulnguard-scanner`.

```bash
docker build -t vulnguard-scanner ./scan-engine
```

### 2. Run a Scan

Once the image is built, you can run a scan against any target URL. This command starts the container in detached mode, runs the ZAP baseline scan, and then executes our `scanner_worker.py` script against the specified target.

Replace `http://testphp.vulnweb.com` with your target URL.

```bash
# Generate a random API key for this session
ZAP_API_KEY=$(openssl rand -hex 16)

# Create reports directory if it doesn't exist
mkdir -p reports

# Run the scan in a detached container
docker run -d \
  --name vulnguard-scanner \
  -v $(pwd)/reports:/zap/wrk:rw \
  -e ZAP_API_KEY=${ZAP_API_KEY} \
  -p 8080:8080 \
  vulnguard-scanner zap.sh -daemon \
  -port 8080 \
  -host 0.0.0.0 \
  -config api.key=${ZAP_API_KEY} \
  -config api.disablekey=false \
  -config api.addrs.addr.name=.* \
  -config api.addrs.addr.regex=true
```

**Note**: This starts the ZAP daemon. We will execute the scan in the next step.

### 3. Execute the Python Scan Script

Find the container ID of the running scanner:

```bash
docker ps
```

Now, execute the Python worker script inside that container:

```bash
# replace <CONTAINER_ID> with the actual ID from the command above
docker exec <CONTAINER_ID> python3 /zap/scanner_worker.py --target http://testphp.vulnweb.com
```

### 4. Monitor Progress and View Results

The scan will take several minutes. You can monitor its progress by viewing the container's logs:

```bash
docker logs -f <CONTAINER_ID>
```

When the scan is complete, the JSON report will be saved in the `vulnguard/reports` directory on your local machine.

### 5. Clean Up

After the scan is complete, you can stop and remove the container:

```bash
docker stop <CONTAINER_ID>
docker rm <CONTAINER_ID>
```

## Alternative: Using Docker Compose

For a more automated approach, you can use the provided docker-compose.yml:

```bash
# Start the scan engine
docker-compose up -d

# Run a scan
docker exec vulnguard-zap python3 /zap/scanner_worker.py --target http://testphp.vulnweb.com

# View logs
docker-compose logs -f zap

# Stop the service
docker-compose down
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ZAP_API_KEY` | Randomly generated | API key for ZAP authentication |
| `ZAP_PORT` | `8080` | Port for ZAP API |

### Scan Options

The scanner supports various options that can be configured:

- **Spider Scan**: Discovers application structure and endpoints
- **Active Scan**: Performs security testing on discovered endpoints
- **Report Generation**: Creates JSON reports of findings

### Custom Scan Policies

You can mount custom ZAP scan policies:

```bash
docker run -d \
  -v $(pwd)/policies:/zap/policies:ro \
  # ... other options
```

## Troubleshooting

### Common Issues

1. **ZAP API Key Issues**: Ensure the API key is properly set and matches between container and script
2. **Port Conflicts**: Make sure port 8080 is available
3. **Memory Issues**: Large applications may require more memory: `-m 2g`
4. **Timeout Issues**: Increase timeout for larger applications

### Debug Mode

For debugging, you can run the container interactively:

```bash
docker run -it --name vulnguard-debug \
  -v $(pwd)/reports:/zap/wrk:rw \
  -e ZAP_API_KEY=${ZAP_API_KEY} \
  -p 8080:8080 \
  vulnguard-scanner /bin/bash
```

Then manually start ZAP and run the script:

```bash
zap.sh -daemon -port 8080 -host 0.0.0.0 -config api.key=${ZAP_API_KEY} -config api.disablekey=false
python3 /zap/scanner_worker.py --target http://example.com
```

## Next Steps

This component serves as the core of the "Scan Worker" microservice. The next steps in building the full VulnGuard platform will involve:

1. **Building the Backend Orchestrator API** to programmatically manage and trigger these containerized scans.
2. **Developing the ML Classifier Service** to analyze the raw JSON output from these scans.
3. **Creating the Frontend dashboard** to interact with the API.

## Integration with VulnGuard Platform

The scan engine integrates with the larger VulnGuard ecosystem:

- **Backend API** (`/backend/`): Orchestrates scan jobs and manages results
- **ML Service** (`/ml-service/`): Classifies findings to reduce false positives
- **Frontend** (`/frontend/`): Provides user interface for scan management

## Security Considerations

- API keys are randomly generated for each session
- Containers run with non-root user where possible
- Network access is limited to necessary ports
- Reports contain sensitive data - handle appropriately in production

## Performance

- **Startup Time**: ~30 seconds for ZAP initialization
- **Scan Duration**: 2-10 minutes depending on application size
- **Memory Usage**: ~500MB - 1GB depending on target complexity
- **Storage**: Reports are typically 1-10MB per scan

## Contributing

When modifying the scan engine:

1. Update the Dockerfile if adding new dependencies
2. Test with multiple target applications
3. Ensure proper error handling in the worker script
4. Update documentation for any new features

## License

This component is part of the VulnGuard platform and follows the project's license terms.
