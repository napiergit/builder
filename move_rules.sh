#!/bin/bash

# Script to move rules/requirements.md files to .windsurf/rules/requirements.md
# in each feature folder as specified in global rules

echo "Moving requirements.md files to correct .windsurf/rules/ structure..."

# Feature folders that have rules/requirements.md
FEATURE_FOLDERS=("builder" "cookiecutter" "llm" "tests" "host")

for folder in "${FEATURE_FOLDERS[@]}"; do
    if [ -d "$folder" ]; then
        echo "Processing $folder..."
        
        # Create .windsurf/rules directory if it doesn't exist
        mkdir -p "$folder/.windsurf/rules"
        
        # Move requirements.md from rules/ to .windsurf/rules/
        if [ -f "$folder/rules/requirements.md" ]; then
            mv "$folder/rules/requirements.md" "$folder/.windsurf/rules/requirements.md"
            echo "  Moved $folder/rules/requirements.md -> $folder/.windsurf/rules/requirements.md"
            
            # Remove empty rules directory
            if [ -d "$folder/rules" ] && [ -z "$(ls -A $folder/rules)" ]; then
                rmdir "$folder/rules"
                echo "  Removed empty $folder/rules directory"
            fi
        else
            echo "  No requirements.md found in $folder/rules/"
        fi
    else
        echo "  Directory $folder does not exist, skipping..."
    fi
done

echo "Done! All requirements.md files moved to correct .windsurf/rules/ structure."
