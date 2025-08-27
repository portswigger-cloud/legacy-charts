#!/bin/bash

echo "==============================================================================="
echo "BITNAMI HELM CHARTS DEPENDENCY ANALYSIS REPORT"
echo "==============================================================================="

BASE_DIR="/Users/alex.mason/workspaces/portswigger/ps-cloud/legacy-charts/bitnami"
LOCAL_REPO="https://portswigger-cloud.github.io/legacy-charts/"

# Count charts
TOTAL_CHARTS=$(find "$BASE_DIR" -name "Chart.yaml" | wc -l | tr -d ' ')
echo "Total Chart.yaml files found: $TOTAL_CHARTS"

echo
echo "📊 ANALYZING ALL CHARTS..."
echo "-------------------------------------------------------------------------------"

# Initialize counters
charts_with_external_deps=0
charts_with_errors=0
charts_without_deps=0
charts_clean=0

# Create temporary files for categorization
external_deps_file=$(mktemp)
error_charts_file=$(mktemp)
no_deps_file=$(mktemp)
clean_charts_file=$(mktemp)

# Analyze each chart
while IFS= read -r chart_file; do
    chart_dir=$(dirname "$chart_file")
    chart_name=$(basename "$chart_dir")
    
    # Extract basic info
    name=$(grep "^name:" "$chart_file" | head -1 | cut -d' ' -f2)
    version=$(grep "^version:" "$chart_file" | head -1 | cut -d' ' -f2)
    app_version=$(grep "^appVersion:" "$chart_file" | head -1 | cut -d' ' -f2)
    
    # Check if file has dependencies section
    if ! grep -q "^dependencies:" "$chart_file"; then
        echo "$name ($version) - No dependencies" >> "$no_deps_file"
        ((charts_without_deps++))
        continue
    fi
    
    # Extract dependencies section and analyze
    has_external_deps=false
    external_repos=""
    
    # Get all repository lines from dependencies section
    deps_section=$(sed -n '/^dependencies:/,/^[a-zA-Z]/p' "$chart_file" | head -n -1)
    
    while IFS= read -r line; do
        if [[ "$line" =~ repository:.*https?:// ]]; then
            repo_url=$(echo "$line" | sed 's/.*repository: *//' | tr -d '"')
            if [[ "$repo_url" != "$LOCAL_REPO" ]]; then
                has_external_deps=true
                external_repos+="    ❌ External repo: $repo_url"$'\n'
            fi
        fi
    done <<< "$deps_section"
    
    if [[ "$has_external_deps" == true ]]; then
        echo "$name ($version):" >> "$external_deps_file"
        echo "$external_repos" >> "$external_deps_file"
        ((charts_with_external_deps++))
    else
        echo "$name ($version) - ✅ All dependencies use local repo" >> "$clean_charts_file"
        ((charts_clean++))
    fi
    
done < <(find "$BASE_DIR" -name "Chart.yaml" | sort)

echo
echo "🔍 ANALYSIS RESULTS:"
echo "-------------------------------------------------------------------------------"
echo "Charts with external dependencies: $charts_with_external_deps"
echo "Charts with errors: $charts_with_errors" 
echo "Charts without dependencies: $charts_without_deps"
echo "Charts properly configured: $charts_clean"

if [[ $charts_with_external_deps -gt 0 ]]; then
    echo
    echo "🚨 CHARTS WITH EXTERNAL DEPENDENCIES:"
    echo "-------------------------------------------------------------------------------"
    cat "$external_deps_file"
fi

echo
echo "📝 CHARTS WITHOUT DEPENDENCIES (Library charts):"
echo "-------------------------------------------------------------------------------"
cat "$no_deps_file"

echo
echo "✅ PROPERLY CONFIGURED CHARTS:"
echo "-------------------------------------------------------------------------------"
head -20 "$clean_charts_file"
if [[ $(wc -l < "$clean_charts_file") -gt 20 ]]; then
    echo "... and $(($(wc -l < "$clean_charts_file") - 20)) more charts"
fi

echo
echo "📊 VALIDATION SUMMARY:"
echo "-------------------------------------------------------------------------------"
success_rate=$((charts_clean * 100 / TOTAL_CHARTS))
echo "Total charts: $TOTAL_CHARTS"
echo "Charts properly configured: $charts_clean"
echo "Charts needing attention: $((charts_with_external_deps + charts_with_errors))"
echo "Success rate: $success_rate%"

if [[ $charts_with_external_deps -eq 0 && $charts_with_errors -eq 0 ]]; then
    echo
    echo "🎉 ALL CHARTS ARE PROPERLY CONFIGURED!"
    echo "All dependencies point to the local repository as expected."
fi

# Dependency usage analysis
echo
echo "📈 DEPENDENCY USAGE ANALYSIS:"
echo "-------------------------------------------------------------------------------"

# Extract all dependency names and their usage
dep_usage_file=$(mktemp)
while IFS= read -r chart_file; do
    # Extract dependency names from each chart
    sed -n '/^dependencies:/,/^[a-zA-Z]/p' "$chart_file" | grep "^- name:" | sed 's/^- name: //' | while read dep_name; do
        chart_name=$(grep "^name:" "$chart_file" | head -1 | cut -d' ' -f2)
        echo "$dep_name|$chart_name" >> "$dep_usage_file"
    done
done < <(find "$BASE_DIR" -name "Chart.yaml")

# Summarize dependency usage
if [[ -f "$dep_usage_file" ]] && [[ -s "$dep_usage_file" ]]; then
    echo "Most commonly used dependencies:"
    cut -d'|' -f1 "$dep_usage_file" | sort | uniq -c | sort -nr | head -10 | while read count dep; do
        echo "  $dep: used by $count charts"
    done
fi

# Cleanup
rm -f "$external_deps_file" "$error_charts_file" "$no_deps_file" "$clean_charts_file" "$dep_usage_file"

echo
echo "==============================================================================="