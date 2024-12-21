# Use the official Ubuntu image as a base
FROM ubuntu:latest

# Set environment variables to avoid prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-venv curl libsndfile1

# Set the working directory
WORKDIR /app

# Copy only the necessary files for installation and testing
COPY pyproject.toml ./

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH
ENV PATH="/root/.local/bin:$PATH"

# Install all dependencies including dev-dependencies using Poetry
RUN poetry install --extras examples --with dev

# Copy the entire project into the container's work directory
COPY . .

# Run tests with pytest directly when the container is started
CMD ["poetry", "run", "pytest", "--cov=choralebricks", "--cov-report=term-missing"]
