"""
Feature Validation Tests Package

This directory contains auto-generated feature validation tests created by
the testing-expert agent during the pre-commit workflow.

## Purpose
Validation tests verify that implemented features meet requirements BEFORE commit.
They are ephemeral and may be deleted after successful commit.

## Workflow
1. Developer stages changes for commit
2. testing-expert agent detects feature context from git diff
3. Agent generates validation tests in this directory
4. Tests are executed to verify feature works
5. If tests pass, commit is approved
6. Validation test files may be deleted or committed

## File Naming Convention
test_feature_{jira_ticket}_{timestamp}.py

Example:
- test_feature_DA1_123_20251218_1430.py
- test_feature_web_search_20251218_1500.py

## Test Structure
Each validation test file follows this structure:
- TestFeatureValidation_{feature_name} class
- test_feature_happy_path - Primary use case
- test_feature_edge_cases - Edge case handling
- test_feature_error_handling - Error conditions
- test_feature_integration - Component integration
"""
