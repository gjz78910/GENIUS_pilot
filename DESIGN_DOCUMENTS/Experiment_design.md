# Experiment

This study explores how developers interact with AI-powered coding assistants in industry inspired programming scenarios. By observing and comparing how participants approach manual coding tasks and tasks using an AI enabled coding assistant, we aim to understand how such tools influence coding practices, problem-solving approaches, and overall developer productivity and sustainability of both the produced software and development process.

## Methodology

This study is designed as a full-day observational experiment to explore how developers interact with AI-powered coding assistants, specifically the "Q Developer" tool, in a Python programming context. The study uses a mixed-methods approach, integrating both quantitative and qualitative data to provide a comprehensive understanding of developer behaviour and experience, along with exploring the sustainability of the process and developed software.

## Participants

Participants will be recruited from three distinct groups:

- Developers from BT
- University students with relevant programming experience
- Developers from DiffBlue (subject to availability)

All participants must meet a predefined baseline of Python proficiency to ensure consistency in task execution and data quality. Each participant will work individually to eliminate group dynamics and focus on personal interaction with the AI assistant. An initial short training session of using AI coding assistants will be provided if necessary to ensure participants fully understand how to extract the benefit from the AI coding assistant.

Each participant will complete all tasks. Participants will complete some of their tasks without AI assistance and some will be completed with the AI coding assistant available.

## Pilot Study

Prior to the main experiment, a pilot study will be conducted to refine the research design and ensure the robustness of the methodology. The pilot will involve a small number of participants of the GENIUS UK consortium and will be used to:

**Validate the experimental setup:** This includes testing the technical environment (IDE, Git, AI plugin, CI/CD pipeline, virtual environment, and screen recording tools) to ensure smooth operation and usability.

**Refine data collection instruments:** Insights from the pilot will inform the development of post-task surveys and semi-structured interview questions, ensuring they are relevant, clear, and capable of capturing meaningful data.

**Identify usability and methodological issues:** The pilot will help uncover any practical or procedural challenges, such as unclear task instructions, technical glitches, or participant confusion, allowing for adjustments before the full study rollout.

Findings from the pilot will be documented and used to optimize the main study protocol, improving both the reliability and validity of the research outcomes.

## Experimental Setup

To ensure consistency and control across all sessions, each participant will be provided with a fully standardized and isolated development environment tailored for Python development. This setup is designed to closely mirror industry-standard tooling and workflows, ensuring that participants engage with technologies and practices that reflect real-world development contexts. This environment will be pre-configured with all necessary tools and resources to support the use of the Q Developer AI assistant and facilitate smooth task execution.

The setup will include:

- **Python IDE:** A modern integrated development environment configured with relevant extensions to support Python and AI assistant integration. For the experiment Visual Studio Code will be used.
- **Access to a pre-existing codebase:** Participants will be provided with a realistic, appropriately complex given the timescales, codebase to work from. This will ensure tasks are grounded in practical development scenarios. This initial codebase will serve as the starting point for the assigned tasks and will include unit tests to support development and validation.
- **Existing documentation and requirements:** we will provide a set of requirements that forms the basis of the provided codebase.
- **Test Suites:** Three test suites will be provided. The first is a set of unit-tests that gives participants a baseline for correctness against the existing project. For the tasks, they should write the tests themselves. The second set of tests is not directly provided to participants and helps measure the performance of the solution to the tasks. A third set of tests will check for correctness.
- **Git version control:** Participants will have access to a GitLab based Git repository to manage code changes. The main branch will be protected and participants will create a feature branch. This will be isolated from other participants.
- **Q Developer AI plugin:** The AI assistant will be installed and configured to ensure consistent functionality across all sessions. All functionalities including in-line code completion, chat and agentic coding with be enabled and available to participants.
- **CI/CD pipeline configuration:** A basic continuous integration and deployment setup will be included to reflect industry development environments and allow participants to test and deploy code. As part of the CI/CD pipeline, a set of performance tests will also be included to measure the effectiveness of a participant's solution.
- **Python virtual environment (venv):** Each participant will work within a clean virtual environment to manage dependencies and avoid conflicts.
- **Screen recording software:** All sessions will be recorded to capture participant interactions, coding behaviour, and use of the AI assistant.

Each participant's environment will be spun up independently to ensure isolation, reproducibility, and the ability to reset or reconfigure as needed. This approach minimizes variability and supports robust data collection and analysis.

