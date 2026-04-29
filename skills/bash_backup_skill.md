---
name: bash_backup_skill
tags: [bash, backup, zip, timestamp, automation]
trigger: task involves backing up a folder or creating timestamped archives
type: tool
version: 1
success_count: 0
fail_count: 0
---
# Bash Backup Skill

## Purpose
Backup a folder to a timestamped zip file using bash.

## When to use
Use this skill when you need to backup a folder and want to automate the process using bash.

## How to use
1. Create a new bash script with the content below.
2. Replace `/path/to/folder` with the path to the folder you want to backup.
3. Replace `/path/to/backup` with the path where you want to store the backup.
4. Run the script using `bash script_name.sh`.

## Template
```bash
#!/bin/bash
FOLDER_TO_BACKUP="/path/to/folder"
BACKUP_LOCATION="/path/to/backup"
mkdir -p "$BACKUP_LOCATION"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
zip -r "$BACKUP_LOCATION/backup_${TIMESTAMP}.zip" "$FOLDER_TO_BACKUP"
echo "Backup created: $BACKUP_LOCATION/backup_${TIMESTAMP}.zip"
```

## Example use case
Backup a website's content folder to a timestamped zip file every day.
