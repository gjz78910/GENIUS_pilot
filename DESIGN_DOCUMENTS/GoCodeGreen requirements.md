**GENIUS Experiment Series 1 Data Requirements**

Data capture table:

|  | **Manual** | **Hybrid** | **GenAI-assisted** |
| --- | --- | --- | --- |
| **Personnel** | (e.g. internal, external / architects, developers, testers) |  |  |
| **Compute** | (e.g. development servers, memory per development, serverless) |  |  |
| **Network** | (e.g. average dev/test hits per minute, average network packet size) |  |  |
| **Engineering Factors** | (e.g. main programming language, SSE rating, DevOps maturity) |  |  |
| **Travel** | (e.g. employee commute, business travel / flights) |  |  |

Success criteria table:

|  | **Manual** | **Hybrid** | **GenAI-assisted** |
| --- | --- | --- | --- |
| **Efficiency** | (e.g. measurable reduction in time taken / effort / cost / ranking for meaningful comparison) |  |  |
| **Quality** | (e.g. defect rates, maintainability) |  |  |
| **Scalability** | (e.g. repeatability across use cases and teams) |  |  |
| **Sustainability** | (e.g. energy use, compute cycles, emissions) |  |  |
| **Governance** | (e.g. controls, security, ethical boundaries) |  |  |



