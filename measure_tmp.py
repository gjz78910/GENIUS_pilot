import sys, time
from src.optimization.matching import assign_jobs
from src.optimization.routing import find_optimal_route
import tests.performance.test_scalability as ts

tm = ts._create_travel_matrix(30, min_travel=0.1, max_travel=0.5)
eng = ts._create_engineers(25, 30, working_hours=8.0, skill_variety="mixed")
jobs = ts._create_jobs(250, 30, length_range=(0.5,1.5), skills_per_job=(1,2))
assignments, unassigned = assign_jobs(eng, jobs, tm)
for e in eng:
    aj = assignments.get(e.id, [])
    if not aj:
        continue
    locs = [j.location for j in aj]
    print(f"eng {e.id}: {len(locs)} jobs, distinct={sorted(set(locs))}", flush=True)
    find_optimal_route(e.location, locs, tm)
    print(f"  done {e.id}", flush=True)
print("ALL done")
