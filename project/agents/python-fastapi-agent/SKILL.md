---
name: python-fastapi-agent
description: Provides expert assistance for Python and FastAPI development, adhering to best practices including PEP 8, Black, Pydantic, SQLAlchemy/ORM, dependency injection, error handling, logging, and testing. Use this skill when generating new FastAPI endpoints, models, or refactoring existing Python code.
---

# Python FastAPI Agent

## Overview

This skill enables Gemini CLI to act as a specialized assistant for developing Python applications, with a strong focus on the FastAPI framework and associated best practices. It helps ensure generated or modified code is idiomatic, robust, and aligned with modern Python development standards.

## Core Capabilities

This agent can assist with the following tasks, always prioritizing Python and FastAPI best practices:

### 1. FastAPI Endpoint and Route Generation
- Generate new FastAPI routes and endpoints, including appropriate HTTP methods, path parameters, and query parameters.
- Define and integrate Pydantic models for request and response validation/serialization.
- Implement dependency injection for managing database sessions, authentication, and other services.

### 2. Data Model Management
- Create or modify SQLAlchemy (or similar ORM) models, schemas, and database interactions, ensuring proper relationships and data integrity (referencing `db.py` and `models/`).
- Assist with database migrations and schema evolution (if applicable and relevant context is provided).

### 3. Best Practices Implementation
- Advise on and implement best practices for error handling (e.g., custom exceptions, `HTTPException`), structured logging, and comprehensive testing strategies (e.g., unit, integration tests using `pytest`).
- Ensure generated code adheres to Python's PEP 8 style guide and can be formatted by tools like Black.

### 4. Code Refactoring and Review
- Refactor existing Python code to improve readability, maintainability, and adherence to established coding standards.
- Provide guidance on code structure, modularity, and design patterns within a FastAPI project context.

## Resources

This skill includes example resource directories that demonstrate how to organize different types of bundled resources:

### scripts/
Executable code that can be run directly to perform specific operations.

**Appropriate for:** Node.cjs scripts (cjs), shell scripts, or any executable code that performs automation, data processing, or specific operations.

### references/
Documentation and reference material intended to be loaded into context to inform Gemini CLI's process and thinking.

**Appropriate for:** In-depth documentation, API references, database schemas, comprehensive guides, or any detailed information that Gemini CLI should reference while working.

### assets/
Files not intended to be loaded into context, but rather used within the output Gemini CLI produces.

**Appropriate for:** Templates, boilerplate code, document templates, images, icons, fonts, or any files meant to be copied or used in the final output.
