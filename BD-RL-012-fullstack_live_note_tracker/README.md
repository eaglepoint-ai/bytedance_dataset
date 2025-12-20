# Note Tracker Application

This is a simple note-taking application that allows users to create and edit notes in real-time. The application is built with a client-server architecture and uses WebSockets for real-time communication.

## Getting Started

To get started with the application, you need to have Docker and Docker Compose installed on your machine.

1.  **Build and run the application:**

    ```bash
    docker compose up --build
    ```

    This will build the Docker images for the client, server, and tests, and then start the services.

2.  **Access the application:**

    Once the services are up and running, you can access the application in your browser at `http://localhost:5173`.

## Services

The application is composed of the following services:

*   **`client`**: A React application built with Vite that serves the user interface.
*   **`server`**: A Node.js application with an Express server that handles the business logic and communicates with the client via WebSockets.
*   **`tests`**: A service that runs the frontend and backend tests.

## Development

For development, you can run the client and server applications using Docker Compose.

### Client and Server

To run the client and server in development mode:

```bash
docker-compose up --build
```

The client will be available at `http://localhost:5173` and the server will be running on port 3000.

## Testing

To run the tests, you can use the `tests` service defined in the `docker-compose.yml` file.

```bash
docker-compose run --build tests
```

This will run both the frontend and backend tests.
