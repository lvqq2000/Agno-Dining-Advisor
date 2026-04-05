# Agno-Dining-Advisor

Agno Dining Advisor is a simple open-source restaurant recommendation tool. For now, it only supports restaurants in Melbourne. It is built using Agno with an AI-powered workflow, including database-driven prompt construction, semantic matching (CAG), retrieval-augmented generation (RAG), conditional logic, and SSE streaming output.

## Table of Contents

- [Agno-Dining-Advisor](#agno-dining-advisor)
  - [Table of Contents](#table-of-contents)
  - [Architecture Overview](#architecture-overview)
  - [Setup Instructions](#setup-instructions)
    - [Prerequisites](#prerequisites)
    - [1. Open a terminal and clone the Repository](#1-open-a-terminal-and-clone-the-repository)
    - [2. Navigate to the project directory](#2-navigate-to-the-project-directory)
    - [3. Environment Setup](#3-environment-setup)
  - [How to run the project](#how-to-run-the-project)
    - [1. Install Make (if not already installed)](#1-install-make-if-not-already-installed)
    - [2. Run the project](#2-run-the-project)
    - [3. Run tests](#3-run-tests)

## Architecture Overview

TO DO

## Setup Instructions

### Prerequisites

Before you begin, ensure you have the following installed on your system:

- [Docker](https://www.docker.com/get-started) (v20.0 or higher)
- [Git](https://git-scm.com/) - Optional, required only for running Git commands in the terminal

### 1. Open a terminal and clone the Repository

MacOS / Linux: Open Terminal

Windows: Open Git Bash, Command Prompt, or PowerShell

```bash
git clone https://github.com/lvqq2000/Agno-Dining-Advisor
```

This command downloads the repository, creates a local directory named `Agno-Dining-Advisor`.

### 2. Navigate to the project directory

```bash
cd Agno-Dining-Advisor
```

### 3. Environment Setup

Create a `.env` file in the root directory and copy the content from `.env.example` file. Fill in the required environment variables.

## How to run the project

This project uses `make` to simplify common development commands.  
`make` is a build automation tool that lets you run predefined commands (defined in a `Makefile`) with simple shortcuts, instead of typing long commands manually.

### 1. Install Make (if not already installed)

- **MacOS**
  
  ```bash
  xcode-select --install
  ```

- **Linux (Ubuntu/Debian)**
  
  ```bash
  sudo apt update
  sudo apt install make
  ```

- **Windows**
  - Use Git Bash (recommended), or
  - Install WSL and follow the Linux instructions, or
  - Install via Chocolatey:
  
    ```bash
    choco install make
    ```

### 2. Run the project

After completing the setup:

```bash
# Install dependencies and prepare the project
make setup

# Start the project
make run
```

### 3. Run tests

```bash
# Run all tests
make test
```

Notes

- Make sure Docker is running before starting the project.
- If you encounter issues, check the .env configuration and ensure all required variables are set.
