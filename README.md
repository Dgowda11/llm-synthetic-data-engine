# Synthetic Azure DevOps Test Data Generator

## Overview

The **Synthetic Azure DevOps Test Data Generator** is a Python-based application that generates realistic Azure DevOps project artifacts using Large Language Models (LLMs).

The primary goal of this project is to create synthetic yet realistic software development data that can be imported into Azure DevOps. This data can then be used for:

* Building Retrieval-Augmented Generation (RAG) applications
* Testing AI-powered Quality Engineering tools
* Demonstrating Azure DevOps workflows
* Learning Azure DevOps REST APIs
* Creating enterprise-like datasets without exposing real customer data

The generator accepts a **business domain** (for example, Banking, Insurance, Healthcare, or E-Commerce) and automatically creates a structured project hierarchy.

---

# Project Workflow

```text
User Input (Business Domain)
            │
            ▼
      OpenRouter LLM
            │
            ▼
 Generate Azure DevOps Artifacts
            │
            ▼
      Export as JSON Files
            │
            ▼
 Import into Azure DevOps
      (REST API + PAT Token)
```

---

# Features

The application generates the following Azure DevOps artifacts:

* Project
* Epics
* Features
* User Stories
* Acceptance Criteria
* Manual Test Cases
* Bugs
* Traceability Relationships

Future enhancements may include:

* Test Plans
* Test Suites
* Test Runs
* Automation Test Mappings
* Sprint Data
* Area Paths
* Iteration Paths

---

# Example

### Input

```text
Domain:
Banking
```

### Generated Output

```text
Project
│
├── Epic
│      ├── Feature
│      │      ├── User Stories
│      │      │      ├── Acceptance Criteria
│      │      │      ├── Manual Test Cases
│      │      │      └── Bugs
```

---

# Project Structure

```text
SyntheticAzureDevOpsGenerator/
│
├── app.py
├── config.py
├── requirements.txt
├── .env
│
├── prompts/
│
├── generator/
│
├── azure/
│
├── output/
│
└── utils/
```

---

# Technology Stack

| Component         | Technology                             |
| ----------------- | -------------------------------------- |
| Language          | Python                                 |
| LLM Provider      | OpenRouter                             |
| LLM Models        | OpenAI, Anthropic, Google Gemini, etc. |
| HTTP Client       | requests                               |
| Configuration     | python-dotenv                          |
| Data Validation   | Pydantic                               |
| Output Format     | JSON                                   |
| Azure Integration | Azure DevOps REST API                  |

---

# Prerequisites

* Python 3.12 or later
* OpenRouter API Key
* Azure DevOps Personal Access Token (PAT)
* Azure DevOps Organization
* Azure DevOps Project (or permissions to create one)

---

# Installation

Clone the repository:

```bash
git clone <repository-url>
cd SyntheticAzureDevOpsGenerator
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate the environment:

### Windows

```bash
.venv\Scripts\activate
```

### Linux / macOS

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# Environment Variables

Create a `.env` file in the project root.

```env
OPENROUTER_API_KEY=your_openrouter_api_key

AZURE_DEVOPS_ORG=https://dev.azure.com/your-organization

AZURE_DEVOPS_PROJECT=YourProject

AZURE_DEVOPS_PAT=your_personal_access_token
```

---

# Running the Application

```bash
python app.py
```

Example:

```text
Enter Business Domain:

Insurance Claim Processing
```

The application will generate synthetic Azure DevOps artifacts and save them as JSON files.

---

# Output

The generated files will be stored inside the `output/` directory.

Example:

```text
output/
│
├── project.json
├── epics.json
├── features.json
├── stories.json
├── acceptance_criteria.json
├── test_cases.json
├── bugs.json
└── traceability.json
```

---

# Azure DevOps Import

Once the JSON files are generated, the application can upload them into Azure DevOps using the Azure DevOps REST API.

The import process follows this order:

1. Project
2. Epics
3. Features
4. User Stories
5. Test Cases
6. Bugs
7. Work Item Relationships

This ensures parent-child relationships are maintained correctly.

---

# Future Roadmap

* Support multiple LLM providers
* Configurable project sizes (Small, Medium, Large)
* Multiple business domain templates
* Validation of generated artifacts
* Duplicate detection
* Coverage gap generation
* Azure DevOps Test Plans support
* Synthetic execution history
* RAG-ready document generation
* Web interface (Streamlit or FastAPI)

---

# Acknowledgements

This project is inspired by real-world Quality Engineering workflows and aims to simplify the creation of realistic Azure DevOps datasets for AI, RAG, and software testing research.
