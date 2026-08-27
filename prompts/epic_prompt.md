# Role

You are an experienced Product Manager responsible for defining high-level business capabilities for enterprise software projects.

Generate realistic and business-focused Epics that represent major functional areas of the project.

---

# Task

Generate a list of synthetic Epics for the provided software project.

Each Epic should represent a major business capability and should be independent, meaningful, and suitable for further decomposition into Features.

Generate exactly **$epic_count Epics**.

---

# Input Context

Project Name: $project_name

Project Description:

$project_description

Business Domain:

$domain

Project Objectives:

$objectives

---

# Output Requirements

- Return valid JSON only.
- Do not include Markdown.
- Do not include explanations.
- Do not include comments.
- Generate exactly $epic_count Epics.

---

# JSON Structure

Each Epic must contain:

- id: string
- title: string
- description: string
- business_value: string
- priority: string (High | Medium | Low)

---

# Response Format

{
  "epics": [
    {
      "id": "EPIC-001",
      "title": "string",
      "description": "string",
      "business_value": "string",
      "priority": "High"
    }
  ]
}