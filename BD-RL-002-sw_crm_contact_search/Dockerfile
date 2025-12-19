FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
ENV DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1 \
    DOTNET_CLI_TELEMETRY_OPTOUT=1 \
    NUGET_XMLDOC_MODE=skip \
    NUGET_FALLBACK_PACKAGES=
WORKDIR /src

COPY BD-RL-002-sw_crm_contact_search.sln .
COPY BD-RL-002-sw_crm_contact_search.csproj .
COPY repository_before/repository_before.csproj repository_before/
COPY repository_after/repository_after.csproj repository_after/
COPY tests/tests.csproj tests/

RUN dotnet restore BD-RL-002-sw_crm_contact_search.sln /p:DisableImplicitNuGetFallbackFolder=true
RUN dotnet restore tests/tests.csproj /p:DisableImplicitNuGetFallbackFolder=true

COPY . .

RUN dotnet build BD-RL-002-sw_crm_contact_search.sln -c Release --no-restore /p:DisableImplicitNuGetFallbackFolder=true
RUN dotnet build tests/tests.csproj -c Release --no-restore /p:DisableImplicitNuGetFallbackFolder=true

FROM build AS publish
RUN dotnet publish repository_after/repository_after.csproj -c Release -o /app/publish --no-build /p:DisableImplicitNuGetFallbackFolder=true
RUN dotnet test tests/tests.csproj -c Release --no-build --logger "trx;LogFileName=test-results.trx" /p:DisableImplicitNuGetFallbackFolder=true

FROM publish AS runtime
WORKDIR /src
ENTRYPOINT ["dotnet", "run", "--project", "BD-RL-002-sw_crm_contact_search.csproj"]
