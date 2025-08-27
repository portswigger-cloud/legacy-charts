#!/usr/bin/env python3

import os
import yaml
import re

def get_chart_version(chart_path):
    """Get the version of a chart from its Chart.yaml"""
    try:
        with open(os.path.join(chart_path, 'Chart.yaml'), 'r') as f:
            chart = yaml.safe_load(f)
            return chart.get('version', 'unknown')
    except:
        return None

def get_chart_dependencies(chart_path):
    """Get dependencies from a chart's Chart.yaml"""
    try:
        with open(os.path.join(chart_path, 'Chart.yaml'), 'r') as f:
            chart = yaml.safe_load(f)
            return chart.get('dependencies', [])
    except:
        return []

def main():
    bitnami_dir = 'bitnami'
    
    # Get all chart versions
    chart_versions = {}
    print("=== Available Chart Versions ===")
    for item in sorted(os.listdir(bitnami_dir)):
        chart_path = os.path.join(bitnami_dir, item)
        if os.path.isdir(chart_path) and item != 'common':
            version = get_chart_version(chart_path)
            if version:
                chart_versions[item] = version
                print(f"{item}: {version}")
    
    print("\n=== Dependency Version Mismatches ===")
    mismatches = []
    
    for chart_name in sorted(chart_versions.keys()):
        chart_path = os.path.join(bitnami_dir, chart_name)
        dependencies = get_chart_dependencies(chart_path)
        
        for dep in dependencies:
            dep_name = dep.get('name')
            dep_version = dep.get('version')
            dep_repo = dep.get('repository', '')
            
            # Skip if not our repository or common chart
            if 'portswigger-cloud.github.io' not in dep_repo or dep_name == 'common':
                continue
                
            if dep_name in chart_versions:
                actual_version = chart_versions[dep_name]
                # Extract major version from constraint (e.g., "8.x.x" -> "8")
                if dep_version and 'x.x' in dep_version:
                    constraint_major = dep_version.split('.')[0]
                    # Extract major version from actual version
                    actual_major = actual_version.split('.')[0]
                    
                    if constraint_major != actual_major:
                        mismatches.append({
                            'chart': chart_name,
                            'dependency': dep_name,
                            'constraint': dep_version,
                            'actual': actual_version,
                            'expected': f"{actual_major}.x.x"
                        })
    
    if mismatches:
        for mismatch in mismatches:
            print(f"{mismatch['chart']} -> {mismatch['dependency']}: {mismatch['constraint']} (should be {mismatch['expected']}, actual: {mismatch['actual']})")
    else:
        print("No mismatches found!")
    
    return len(mismatches)

if __name__ == '__main__':
    count = main()
    print(f"\nFound {count} version mismatches")