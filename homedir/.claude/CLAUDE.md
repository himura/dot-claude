# Communication Guidelines

**Ask for clarification when unclear**: When requirements are ambiguous or unclear points arise during implementation, ask questions rather than proceeding with assumptions. This prevents generating unwanted output that will be discarded.

**Ask one question at a time**: This minimizes user effort - users can answer directly without specifying which question they're responding to. List multiple options only when it helps show the full picture (e.g., independent simple confirmations, mutually exclusive choices).

**Wait for user response**: Don't proceed with speculative work while questions are outstanding.

# Development Workflow

## Commit Policy

Commit with appropriate granularity:
- Each commit must compile and pass tests
- Commit message clearly conveys intent
- Commit when a logical unit is complete

**Workflow**:
1. Make focused changes to related code
2. Run tests for the changed area
3. If tests pass, commit immediately
4. Move to next change

## Testing Strategy

After making changes, run tests at appropriate scope:
- Changed a package? Test that package
- Changed multiple packages? Test all packages
- Unsure? Run all tests

**Example**: After editing core library code, run the core package tests before committing.
