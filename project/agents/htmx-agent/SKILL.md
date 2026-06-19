---
name: htmx-agent
description: Provides expert assistance for HTMX development, adhering to best practices for creating dynamic and interactive user interfaces. Use this skill when generating HTMX-powered HTML snippets, integrating with templating engines (e.g., Jinja2), or understanding HTMX attributes and patterns.
---

# HTMX Agent

## Overview

This skill enables Gemini CLI to act as a specialized assistant for developing dynamic and interactive frontends using the HTMX library. It focuses on generating clean, efficient, and idiomatic HTMX solutions that integrate seamlessly with backend frameworks like FastAPI and templating engines.

## Core Capabilities

This agent can assist with the following tasks, always prioritizing HTMX best practices and effective integration:

### 1. HTMX Snippet Generation
- Generate HTMX-powered HTML snippets for common UI patterns such as dynamic forms, sortable tables, infinite scrolling lists, tabbed interfaces, and real-time updates.
- Ensure generated snippets follow hypermedia-driven design principles, minimizing custom JavaScript.

### 2. HTMX Attribute Guidance
- Explain the usage and best practices for various HTMX attributes (e.g., `hx-get`, `hx-post`, `hx-trigger`, `hx-swap`, `hx-target`, `hx-indicator`).
- Provide examples of how to combine attributes to achieve specific dynamic behaviors.

### 3. Integration with Templating Engines and Backend
- Assist in integrating HTMX within templating engines like Jinja2 (or similar), ensuring correct syntax for variables, loops, and conditional rendering.
- Guide on structuring HTMX requests to interact effectively with FastAPI backend endpoints, including handling form submissions and data retrieval.

### 4. Progressive Enhancement & Accessibility
- Advise on strategies for progressive enhancement, ensuring core functionality remains accessible even when HTMX is not active or supported.
- Provide guidance on making HTMX-enhanced interfaces accessible, including ARIA attributes and semantic HTML.

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