| Environmental Impact Measurement : MANUAL |  |  |  |  |  |  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  |  |  |  | Notes: |
| GENERAL PROGRAMME INFORMATION |  |  |  |  |  |  |  |  |  |  | Sections should be completed based on whether an associated application is being developed alongside the AI model. |
|  |  |  |  |  |  |  |  |  |  |  | For training, decision points should reflect if the model is pre-trained and whether reserved compute is needed. |
| PROGRAMME NAME |  |  |  |  |  |  |  |  |  |  | The data input fields should be entered to reflect the scope and scale of the AI solution, avoid double counting. |
| EXPECTED DURATION (MONTHS) |  |  |  |  |  |  |  |  |  |  | The data input allows for standard development for an application alongside model development if used correctly. |
| WORKING HOURS PER DAY |  |  |  |  |  |  |  |  |  |  | For model training the level of serverless is generally LOW an linked to peripheral services e.g. batch management processes, the calculation will be based on the total compute with a serverless apportionment. |
| MODEL TYPE |  |  |  |  |  |  |  |  |  |  | If compute is not reserved then calculation will assume that resources are reallocated when not being used. |
| AVERAGE TRAINING HOURS PER MONTH |  |  |  |  |  |  |  |  |  |  |  |
| VOLUMETRIC: # CUSTOMERS |  |  |  |  |  |  |  |  |  |  |  |
| VOLUMETRIC: # TRANSACTIONS PROCESSED ANNUALLY |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |
| CATEGORY | Example Response | DATA INPUT |  |  |  |  |  |  |  |  |  |
| LOCATION | UK | UK | Europe | Middle East | Africa | India | Asia | Australia | North America & Canada | Latin America |  |
| PERSONNEL - Employees (FTE) |  |  |  |  |  |  |  |  |  |  |  |
| Programme & Project Management Roles (incl. Product, RTE and Scrum Masters) | 5 |  |  |  |  |  |  |  |  |  |  |
| Architecture | 1 |  |  |  |  |  |  |  |  |  |  |
| Developer & Engineering (incl. AI) | 25 |  |  |  |  |  |  |  |  |  |  |
| Tester | 10 |  |  |  |  |  |  |  |  |  |  |
| Analyst | 5 |  |  |  |  |  |  |  |  |  |  |
| Data Scientist/ Data Analyst | 4 |  |  |  |  |  |  |  |  |  |  |
| Infrastructure | 3 |  |  |  |  |  |  |  |  |  |  |
| Support & SRE | 2 |  |  |  |  |  |  |  |  |  |  |
| Other | 2 |  |  |  |  |  |  |  |  |  |  |
| PERSONNEL - Subcontract / Third Party (FTE) |  |  |  |  |  |  |  |  |  |  |  |
| Programme & Project Management Roles (incl. Product, RTE and Scrum Masters) | 5 |  |  |  |  |  |  |  |  |  |  |
| Architecture | 1 |  |  |  |  |  |  |  |  |  |  |
| Developer & Engineering (incl. AI) | 2 |  |  |  |  |  |  |  |  |  |  |
| Tester | 10 |  |  |  |  |  |  |  |  |  |  |
| Analyst | 5 |  |  |  |  |  |  |  |  |  |  |
| Data Scientist / Data Analyst | 4 |  |  |  |  |  |  |  |  |  |  |
| Infrastructure | 3 |  |  |  |  |  |  |  |  |  |  |
| Support & SRE | 2 |  |  |  |  |  |  |  |  |  |  |
| Other | 2 |  |  |  |  |  |  |  |  |  |  |
| TECHNOLOGY - DEVELOPMENT and TEST: Compute |  |  |  |  |  |  |  |  |  |  |  |
| On-Premise Data Centre |  |  |  |  |  |  |  |  |  |  |  |
| Number of Development Servers | 1 |  |  |  |  |  |  |  |  |  |  |
| Do you use GPU in Development? | No |  |  |  |  |  |  |  |  |  |  |
| Number of Development CPU/GPU per Server | 2 |  |  |  |  |  |  |  |  |  |  |
| Memory (GB) per Development CPU/GPU | 40 |  |  |  |  |  |  |  |  |  |  |
| Development Data Storage (TB) | 100 |  |  |  |  |  |  |  |  |  |  |
| Number of Test Servers | 1 |  |  |  |  |  |  |  |  |  |  |
| Do you use GPU in Test? | No |  |  |  |  |  |  |  |  |  |  |
| Number of Test CPU/GPU per Server | 2 |  |  |  |  |  |  |  |  |  |  |
| Memory (GB) per Test CPU/GPU | 80 |  |  |  |  |  |  |  |  |  |  |
| Test Data Storage (TB) | 100 |  |  |  |  |  |  |  |  |  |  |
| Number of Model Training Servers | 45 |  |  |  |  |  |  |  |  |  |  |
| Do you use GPU in Model Training? | Yes |  |  |  |  |  |  |  |  |  |  |
| Number of Model Training CPU/GPU per server | 2 |  |  |  |  |  |  |  |  |  |  |
| Memory (GB) per Model Training CPU/GPU | 80 |  |  |  |  |  |  |  |  |  |  |
| Model Training Data Storage (TB) | 500 |  |  |  |  |  |  |  |  |  |  |
| Public Cloud |  |  |  |  |  |  |  |  |  |  |  |
| Public Cloud Provider | AWS |  |  |  |  |  |  |  |  |  |  |
| Are you using Serverless Compute in Development? | No |  |  |  |  |  |  |  |  |  |  |
| Name the Instance / Machine Type provisioned | M Family |  |  |  |  |  |  |  |  |  |  |
| Number of Development vCPU provisioned | 2 |  |  |  |  |  |  |  |  |  |  |
| IF Serverless, Average Number of Compute Hours per Day | 6 |  |  |  |  |  |  |  |  |  |  |
| Memory (GB) per vCPU | 4 |  |  |  |  |  |  |  |  |  |  |
| Development Data Storage (TB) | 50 |  |  |  |  |  |  |  |  |  |  |
| Are you using Serverless Compute in Test? | No |  |  |  |  |  |  |  |  |  |  |
| Name the Instance / Machine Type provisioned | M Family |  |  |  |  |  |  |  |  |  |  |
| Number of Test vCPU provisioned | 2 |  |  |  |  |  |  |  |  |  |  |
| IF Serverless, Average Number of Compute Hours per Day | 6 |  |  |  |  |  |  |  |  |  |  |
| Memory (GB) per vCPU | 4 |  |  |  |  |  |  |  |  |  |  |
| Test Data Storage (TB) | 50 |  |  |  |  |  |  |  |  |  |  |
| Do you use Reserved Compute for Model Training? | Yes |  |  |  |  |  |  |  |  |  |  |
| Are you using Serverless Compute in Model Training? | No |  |  |  |  |  |  |  |  |  |  |
| Name the Instance / Machine Type provisioned | M Family |  |  |  |  |  |  |  |  |  |  |
| IF Serverless, Average Number of Compute Hours per Day | 3 |  |  |  |  |  |  |  |  |  |  |
| Number of Development GPU provisioned | 200 |  |  |  |  |  |  |  |  |  |  |
| Memory (GB) per Model Training GPU | 40 |  |  |  |  |  |  |  |  |  |  |
| Model Training Data Storage (TB) | 200 |  |  |  |  |  |  |  |  |  |  |
| TECHNOLOGY - DEVELOPMENT and TEST: Network |  |  |  |  |  |  |  |  |  |  |  |
| Average Dev/Test Hits per Minute | 5 |  |  |  |  |  |  |  |  |  |  |
| Average Network Packet Size (KB) | 5 |  |  |  |  |  |  |  |  |  |  |
| TECHNOLOGY - Engineering Factors |  |  |  |  |  |  |  |  |  |  |  |
| Main Programming Language | Java |  |  |  |  |  |  |  |  |  |  |
| SSE Rating Above Very Good? Yes or No | No |  |  |  |  |  |  |  |  |  |  |
| DevOps Maturity Above 4? (Managed/Optimised) - Yes or No | Yes |  |  |  |  |  |  |  |  |  |  |
| MLOps Maturity Above 4? (Reliable/Scalable) - Yes or No | Yes |  |  |  |  |  |  |  |  |  |  |
| TRAVEL - Business Travel |  |  |  |  |  |  |  |  |  |  |  |
| Estimated Short Haul Flights per month | 1 |  |  |  |  |  |  |  |  |  |  |
| Estimated Long Haul Flights per month | 1 |  |  |  |  |  |  |  |  |  |  |
| Estimated # of Bus Trips per month |  |  |  |  |  |  |  |  |  |  |  |
| Estimated # of Train Trips per month | 3 |  |  |  |  |  |  |  |  |  |  |
| Estimated # of Car Trips per month |  |  |  |  |  |  |  |  |  |  |  |
| Estimated # Hotel Nights per month | 4 |  |  |  |  |  |  |  |  |  |  |
| TRAVEL - Employee Commute |  |  |  |  |  |  |  |  |  |  |  |
| Average # of Bus Trips per employee per day | 2 |  |  |  |  |  |  |  |  |  |  |
| Average # of Train Trips per employee per day |  |  |  |  |  |  |  |  |  |  |  |
| Average # of Car Trips per employee per day |  |  |  |  |  |  |  |  |  |  |  |