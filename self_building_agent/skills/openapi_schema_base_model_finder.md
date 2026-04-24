---
name: openapi_schema_base_model_finder
tags:
- fastapi
- openapi
- schema
- model
trigger: when needing to identify the base model class for OpenAPI schemas in FastAPI.
type: pattern
version: 1
success_count: 0
fail_count: 0
---
---
# OpenAPI Schema Base Model Finder
## Purpose
To identify the base class used for defining OpenAPI schemas within the FastAPI library.
## When to use
Use this skill when you need to understand the foundational class from which OpenAPI schema models inherit in FastAPI. This is useful for tasks related to schema generation, validation, or custom schema definition.
## How to use
1. Navigate to the `fastapi/openapi/models.py` file in the FastAPI repository.
2. Examine the class definitions to find the primary class designated for OpenAPI schema representation.
3. Identify the class that other schema models inherit from. In FastAPI, this is `OpenAPIV3Schema`.