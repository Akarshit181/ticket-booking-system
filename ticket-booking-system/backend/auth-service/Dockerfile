# How to run docker
# A Dockerfile is a set of instructions that tells Docker how to create an image for your application.
# docker compose build ----  Create the image
# docker compose up ------ uses this image build earlier and create container from that image  execute the cmd from the dockerfile
# docker compose up --build  --------   build the image if needed then imediately start the container
# In summary
# docker compose build → Creates or updates the Docker image by executing the Dockerfile.
# docker compose up → Creates and starts containers from those images.
# docker compose up --build → Builds the image first (if needed), then starts the containers in one command.





# Use the official lightweight Python 3.14 image as the base.
# "slim" keeps the image much smaller than the full Python image.
FROM python:3.14-slim


# ==========================
# Environment Variables
# ==========================

# Prevent Python from creating .pyc (compiled bytecode) files.
# They are unnecessary inside a Docker container and only consume space.
ENV PYTHONDONTWRITEBYTECODE=1

# Disable Python output buffering.
# This ensures logs are written immediately, which is important for
# viewing logs in Docker (docker logs).
ENV PYTHONUNBUFFERED=1


# ==========================
# Working Directory
# ==========================

# Set the default working directory inside the container.
# All subsequent commands will execute relative to /app.
WORKDIR /app


# ==========================
# Create Non-Root User
# ==========================

# Create a system group named "app".
# Create a system user named "app" belonging to that group.
#
# Running applications as root is a security risk.
# The application will run as this less-privileged user instead.
RUN addgroup --system app && \
    adduser --system --ingroup app app


# ==========================
# Install Dependencies
# ==========================

# Copy only the requirements file first.
#
# Docker caches each build layer. If only your application code changes
# but requirements.txt remains the same, Docker reuses the cached
# dependency installation layer, making builds much faster.
COPY requirements.txt .


# Upgrade pip and install project dependencies.
#
# --no-cache-dir prevents pip from storing downloaded packages,
# reducing the final image size.
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# ==========================
# Copy Application Source
# ==========================

# Copy the entire project into the container.
COPY . .


# ==========================
# File Permissions
# ==========================

# Give ownership of the application directory to the non-root user.
# Otherwise the "app" user may not have permission to access files.
RUN chown -R app:app /app


# ==========================
# Switch User
# ==========================

# From this point onward, all commands and the application itself
# will run as the "app" user instead of root.
USER app


# ==========================
# Network
# ==========================

# Inform Docker that this container listens on port 8000.
# This is mainly documentation and helps when mapping ports.
EXPOSE 8000


# ==========================
# Start Application
# ==========================

# Start the FastAPI application using Uvicorn.
#
# main:app
#   main -> main.py
#   app  -> FastAPI instance named "app"
#
# --host 0.0.0.0
#   Listen on all network interfaces so the application is accessible
#   from outside the container.
#
# --port 8000
#   Run the application on port 8000.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]