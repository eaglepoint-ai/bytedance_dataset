# BD-RL-002-sw_crm_contact_search

This repository contains a small .NET console benchmark around a CRM contact search refactor.  
The "before" app keeps the data access in a single class, while the "after" app layers caching and typed records to demonstrate an incremental improvement.

## Requirements

- [.NET SDK 8.0+](https://dotnet.microsoft.com/download)

## Projects

- `BD-RL-002-sw_crm_contact_search.csproj` - Launcher that lets you choose which console app to run.
- `repository_before/` - Legacy console app exposing helper functions that read in-memory dictionaries.
- `repository_after/` - Refined console app exposing the same contact data via a reusable catalog and typed records.
- `tests/` - xUnit test project validating that both implementations serve the same data and performance envelope.

## Usage

```bash
# Launcher (prompts for before/after)
dotnet run --project BD-RL-002-sw_crm_contact_search.csproj

# Run projects individually
dotnet run --project repository_before/repository_before.csproj
dotnet run --project repository_after/repository_after.csproj

# Execute tests
dotnet test tests/tests.csproj

# Run individual performance suites in Docker
docker compose run --rm tests dotnet test tests/tests.csproj --filter RepositoryBeforePerformanceTests -c Release -v minimal
docker compose run --rm tests dotnet test tests/tests.csproj --filter RepositoryAfterPerformanceTests -c Release -v minimal
```

## Tasks

1. Run the Dockerized app with `docker compose up app` (or `docker-compose up app` on older installs) to start the launcher container.
2. Test the Docker image with `docker compose run --rm tests` to execute `dotnet test` inside the build container and remove it afterward.

## Containers

- `docker build -t bd-rl-002-sw_crm_contact_search .` builds the .NET image and runs the Release build steps.
- `docker run --rm bd-rl-002-sw_crm_contact_search` executes the xUnit suite inside the container.
- `docker compose up app` (or `docker-compose up app`) launches the interactive launcher via `dotnet run` inside the container (bind mounted to the local workspace).