Equipment for the experiment will be provided to participants, configured with the required software and environment as previously described.

## Procedure

### Task Execution

Participants will be asked to complete a series of programming tasks, detailed below, using the Q Developer AI assistant. These tasks will be based on a specially crafted and representative codebase and designed to reflect realistic development scenarios, such as code optimisation, feature implementation, and architectural refactoring. Each task will be clearly defined with objectives and expected outcomes. Participants will work independently, and their interactions with the AI assistant will be unobtrusively recorded using screen capture and system logging tools. This will allow researchers to observe natural usage patterns without interfering with the development process.

### Quantitative Data Collection

Quantitative data will be gathered from multiple sources to measure participant performance and interaction with the AI assistant. These metrics are essential for identifying patterns, assessing tool effectiveness, comparing participant outcomes, and evaluating sustainability impacts.

**Usage metrics:** This includes the frequency and timing of AI assistant queries, the number of suggestions accepted or rejected, and the time spent on each task. These metrics help quantify engagement with the assistant and provide insight into how often and in what contexts developers rely on AI support. Usage metrics will be captured through plugin telemetry, IDE event logs, and timestamped screen recordings.

**Performance indicators:** These include task completion rates, the number of errors introduced or resolved, adherence to unit test requirements, and the performance of solutions to designated software optimisation tasks. For these optimisation tasks, performance will be measured using integration and performance tests embedded in the CI/CD pipeline. This allows for objective assessment of runtime efficiency, resource usage, and scalability of the submitted code. Collecting this data is crucial for evaluating the impact of AI assistance on code quality and developer productivity. Performance indicators will be assessed and collected through automated test results, Git commit analysis, CI/CD pipeline performance logs, and manual review of task outcomes.

**System-level data:** Git commits, CI/CD pipeline activity will be collected to provide a detailed view of development behaviour. This data helps contextualize participant actions and supports the identification of workflow patterns, bottlenecks, and deviations from expected practices. It also enables analysis of resource-intensive operations, helping to assess whether AI assistance leads to more sustainable development practices. System-level data will be extracted from integrated logging tools, Git repositories, and CI/CD dashboards.

### Qualitative Data Collection

Qualitative insights will be captured through multiple methods to explore the subjective experiences and contextual factors influencing developer interaction with the AI assistant. These insights will complement the quantitative findings and help interpret the broader implications of AI-assisted development, including sustainability.

**Post-task surveys:** Participants will complete structured questionnaires after completing the tasks. These surveys will assess perceptions of the AI assistant's usability, trustworthiness, and impact on productivity amongst other things. Additional questions will explore whether participants felt the assistant helped them work more efficiently or sustainably (e.g., reducing time, effort, or unnecessary computation).

**Semi-structured interviews:** Conducted after initial data analysis, these interviews will delve deeper into participants' reasoning, expectations, and reflections. Interview prompts will be informed by themes emerging from observational and quantitative data, and will include questions about perceived benefits, limitations, and sustainability implications of using AI assistance. Interviews will be audio-recorded and transcribed for thematic analysis.

## Ethical Considerations

Ethical approval will be sought through King's College London (KCL) prior to participant recruitment.

## High Level Scenario Description

The study scenario is situated within the context of a field engineer scheduling tool, which provides a realistic and complex domain for evaluating how developers interact with AI coding assistants. This scheduling problem is highly relevant to BT's industrial context, where efficient allocation of engineering resources across geographic regions and time constraints is a critical operational challenge. The tool includes scheduling logic that assigns jobs to engineers based on factors such as location, timing, and skill requirements. Experiment participants will engage with this codebase to complete tasks that reflect common software engineering challenges.

The tasks are designed to assess how AI assistance influences developer performance, decision-making, and code quality. They include:

- **Task 1 – Optimization of Scheduling / Routing:** Participants will improve suboptimal implementations, including a brute-force Traveling Salesman Problem (TSP) algorithm used to minimize engineer travel time, and a naïve bucket/bin sort algorithm used to match engineers to jobs. The goal is to improve allocation of jobs to engineers for realism and efficiency.
- **Task 2 – Reporting on Engineer Schedules:** Participants will work with a report generation feature that outputs assigned jobs per engineer in CSV format, including timing details and travel information.
- **Task 3 – External Job Data Integration:** Participants will work with logic that loads job data from structured external files (JSON format), replacing hardcoded data and ensuring proper integration with the scheduling system.

