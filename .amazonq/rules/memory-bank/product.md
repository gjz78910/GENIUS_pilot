# Product Overview

## Project Purpose

GENIUS (genIUS) is a Python-based scheduling system designed for field service operations. It automates the assignment of field engineers to jobs and optimizes their travel routes to minimize time and distance.

## Value Proposition

- **Automated Job Assignment**: Eliminates manual scheduling by automatically matching engineers to jobs based on skills and proximity
- **Route Optimization**: Reduces travel time and costs through intelligent route planning using TSP (Travelling Salesperson Problem) algorithms
- **Skill-Based Matching**: Ensures only qualified engineers are assigned to jobs requiring specific technical skills
- **Location-Aware Scheduling**: Prioritizes nearby engineers to minimize travel distance

## Key Features

### 1. Intelligent Job Assignment
- Matches engineers to jobs based on required skills
- Considers engineer location and proximity to job sites
- Validates skill requirements before assignment
- Handles multiple jobs per engineer

### 2. Route Optimization
- Calculates optimal travel routes using brute-force TSP algorithm
- Minimizes total travel distance across all assigned jobs
- Uses predefined travel distance matrices
- Suitable for small to medium job sets

### 3. Skill Management
- Case-insensitive skill matching
- Support for multiple skills per engineer
- Multiple skill requirements per job
- Automatic skill validation

## Target Users

### Primary Users
- **Field Service Managers**: Schedule and coordinate field engineer assignments
- **Operations Teams**: Optimize resource allocation and route planning
- **Dispatchers**: Assign jobs efficiently based on real-time availability

### Secondary Users
- **Experiment Participants**: Researchers studying AI-assisted development workflows
- **Developers**: Extending the system with new features (reporting, data loading)

## Use Cases

### Operational Use Cases
1. **Daily Job Scheduling**: Assign morning jobs to available engineers based on skills and location
2. **Emergency Dispatch**: Quickly find the nearest qualified engineer for urgent repairs
3. **Route Planning**: Optimize multi-stop routes for engineers with multiple assignments
4. **Workload Balancing**: Distribute jobs evenly across the engineering team

### Experimental Use Cases
1. **Code Comprehension Studies**: Participants read and understand the scheduling logic
2. **Feature Extension Tasks**: Implement stub features like reporting and data loading
3. **Algorithm Enhancement**: Extend matching logic with workload balancing or time constraints
4. **AI-Assisted Development**: Compare development workflows with and without AI tools

## Sample Scenario

**Input:**
- 4 engineers (Alice, Bob, Charlie, Daisy) at locations A, B, C, D
- 5 jobs requiring various skills (repair, install, maintain)
- Travel distance matrix between all locations

**Output:**
- Job assignments: Each job assigned to the closest qualified engineer
- Optimized routes: Shortest path for each engineer to complete their assigned jobs
- Total travel distance: Minimized across all engineers

## Technical Constraints

- No external dependencies (Python standard library only)
- Brute-force TSP suitable for small job sets only (< 10 jobs per engineer)
- Requires complete travel matrix with all location pairs defined
- Python 3.8+ required
