#!/usr/bin/env python3
"""
Analyze all Bitnami Helm charts for dependency validation
"""

import yaml
import os
import json
from pathlib import Path

# Expected local repository URL
LOCAL_REPO_URL = "https://portswigger-cloud.github.io/legacy-charts/"

def analyze_chart(chart_path):
    """Analyze a single Chart.yaml file"""
    try:
        with open(chart_path, 'r') as f:
            chart_data = yaml.safe_load(f)
        
        result = {
            'path': str(chart_path),
            'name': chart_data.get('name', 'Unknown'),
            'version': chart_data.get('version', 'Unknown'),
            'app_version': chart_data.get('appVersion', 'Unknown'),
            'dependencies': [],
            'external_repos': [],
            'local_repo_deps': [],
            'errors': []
        }
        
        # Analyze dependencies
        dependencies = chart_data.get('dependencies', [])
        for dep in dependencies:
            dep_info = {
                'name': dep.get('name', 'Unknown'),
                'version': dep.get('version', 'Unknown'),
                'repository': dep.get('repository', ''),
                'condition': dep.get('condition', ''),
                'tags': dep.get('tags', [])
            }
            result['dependencies'].append(dep_info)
            
            # Check repository URL
            repo_url = dep.get('repository', '')
            if repo_url:
                if repo_url == LOCAL_REPO_URL:
                    result['local_repo_deps'].append(dep_info)
                elif repo_url.startswith('http'):
                    result['external_repos'].append({
                        'dependency': dep_info['name'],
                        'repository': repo_url
                    })
        
        return result
    
    except Exception as e:
        return {
            'path': str(chart_path),
            'name': 'ERROR',
            'version': 'ERROR',
            'app_version': 'ERROR',
            'dependencies': [],
            'external_repos': [],
            'local_repo_deps': [],
            'errors': [str(e)]
        }

def main():
    base_path = Path("/Users/alex.mason/workspaces/portswigger/ps-cloud/legacy-charts/bitnami")
    
    # Find all Chart.yaml files
    chart_files = list(base_path.glob("*/Chart.yaml"))
    chart_files.extend(list(base_path.glob("*/charts/*/Chart.yaml")))  # Include subcharts
    
    print(f"Found {len(chart_files)} Chart.yaml files")
    
    all_results = []
    charts_with_external_deps = []
    charts_with_errors = []
    charts_without_deps = []
    dependency_summary = {}
    
    for chart_file in sorted(chart_files):
        result = analyze_chart(chart_file)
        all_results.append(result)
        
        # Categorize results
        if result['errors']:
            charts_with_errors.append(result)
        elif result['external_repos']:
            charts_with_external_deps.append(result)
        elif not result['dependencies']:
            charts_without_deps.append(result)
        
        # Track dependency usage
        for dep in result['dependencies']:
            dep_name = dep['name']
            if dep_name not in dependency_summary:
                dependency_summary[dep_name] = []
            dependency_summary[dep_name].append({
                'chart': result['name'],
                'version': dep['version'],
                'repository': dep['repository']
            })
    
    # Generate report
    print("\n" + "="*80)
    print("BITNAMI HELM CHARTS DEPENDENCY ANALYSIS REPORT")
    print("="*80)
    
    print(f"\nTOTAL CHARTS ANALYZED: {len(all_results)}")
    print(f"Charts with external dependencies: {len(charts_with_external_deps)}")
    print(f"Charts with errors: {len(charts_with_errors)}")
    print(f"Charts without dependencies: {len(charts_without_deps)}")
    print(f"Charts with local dependencies only: {len(all_results) - len(charts_with_external_deps) - len(charts_with_errors) - len(charts_without_deps)}")
    
    # Report charts with external dependencies (ISSUES)
    if charts_with_external_deps:
        print(f"\n🚨 CHARTS WITH EXTERNAL DEPENDENCIES ({len(charts_with_external_deps)}):")
        print("-" * 60)
        for chart in charts_with_external_deps:
            print(f"Chart: {chart['name']} (v{chart['version']})")
            for ext_dep in chart['external_repos']:
                print(f"  ❌ {ext_dep['dependency']} -> {ext_dep['repository']}")
            print()
    
    # Report charts with errors
    if charts_with_errors:
        print(f"\n⚠️  CHARTS WITH ERRORS ({len(charts_with_errors)}):")
        print("-" * 60)
        for chart in charts_with_errors:
            print(f"Chart: {chart['name']} - {chart['path']}")
            for error in chart['errors']:
                print(f"  Error: {error}")
            print()
    
    # Dependency usage summary
    print(f"\n📊 DEPENDENCY USAGE SUMMARY:")
    print("-" * 60)
    for dep_name, usages in sorted(dependency_summary.items()):
        print(f"{dep_name}: used by {len(usages)} charts")
        unique_repos = set(usage['repository'] for usage in usages)
        for repo in sorted(unique_repos):
            charts_using_repo = [usage['chart'] for usage in usages if usage['repository'] == repo]
            print(f"  Repository: {repo or 'None'} ({len(charts_using_repo)} charts)")
    
    # Charts without dependencies (library charts)
    print(f"\n📝 CHARTS WITHOUT DEPENDENCIES ({len(charts_without_deps)}):")
    print("-" * 60)
    for chart in charts_without_deps:
        print(f"  {chart['name']} (v{chart['version']})")
    
    print(f"\n✅ VALIDATION SUMMARY:")
    print("-" * 60)
    total_charts = len(all_results)
    clean_charts = total_charts - len(charts_with_external_deps) - len(charts_with_errors)
    print(f"Total charts: {total_charts}")
    print(f"Charts properly configured: {clean_charts}")
    print(f"Charts needing attention: {len(charts_with_external_deps) + len(charts_with_errors)}")
    print(f"Success rate: {(clean_charts/total_charts)*100:.1f}%")
    
    if len(charts_with_external_deps) == 0 and len(charts_with_errors) == 0:
        print("\n🎉 ALL CHARTS ARE PROPERLY CONFIGURED!")
        print("All dependencies point to the local repository as expected.")
    
    return all_results

if __name__ == "__main__":
    results = main()