These tasks are timeboxed and can be completed manually or with assistance from an AI coding assistant. The scenario and task design aim to simulate real-world development conditions and provide insight into the practical utility and limitations of AI support in software engineering workflows.

For manual task completion, participants are welcome to use any sources of information, such as search engine results, stack overflow, etc, without using any AI assistance in the IDE. Users will be guided not to use AI chatbots such as ChatGPT.

For tasks where users are told they can use the AI assistant, they will have the freedom to complete any which way they can. If they wish to use AI assistances outside the IDE, that is also acceptable.

## Tasks Descriptions for Participants

### Task 1 – Optimization of Scheduling / Routing

**Objective:** Improve the allocation of jobs to engineers for realism and efficiency by optimizing both the routing logic and the job matching algorithm.

**Context:** The current system uses a brute-force approach to solve a Traveling Salesman Problem (TSP) for routing engineers between job locations, and a naïve bucket/bin sort algorithm to match jobs to engineers based on location proximity and skill requirements. Both approaches have limitations in terms of performance and solution quality.

**Instructions:**

1. Review the existing routing function in `src/optimization/routing.py` that minimizes travel time between job locations using brute-force TSP.
2. Review the existing matching algorithm in `src/optimization/matching.py` that assigns jobs to engineers using a bucket/bin sort approach.
3. Identify inefficiencies in both algorithms (e.g., scalability issues, suboptimal solutions).
4. Replace or improve the routing logic using a more efficient approach (e.g., heuristic algorithms, approximation methods).
5. Refactor or redesign the matching algorithm to improve speed and matching precision, considering edge cases such as overlapping skill sets, geographic constraints, and workload balancing.
6. Ensure the updated implementations pass all existing unit tests and integrate cleanly with the scheduling workflow.
7. Validate your changes using the provided test suite, including benchmark tests that measure solution quality against known optimal solutions.

**Metrics:** The solution will be evaluated on correctness (skills, durations, working-hours respected), solution quality vs. benchmark (gap to optimal on toy instances), and performance (runtime and scalability).

### Task 2 – Reporting on Engineer Schedules

**Objective:** Work with and potentially extend the CSV report generation feature that outputs per-engineer schedules with timing details.

**Context:** The system includes a CSV reporting feature that generates per-engineer reports. These reports are used for correctness checks and must adhere to specific requirements.

**Instructions:**

1. Review the existing report generation function in `src/features/report.py`.
2. Understand the current report format and fields (engineer_id, engineer_name, job_id, job_location, job_time, required_skills, timing details, travel_time).
3. Verify that reports meet the output contract: one line per job per engineer with timing details in minutes.
4. Ensure reports pass correctness checks: sequential timing, working-hours window adherence, no missing/duplicate jobs.
5. If needed, extend or modify the reporting functionality to meet additional requirements or improve clarity.
6. Test the report generation using the provided test suite in `tests/test_report_correctness.py`.

**Metrics:** The reports will be validated for correctness (sequential timing, working-hours constraints, no missing/duplicate jobs) and completeness (all required fields present).

### Task 3 – External Job Data Integration

**Objective:** Work with and potentially extend the external data loading mechanism that reads job, engineer, and travel matrix data from structured JSON files.

**Context:** The system includes functionality to load data from external JSON files, replacing hardcoded data. This enables experiment operability with standardized data formats and GitLab repository workflows.

**Instructions:**

1. Review the existing data loader in `src/features/data_loader.py` that loads engineers, jobs, and travel matrix from JSON files.
2. Understand the JSON data format specification (see example files in `data/benchmarks/` or `data/performance/`).
3. Verify that the data loader correctly parses and validates the input data (required fields, location references, duplicate IDs).
4. Ensure the loaded data integrates correctly with the scheduling logic and maintains existing scheduling behaviour.
5. If needed, extend the data loader to support additional data formats, validation rules, or error handling.
6. Test the data loading functionality using the provided test suite in `tests/test_data_loader.py` and with benchmark/performance instance files.

**Metrics:** The data loader will be evaluated on data realism and control (locations, travel times, job durations, capacities) and experiment operability (compatibility with GitLab repos, CI pipelines, standardized setup).

## Provided Codebase Creation

What are the factors we need to consider, especially from a sustainability perspective and what methodology should be followed?

## Survey Questions & Interview Protocol

To be written
