#!/usr/bin/env python3
"""Fill GoCodeGreen template with collected experiment data.

This script maps collected experiment data to the GoCodeGreen requirements format.
"""

import csv
import json
import sys
from datetime import datetime
from pathlib import Path


def load_aggregated_data(data_file):
    """Load aggregated experiment data.
    
    Args:
        data_file: Path to aggregated data JSON file
    
    Returns:
        Dictionary with aggregated data
    """
    with open(data_file, "r") as f:
        return json.load(f)


def map_to_gocodegreen_format(aggregated_data, session_type="manual"):
    """Map aggregated data to GoCodeGreen format.
    
    Args:
        aggregated_data: Aggregated experiment data
        session_type: "manual" or "ai-assisted"
    
    Returns:
        Dictionary with GoCodeGreen formatted data
    """
    data = aggregated_data.get("data", {})
    
    gcg_data = {
        "programme_name": "GENIUS Pilot Experiment",
        "session_type": session_type,
        "participant_id": aggregated_data.get("participant_id"),
        "session_id": aggregated_data.get("session_id"),
        "timestamp": datetime.now().isoformat(),
    }
    
    # General Programme Information
    if "task_timing" in data:
        timing = data["task_timing"]
        total_seconds = timing.get("experiment_info", {}).get("total_duration_seconds", 0)
        total_hours = total_seconds / 3600.0
        gcg_data["expected_duration_months"] = None  # Single session
        gcg_data["working_hours_per_day"] = total_hours
    else:
        gcg_data["working_hours_per_day"] = None
    
    gcg_data["model_type"] = "N/A"  # Not training models
    gcg_data["average_training_hours_per_month"] = None
    gcg_data["volumetric_customers"] = None
    gcg_data["volumetric_transactions"] = None
    
    # Location
    # Try to get from system info or use default
    location = "UK"  # Default
    if "system_info" in data:
        # Could extract from system info if available
        pass
    gcg_data["location"] = location
    
    # Personnel - Employees (FTE)
    # For pilot: 1 developer per participant
    gcg_data["personnel_employees"] = {
        "programme_management": 0,
        "architecture": 0,
        "developer_engineering": 1,  # 1 participant = 1 FTE
        "tester": 0,
        "analyst": 0,
        "data_scientist": 0,
        "infrastructure": 0,
        "support_sre": 0,
        "other": 0,
    }
    
    # Personnel - Subcontract (FTE)
    gcg_data["personnel_subcontract"] = {
        "programme_management": 0,
        "architecture": 0,
        "developer_engineering": 0,
        "tester": 0,
        "analyst": 0,
        "data_scientist": 0,
        "infrastructure": 0,
        "support_sre": 0,
        "other": 0,
    }
    
    # Technology - Development and Test: Compute
    if "system_info" in data:
        sys_info = data["system_info"]
        cpu = sys_info.get("cpu", {})
        memory = sys_info.get("memory", {})
        gpu = sys_info.get("gpu", {})
        
        gcg_data["compute"] = {
            "on_premise": {
                "dev_servers": 0,  # Using participant laptop
                "dev_gpu": "No",
                "dev_cpu_per_server": cpu.get("cores_logical", 2),
                "dev_memory_gb_per_cpu": round(memory.get("total_gb", 8) / max(cpu.get("cores_logical", 1), 1), 1),
                "dev_storage_tb": 0.001,  # Small codebase
                "test_servers": 0,
                "test_gpu": "No",
                "test_cpu_per_server": cpu.get("cores_logical", 2),
                "test_memory_gb_per_cpu": round(memory.get("total_gb", 8) / max(cpu.get("cores_logical", 1), 1), 1),
                "test_storage_tb": 0.001,
            },
            "public_cloud": {
                "provider": "AWS",  # GitLab CI/CD
                "dev_serverless": "No",
                "dev_instance_type": "N/A",
                "dev_vcpu": None,
                "dev_serverless_hours_per_day": None,
                "dev_memory_gb_per_vcpu": None,
                "dev_storage_tb": 0.001,
                "test_serverless": "No",
                "test_instance_type": "N/A",
                "test_vcpu": None,
                "test_serverless_hours_per_day": None,
                "test_memory_gb_per_vcpu": None,
                "test_storage_tb": 0.001,
            },
            "model_training": {
                "servers": 0,
                "gpu": "No",
                "cpu_per_server": None,
                "memory_gb_per_cpu": None,
                "storage_tb": None,
                "reserved_compute": "No",
                "serverless": "No",
                "instance_type": None,
                "serverless_hours_per_day": None,
                "gpu_count": None,
                "gpu_memory_gb": None,
                "storage_tb": None,
            },
        }
    else:
        # Default values
        gcg_data["compute"] = {
            "on_premise": {
                "dev_servers": 0,
                "dev_gpu": "No",
                "dev_cpu_per_server": 2,
                "dev_memory_gb_per_cpu": 4,
                "dev_storage_tb": 0.001,
            },
            "public_cloud": {
                "provider": "AWS",
            },
            "model_training": {
                "servers": 0,
                "gpu": "No",
            },
        }
    
    # Technology - Network
    if "resource_usage" in data:
        # Calculate average network metrics from resource monitoring
        resource_data = data["resource_usage"]
        if isinstance(resource_data, list) and len(resource_data) > 0:
            # Calculate average bytes per minute
            total_bytes_sent = sum(
                s.get("network", {}).get("bytes_sent_per_min", 0) for s in resource_data
            )
            total_bytes_recv = sum(
                s.get("network", {}).get("bytes_recv_per_min", 0) for s in resource_data
            )
            avg_bytes_per_min = (total_bytes_sent + total_bytes_recv) / len(resource_data) if resource_data else 0
            
            # Estimate hits per minute (rough approximation)
            hits_per_min = max(1, int(avg_bytes_per_min / 1024 / 5))  # Assume ~5KB per hit
            packet_size_kb = max(1, round(avg_bytes_per_min / 1024 / hits_per_min, 1)) if hits_per_min > 0 else 5
            
            gcg_data["network"] = {
                "avg_dev_test_hits_per_min": hits_per_min,
                "avg_network_packet_size_kb": packet_size_kb,
            }
        else:
            gcg_data["network"] = {
                "avg_dev_test_hits_per_min": None,
                "avg_network_packet_size_kb": None,
            }
    else:
        gcg_data["network"] = {
            "avg_dev_test_hits_per_min": None,
            "avg_network_packet_size_kb": None,
        }
    
    # Technology - Engineering Factors
    survey = data.get("survey", {})
    devops_val = survey.get("devops_maturity")
    mlops_val = survey.get("mlops_maturity")
    gcg_data["engineering_factors"] = {
        "main_programming_language": survey.get("main_language", "Python"),
        "sse_rating_above_very_good": "Yes" if survey.get("sse_completed") == "yes" else "No",
        "devops_maturity_above_4": "Yes" if devops_val and int(devops_val) >= 4 else "No",
        "mlops_maturity_above_4": "Yes" if mlops_val and int(mlops_val) >= 4 else "N/A",
    }

    # Travel - Business Travel
    gcg_data["travel_business"] = {
        "short_haul_flights_per_month": 0,
        "long_haul_flights_per_month": 0,
        "bus_trips_per_month": 0,
        "train_trips_per_month": 0,
        "car_trips_per_month": 0,
        "hotel_nights_per_month": 0,
    }

    # Travel - Employee Commute (from pre-experiment survey)
    def _to_float(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    gcg_data["travel_commute"] = {
        "avg_bus_trips_per_employee_per_day": _to_float(survey.get("bus_trips_per_day")),
        "avg_train_trips_per_employee_per_day": _to_float(survey.get("train_trips_per_day")),
        "avg_car_trips_per_employee_per_day": _to_float(survey.get("car_trips_per_day")),
    }
    
    # Sustainability metrics
    if "energy_estimate" in data:
        energy = data["energy_estimate"]
        gcg_data["sustainability"] = {
            "total_energy_kwh": energy.get("total_energy", {}).get("kwh"),
            "energy_breakdown": energy.get("energy_breakdown", {}),
        }
    else:
        gcg_data["sustainability"] = {}
    
    if "carbon_footprint" in data:
        carbon = data["carbon_footprint"]
        gcg_data["sustainability"]["total_emissions_kg_co2"] = carbon.get("total", {}).get("emissions_kg_co2")
        gcg_data["sustainability"]["compute_cycles"] = carbon.get("compute", {}).get("estimated_cycles")
    
    return gcg_data


def generate_csv_output(gcg_data, output_file):
    """Generate CSV output matching GoCodeGreen format.
    
    Args:
        gcg_data: GoCodeGreen formatted data
        output_file: Output CSV file path
    """
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        
        # Write header
        writer.writerow(["Category", "Field", "Value", "Session Type"])
        
        # General Programme Information
        writer.writerow(["GENERAL", "PROGRAMME NAME", gcg_data["programme_name"], gcg_data["session_type"]])
        writer.writerow(["GENERAL", "EXPECTED DURATION (MONTHS)", gcg_data.get("expected_duration_months", "N/A"), gcg_data["session_type"]])
        writer.writerow(["GENERAL", "WORKING HOURS PER DAY", gcg_data.get("working_hours_per_day"), gcg_data["session_type"]])
        writer.writerow(["GENERAL", "MODEL TYPE", gcg_data.get("model_type"), gcg_data["session_type"]])
        
        # Location
        writer.writerow(["LOCATION", "LOCATION", gcg_data.get("location"), gcg_data["session_type"]])
        
        # Personnel - Employees
        personnel = gcg_data.get("personnel_employees", {})
        writer.writerow(["PERSONNEL", "Developer & Engineering (FTE)", personnel.get("developer_engineering", 0), gcg_data["session_type"]])
        
        # Compute
        compute = gcg_data.get("compute", {})
        on_prem = compute.get("on_premise", {})
        writer.writerow(["COMPUTE", "Number of Development Servers", on_prem.get("dev_servers", 0), gcg_data["session_type"]])
        writer.writerow(["COMPUTE", "Do you use GPU in Development?", on_prem.get("dev_gpu", "No"), gcg_data["session_type"]])
        writer.writerow(["COMPUTE", "Number of Development CPU per Server", on_prem.get("dev_cpu_per_server"), gcg_data["session_type"]])
        writer.writerow(["COMPUTE", "Memory (GB) per Development CPU", on_prem.get("dev_memory_gb_per_cpu"), gcg_data["session_type"]])
        
        # Network
        network = gcg_data.get("network", {})
        writer.writerow(["NETWORK", "Average Dev/Test Hits per Minute", network.get("avg_dev_test_hits_per_min"), gcg_data["session_type"]])
        writer.writerow(["NETWORK", "Average Network Packet Size (KB)", network.get("avg_network_packet_size_kb"), gcg_data["session_type"]])
        
        # Engineering Factors
        eng = gcg_data.get("engineering_factors", {})
        writer.writerow(["ENGINEERING", "Main Programming Language", eng.get("main_programming_language"), gcg_data["session_type"]])
        writer.writerow(["ENGINEERING", "SSE Rating Above Very Good?", eng.get("sse_rating_above_very_good"), gcg_data["session_type"]])
        writer.writerow(["ENGINEERING", "DevOps Maturity Above 4?", eng.get("devops_maturity_above_4"), gcg_data["session_type"]])
        
        # Sustainability
        sustainability = gcg_data.get("sustainability", {})
        writer.writerow(["SUSTAINABILITY", "Total Energy (kWh)", sustainability.get("total_energy_kwh"), gcg_data["session_type"]])
        writer.writerow(["SUSTAINABILITY", "Total Emissions (kg CO2)", sustainability.get("total_emissions_kg_co2"), gcg_data["session_type"]])
        writer.writerow(["SUSTAINABILITY", "Compute Cycles", sustainability.get("compute_cycles"), gcg_data["session_type"]])


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Fill GoCodeGreen template with collected experiment data"
    )
    parser.add_argument(
        "aggregated_data_file",
        type=str,
        help="Path to aggregated experiment data JSON file"
    )
    parser.add_argument(
        "-t", "--session-type",
        type=str,
        choices=["manual", "ai-assisted"],
        default="manual",
        help="Session type (default: manual)"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="DATA_COLLECTION/gocodegreen_data.csv",
        help="Output CSV file path"
    )
    parser.add_argument(
        "--json-output",
        type=str,
        help="Also output JSON format (optional)"
    )
    
    args = parser.parse_args()
    
    # Load aggregated data
    aggregated_data = load_aggregated_data(args.aggregated_data_file)
    
    # Map to GoCodeGreen format
    gcg_data = map_to_gocodegreen_format(aggregated_data, args.session_type)
    
    # Generate CSV output
    generate_csv_output(gcg_data, args.output)
    print(f"GoCodeGreen CSV data saved to: {args.output}")
    
    # Generate JSON output if requested
    if args.json_output:
        json_path = Path(args.json_output)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(json_path, "w") as f:
            json.dump(gcg_data, f, indent=2)
        
        print(f"GoCodeGreen JSON data saved to: {args.json_output}")
    
    # Print summary
    print(f"\n=== GoCodeGreen Data Summary ===")
    print(f"Programme: {gcg_data['programme_name']}")
    print(f"Session Type: {gcg_data['session_type']}")
    print(f"Location: {gcg_data.get('location')}")
    print(f"Working Hours: {gcg_data.get('working_hours_per_day')}")
    
    if gcg_data.get("sustainability", {}).get("total_energy_kwh"):
        print(f"Energy: {gcg_data['sustainability']['total_energy_kwh']:.4f} kWh")
    if gcg_data.get("sustainability", {}).get("total_emissions_kg_co2"):
        print(f"Emissions: {gcg_data['sustainability']['total_emissions_kg_co2']:.4f} kg CO2")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
