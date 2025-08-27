#!/bin/bash

# Script to increment patch versions for all charts with dependencies
# This is needed because the current published versions have removed dependencies
# but the local versions have restored self-sufficient dependencies

echo "=== Incrementing chart versions for dependency fixes ==="

count=0
for chart_file in bitnami/*/Chart.yaml; do
    # Skip if no dependencies
    if ! grep -q "dependencies:" "$chart_file"; then
        continue
    fi
    
    chart_dir=$(dirname "$chart_file")
    chart_name=$(basename "$chart_dir")
    
    # Get current version
    current_version=$(grep "^version:" "$chart_file" | cut -d' ' -f2)
    
    # Parse version (assuming semantic versioning: MAJOR.MINOR.PATCH)
    if [[ $current_version =~ ^([0-9]+)\.([0-9]+)\.([0-9]+)$ ]]; then
        major="${BASH_REMATCH[1]}"
        minor="${BASH_REMATCH[2]}"
        patch="${BASH_REMATCH[3]}"
        
        # Increment patch version
        new_patch=$((patch + 1))
        new_version="${major}.${minor}.${new_patch}"
        
        echo "Updating $chart_name: $current_version → $new_version"
        
        # Update the version in Chart.yaml
        sed -i '' "s/^version: $current_version/version: $new_version/" "$chart_file"
        
        count=$((count + 1))
    else
        echo "WARNING: $chart_name has non-standard version format: $current_version (skipping)"
    fi
done

echo ""
echo "=== Summary ==="
echo "Updated $count chart versions"
echo "All charts with dependencies now have incremented patch versions"
echo "This ensures users get the self-sufficient versions with correct repository references"