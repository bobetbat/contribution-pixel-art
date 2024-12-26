#!/usr/bin/env python3

import subprocess
import datetime
import json
import os
import sys

def make_commits_for_day(date_obj, num_commits):
    """
    Creates `num_commits` empty commits on the specified date_obj by
    setting GIT_AUTHOR_DATE and GIT_COMMITTER_DATE.
    """
    base_time_str = date_obj.strftime("%Y-%m-%d 12:00:00")

    for i in range(num_commits):
        env = os.environ.copy()
        commit_datetime = datetime.datetime.strptime(base_time_str, "%Y-%m-%d %H:%M:%S")
        commit_datetime += datetime.timedelta(seconds=i)  # offset each commit by i seconds
        commit_datetime_str = commit_datetime.strftime("%Y-%m-%d %H:%M:%S")

        env["GIT_AUTHOR_DATE"] = commit_datetime_str
        env["GIT_COMMITTER_DATE"] = commit_datetime_str

        subprocess.run(
            [
                "git",
                "commit",
                "--allow-empty",
                "-m",
                f"Backdated commit on {commit_datetime_str} (#{i+1})",
            ],
            env=env,
            check=True,
        )

def find_sunday_weeks_ago(weeks_ago=52):
    """
    Returns the date (as a 'YYYY-mm-dd' string) for the Sunday that is
    `weeks_ago` weeks prior to the most recent Sunday.
    """
    today = datetime.date.today()
    # Monday=0, Sunday=6 for weekday(); we want to find how many days since last Sunday.
    offset = (today.weekday() + 1) % 7
    last_sunday = today - datetime.timedelta(days=offset)
    target_sunday = last_sunday - datetime.timedelta(weeks=weeks_ago)
    return target_sunday.strftime("%Y-%m-%d")

def backdate_commits_for_matrix(start_date_str, pixel_art, commit_map):
    """
    Interprets `pixel_art` as row=day offset, col=week offset (7 rows, X columns).
    Creates commits accordingly, then pushes to 'origin main'.
    """

    # Convert the start_date string to a date object
    start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()

    rows = len(pixel_art)
    cols = len(pixel_art[0]) if rows > 0 else 0

    for col in range(cols):
        for row in range(rows):
            date_for_cell = start_date + datetime.timedelta(weeks=col, days=row)
            shade_code = pixel_art[row][col]  # e.g. 1
            # commit_map keys are strings, so convert shade_code -> str
            num_commits = commit_map.get(str(shade_code), 0)
            if num_commits > 0:
                make_commits_for_day(date_for_cell, num_commits)

    # Push after creating all commits
    subprocess.run(["git", "push", "origin", "main"], check=True)

def main():
    # Always read from 'config.json'
    matrix_file = "config.json"
    if not os.path.exists(matrix_file):
        print(f"Error: {matrix_file} not found. Please create it.")
        sys.exit(1)

    with open(matrix_file, "r") as f:
        data = json.load(f)

    start_date = data.get("start_date")  # might be 'AUTO' or actual date
    pixel_art = data.get("pixel_art", [])
    commit_map = data.get("commit_map", {})

    if not pixel_art:
        print("Error: 'pixel_art' is empty or missing in config.json.")
        sys.exit(1)
    if not commit_map:
        print("Warning: 'commit_map' is empty. All codes will map to 0 commits.")

    # If 'AUTO', compute the Sunday from 52 weeks ago
    if start_date == "AUTO":
        start_date = find_sunday_weeks_ago(52)
        print(f"Using auto-calculated start_date = {start_date}")
    else:
        print(f"Using provided start_date = {start_date}")

    # Stage any changes (just in case)
    subprocess.run(["git", "add", "."], check=True)

    # Backdate commits
    backdate_commits_for_matrix(start_date, pixel_art, commit_map)
    print("Done backdating commits.")

if __name__ == "__main__":
    main()
