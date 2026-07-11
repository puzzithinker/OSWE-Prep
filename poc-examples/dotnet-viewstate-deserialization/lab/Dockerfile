FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src
COPY app/*.csproj ./
RUN dotnet restore
COPY app/ ./
RUN dotnet publish -c Release -o /out

FROM mcr.microsoft.com/dotnet/aspnet:8.0
WORKDIR /app
COPY --from=build /out .
RUN echo "OSWE{dotnet_json_deserial_lab_flag}" > /flag.txt
ENV ASPNETCORE_URLS=http://0.0.0.0:8080
EXPOSE 8080
ENTRYPOINT ["dotnet", "DotNetLab.dll"]
