#!/usr/bin/env python3
"""Calculate carbon footprint from energy consumption and other factors.

This script converts energy consumption to carbon emissions using location-based
grid emission factors, and includes network emissions and other sources.
"""

import json
import sys
from datetime import datetime
from pathlib import Path


# Grid emission factors (kg CO2 per kWh) by location
# Source: IEA, EPA, and other public sources (approximate values)
GRID_EMISSION_FACTORS = {
    "uk": 0.233,  # UK grid average
    "europe": 0.300,  # European average
    "usa": 0.416,  # US average
    "canada": 0.130,  # Canada (mostly hydro)
    "china": 0.681,  # China (coal-heavy)
    "india": 0.708,  # India (coal-heavy)
    "australia": 0.760,  # Australia (coal-heavy)
    "default": 0.400,  # Global average
}

# Network emission factors (kg CO2 per GB)
# Approximate values based on data center and network infrastructure
NETWORK_EMISSION_FACTOR = 0.0004  # kg CO2 per GB transferred

# Travel emission factors (kg CO2 per km or per trip)
TRAVEL_EMISSION_FACTORS = {
    "car": 0.120,  # kg CO2 per km
    "bus": 0.089,  # kg CO2 per km
    "train": 0.041,  # kg CO2 per km
    "flight_short": 0.255,  # kg CO2 per km
    "flight_long": 0.195,  # kg CO2 per km
}


def get_grid_emission_factor(location):
    """Get grid emission factor for location.
    
    Args:
        location: Location string (uk, europe, usa, etc.)
    
    Returns:
        Emission factor (kg CO2 per kWh)
    """
    location_lower = location.lower() if location else "default"
    
    # Map common location names
    location_map = {
        "united kingdom": "uk",
        "uk": "uk",
        "great britain": "uk",
        "england": "uk",
        "scotland": "uk",
        "wales": "uk",
        "north america": "usa",
        "united states": "usa",
        "us": "usa",
    }
    
    location_key = location_map.get(location_lower, location_lower)
    return GRID_EMISSION_FACTORS.get(location_key, GRID_EMISSION_FACTORS["default"])


def calculate_energy_emissions(energy_kwh, location):
    """Calculate CO2 emissions from energy consumption.
    
    Args:
        energy_kwh: Energy consumption in kWh
        location: Location string
    
    Returns:
        CO2 emissions in kg
    """
    emission_factor = get_grid_emission_factor(location)
    emissions_kg = energy_kwh * emission_factor
    return emissions_kg


def calculate_network_emissions(data_gb):
    """Calculate CO2 emissions from network data transfer.
    
    Args:
        data_gb: Data transferred in GB
    
    Returns:
        CO2 emissions in kg
    """
    emissions_kg = data_gb * NETWORK_EMISSION_FACTOR
    return emissions_kg


def calculate_travel_emissions(travel_data):
    """Calculate CO2 emissions from travel.
    
    Args:
        travel_data: Dictionary with travel information
    
    Returns:
        CO2 emissions in kg
    """
    total_emissions = 0.0
    
    # Car trips (assuming average trip distance)
    car_trips = travel_data.get("car_trips", 0)
    car_distance_km = travel_data.get("car_distance_km", 10)  # Default 10km per trip
    if car_trips > 0:
        total_emissions += car_trips * car_distance_km * TRAVEL_EMISSION_FACTORS["car"]
    
    # Bus trips
    bus_trips = travel_data.get("bus_trips", 0)
    bus_distance_km = travel_data.get("bus_distance_km", 5)  # Default 5km per trip
    if bus_trips > 0:
        total_emissions += bus_trips * bus_distance_km * TRAVEL_EMISSION_FACTORS["bus"]
    
    # Train trips
    train_trips = travel_data.get("train_trips", 0)
    train_distance_km = travel_data.get("train_distance_km", 20)  # Default 20km per trip
    if train_trips > 0:
        total_emissions += train_trips * train_distance_km * TRAVEL_EMISSION_FACTORS["train"]
    
    # Flights
    short_haul_flights = travel_data.get("short_haul_flights", 0)
    short_haul_distance_km = travel_data.get("short_haul_distance_km", 500)  # Default 500km
    if short_haul_flights > 0:
        total_emissions += short_haul_flights * short_haul_distance_km * TRAVEL_EMISSION_FACTORS["flight_short"]
    
    long_haul_flights = travel_data.get("long_haul_flights", 0)
    long_haul_distance_km = travel_data.get("long_haul_distance_km", 5000)  # Default 5000km
    if long_haul_flights > 0:
        total_emissions += long_haul_flights * long_haul_distance_km * TRAVEL_EMISSION_FACTORS["flight_long"]
    
    return total_emissions


def calculate_compute_cycles(energy_kwh):
    """Estimate compute cycles from energy consumption.
    
    This is a rough approximation - actual compute cycles depend on CPU type,
    workload, and efficiency.
    
    Args:
        energy_kwh: Energy consumption in kWh
    
    Returns:
        Estimated compute cycles (arbitrary units)
    """
    # Rough approximation: 1 kWh ≈ 3.6 million CPU cycles (for typical laptop CPU)
    # This is highly approximate and depends on CPU efficiency
    cycles_per_kwh = 3600000
    return energy_kwh * cycles_per_kwh


