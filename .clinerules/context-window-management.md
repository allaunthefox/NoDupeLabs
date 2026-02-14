## Brief overview
This rule file contains guidelines for managing context window usage during development sessions, specifically for the NoDupeLabs project.

## Context window management
- When context window reaches 150,000 TOKEN_REMOVEDs, use the /compact command to condense the conversation
- Use context window management proactively to maintain optimal performance
- Prefer concise communication when context window is approaching limits

## Development workflow
- Focus on completing specific phases or tasks before considering context compaction
- Use integration testing patterns similar to those implemented in Phase 7
- Maintain pytest test framework for all new test development

## Project context
- NoDupeLabs project uses Python with pytest for testing
- Plugin system architecture with SimilarityCommandPlugin pattern
- Import resolution follows Python module structure conventions
- Error recovery and security testing are critical components

## Communication style
- Direct and technical communication preferred
- Clear status updates on task completion
- Reference specific file names and test results when reporting progress

## Task continuation
- When context compaction occurs, capture the current step and pending tasks
- Include specific details about what was being worked on and what needs to be done next
- Reference the exact task progress and next steps to ensure seamless continuation
