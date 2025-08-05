# GitLab Container Registry Hub

A centralized dashboard for monitoring and exploring container images stored in GitLab Container Registries. This application provides a searchable interface to browse container images across multiple GitLab projects, view tags, and access image metadata.

## Features

- Collects and indexes container images from GitLab Container Registry
- Provides a searchable web interface for container images
- Shows image tags with creation dates and sizes
- Displays README information for container images
- Automatically updates container image information

## Installation

### Prerequisites

- Docker and Docker Compose
- Access to a GitLab instance with Container Registry enabled
- GitLab API token with read access to container registry

### Using Docker Compose

1. Clone this repository
2. Create a `config.yaml` file (see Configuration section)
3. Run the application using Docker Compose:

```bash
docker-compose up -d
```

## Configuration

The application requires a configuration file `config.yaml` with the following structure:

```yaml
api:
  url: https://gitlab.example.com
  token: <token for api access>
couchdb:
  url: http://couchdb:5984
  user: admin
  password: password
```

### Configuration Options

- `api.url`: URL of your GitLab instance
- `api.token`: GitLab API token with read access to container registry
- `couchdb.url`: URL of the CouchDB instance (use the service name from docker-compose)
- `couchdb.user`: CouchDB username
- `couchdb.password`: CouchDB password

## Docker Compose Example

```yaml
volumes:
  couchdb-data:

services:
  couchdb:
    image: couchdb
    restart: unless-stopped
    ports:
      - 5984:5984
    volumes:
      - couchdb-data:/opt/couchdb/data
    environment:
      COUCHDB_USER: admin
      COUCHDB_PASSWORD: password

  gitlab-container-registry-hub:
    build: .
    restart: unless-stopped
    ports:
      - 8000:8000
    depends_on:
      - couchdb
    volumes:
      - ./config.yaml:/app/config.yml
    command: ["--config-file", "/app/config.yml", "--mode", "web"]

  collector:
    build: .
    restart: unless-stopped
    depends_on:
      - couchdb
    volumes:
      - ./config.yaml:/app/config.yml
    command: ["--config-file", "/app/config.yml", "--mode", "collect"]
```

## Usage

The application runs in two modes:

1. **Collector Mode**: Periodically fetches container image information from GitLab
2. **Web Mode**: Provides a web interface to browse and search container images

After starting the application with Docker Compose, access the web interface at http://localhost:8000

## TODO

See file [TODO](TODO.md) for planned features and improvements.