def calculate_carbon_footprint(
    energy_file,
    location,
    network_data_gb=0,
    travel_data=None,
    output_file=None
):
    """Calculate total carbon footprint.
    
    Args:
        energy_file: Path to energy estimate JSON file
        location: Location string for grid emission factor
        network_data_gb: Network data transferred in GB
        travel_data: Dictionary with travel information
        output_file: Output JSON file path
    
    Returns:
        Dictionary with carbon footprint data
    """
    # Load energy estimate
    with open(energy_file, "r") as f:
        energy_data = json.load(f)
    
    energy_kwh = energy_data["total_energy"]["kwh"]
    
    # Calculate emissions from energy
    energy_emissions = calculate_energy_emissions(energy_kwh, location)
    
    # Calculate emissions from network
    network_emissions = calculate_network_emissions(network_data_gb)
    
    # Calculate emissions from travel
    travel_emissions = 0.0
    if travel_data:
        travel_emissions = calculate_travel_emissions(travel_data)
    
    # Total emissions
    total_emissions_kg = energy_emissions + network_emissions + travel_emissions
    
    # Estimate compute cycles
    compute_cycles = calculate_compute_cycles(energy_kwh)
    
    footprint = {
        "calculation_timestamp": datetime.now().isoformat(),
        "location": location,
        "grid_emission_factor": get_grid_emission_factor(location),
        "energy": {
            "kwh": energy_kwh,
            "emissions_kg_co2": round(energy_emissions, 4),
        },
        "network": {
            "data_gb": network_data_gb,
            "emissions_kg_co2": round(network_emissions, 4),
        },
        "travel": {
            "emissions_kg_co2": round(travel_emissions, 4),
            "data": travel_data or {},
        },
        "total": {
            "emissions_kg_co2": round(total_emissions_kg, 4),
            "emissions_g_co2": round(total_emissions_kg * 1000, 2),
        },
        "compute": {
            "estimated_cycles": int(compute_cycles),
            "cycles_per_kwh": 3600000,
        },
        "breakdown_percent": {
            "energy": round((energy_emissions / total_emissions_kg * 100) if total_emissions_kg > 0 else 0, 1),
            "network": round((network_emissions / total_emissions_kg * 100) if total_emissions_kg > 0 else 0, 1),
            "travel": round((travel_emissions / total_emissions_kg * 100) if total_emissions_kg > 0 else 0, 1),
        },
        "notes": [
            "Emission factors are approximate and may vary by region and time",
            "Network emissions are estimates based on data center and infrastructure",
            "Travel emissions depend on actual distances traveled",
            "Compute cycles are rough approximations",
        ],
    }
    
    # Save to file if specified
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w") as f:
            json.dump(footprint, f, indent=2)
        
        print(f"Carbon footprint calculation saved to: {output_path}")
    
    return footprint


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Calculate carbon footprint from energy consumption"
    )
    parser.add_argument(
        "energy_file",
        type=str,
        help="Path to energy estimate JSON file"
    )
    parser.add_argument(
        "-l", "--location",
        type=str,
        default="uk",
        help="Location for grid emission factor (default: uk)"
    )
    parser.add_argument(
        "-n", "--network-data",
        type=float,
        default=0,
        help="Network data transferred in GB (default: 0)"
    )
    parser.add_argument(
        "-t", "--travel-data",
        type=str,
        help="Path to travel data JSON file"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="DATA_COLLECTION/carbon_footprint.json",
        help="Output JSON file path"
    )
    parser.add_argument(
        "--participant-id",
        type=str,
        help="Participant ID to include in filename"
    )
    
    args = parser.parse_args()
    
    # Load travel data if provided
    travel_data = None
    if args.travel_data:
        with open(args.travel_data, "r") as f:
            travel_data = json.load(f)
    
    # Determine output path
    output_path = args.output
    if args.participant_id:
        output_path = f"DATA_COLLECTION/carbon_footprint_{args.participant_id}.json"
    
    # Calculate footprint
    footprint = calculate_carbon_footprint(
        args.energy_file,
        args.location,
        network_data_gb=args.network_data,
        travel_data=travel_data,
        output_file=output_path
    )
    
    # Print summary
    print("\n=== Carbon Footprint Calculation ===")
    print(f"Location: {footprint['location']}")
    print(f"Grid emission factor: {footprint['grid_emission_factor']} kg CO2/kWh")
    print(f"\nEnergy:")
    print(f"  Consumption: {footprint['energy']['kwh']:.4f} kWh")
    print(f"  Emissions: {footprint['energy']['emissions_kg_co2']:.4f} kg CO2")
    print(f"\nNetwork:")
    print(f"  Data: {footprint['network']['data_gb']:.2f} GB")
    print(f"  Emissions: {footprint['network']['emissions_kg_co2']:.4f} kg CO2")
    print(f"\nTravel:")
    print(f"  Emissions: {footprint['travel']['emissions_kg_co2']:.4f} kg CO2")
    print(f"\nTotal Emissions: {footprint['total']['emissions_kg_co2']:.4f} kg CO2 ({footprint['total']['emissions_g_co2']:.2f} g CO2)")
    print(f"\nBreakdown:")
    print(f"  Energy: {footprint['breakdown_percent']['energy']:.1f}%")
    print(f"  Network: {footprint['breakdown_percent']['network']:.1f}%")
    print(f"  Travel: {footprint['breakdown_percent']['travel']:.1f}%")
    print(f"\nEstimated Compute Cycles: {footprint['compute']['estimated_cycles']:,}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
