# CodeSight

AI-powered health analysis for GitHub repositories. Instantly uncover risks, technical debt, and potential bugs in any public codebase.

![mq1](https://github.com/user-attachments/assets/65953c4e-d3b8-4db8-9f68-29351060dcaa)


## About The Project

In any software project, the biggest challenges are often invisible. CodeSight was built to bring these hidden risks to light. It bridges the gap between high-level project metrics and low-level code quality by combining quantitative commit analysis with the power of AI-driven code review.

This tool helps developers and managers make informed decisions by answering critical questions:
- Which files are the most fragile and need refactoring?
- What potential bugs or security risks are hiding in our highest-risk code?
- How can we get a quick, intelligent second opinion on complex files?

## Core Features

- **Instant Repository Analysis:** Simply provide a public GitHub repository URL to get started.
- **Risk File Visualization:** An interactive Treemap visualizes the entire codebase, with the size of each block representing its calculated risk score.
- **AI-Powered Code Review:** The top 3 highest-risk files are automatically reviewed by a GPT-4 model to identify potential bugs, bad practices, security vulnerabilities, and performance issues.
- **Interactive Dashboard:** Click any file in the Treemap to see its detailed AI review. Clicking a specific issue automatically scrolls to and highlights the exact line of code in question.

## How It Works

CodeSight performs a comprehensive two-part analysis:

1.  **Macro Analysis (The "Where"):** It fetches the repository's commit history to analyze file modification frequency and the number of unique authors for each file. This data is used to calculate a risk score, identifying "hotspot" files that are frequently changed by many people.
2.  **Micro Analysis (The "What"):** It then takes the files with the highest risk scores and sends their content to the OpenAI API for a deep, line-by-line code review, providing qualitative insights and actionable suggestions.

## Tech Stack

This project is a full-stack application built with modern technologies.

**Frontend:**
- **Framework:** Vue 3 (Composition API)
- **Styling:** Tailwind CSS
- **Visualization:** Apache ECharts

**Backend:**
- **Framework:** FastAPI
- **GitHub API:** PyGithub
- **AI Integration:** OpenAI API Client
- **Core Logic:** Python 3, Asyncio

## Getting Started

To get a local copy up and running, follow these simple steps.

### Prerequisites

- Git
- Python 3.8+
- Node.js v16+ & npm
- A GitHub Personal Access Token
- An OpenAI API Key

### Installation & Setup

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/JianHengHin0831/CodeSight.git
    cd CodeSight
    ```

2.  **Setup the Backend:**
    ```sh
    cd backend

    # Create and activate a virtual environment
    python -m venv venv
    source venv/bin/activate  # On Windows, use: venv\Scripts\activate

    # Install Python dependencies
    pip install -r requirements.txt

    # Create an environment file
    touch .env
    ```
    Now, open the newly created `.env` file and add your API keys:
    ```.env
    GITHUB_TOKEN="ghp_YourGitHubTokenHere"
    OPENAI_API_KEY="sk-YourOpenAIKeyHere"
    ```

3.  **Setup the Frontend:**
    ```sh
    # From the root directory 'CodeSight'
    cd frontend

    # Install Node.js dependencies
    npm install
    ```

### Running the Application

You will need to run the backend and frontend servers in two separate terminal windows.

1.  **Run the Backend Server:**
    ```sh
    # In the /backend directory
    uvicorn main:app --reload
    ```
    The backend API will be running at `http://127.0.0.1:8000`.

2.  **Run the Frontend Development Server:**
    ```sh
    # In the /frontend directory
    npm run dev
    ```
    The frontend application will be available at `http://localhost:3000`.

Open your browser to `http://localhost:3000` to use the application.

## What's Next

- **Private Repository Support:** Integrate GitHub OAuth to allow users to securely analyze their private projects.
- **Historical Trend Analysis:** Track a repository's health over time to visualize the impact of refactoring efforts.
- **Direct GitHub Integration:** Allow users to create a GitHub Issue directly from a finding in the AI Review Panel.
