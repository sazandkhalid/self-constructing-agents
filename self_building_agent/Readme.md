## Architecture

User Task
   ↓
Task Planner / Decomposer
   ↓
Execution Engine (Agent Core)
   ↓
Skill Library + Tool Registry
   ↓
Skill/Tool Generator (Self-Improvement Loop), Self- model update, and skill pruning
   ↓
Memory System (stores everything)

## Risks and Mitigation 

 - The model may hallucinate and generate a skill that does not work
   - Can be Improved by using test cases.
 - Creating variatons of the same skills, thus using more memory.
   - Comparing new skills vs old ones, and creating a tool to identify similarities.
 - Skills not being reused. 
   - Creating a semantic vector search.