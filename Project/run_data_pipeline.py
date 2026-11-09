"""Entry point 2: clean all five raw extracts and write the quality report."""

import os

from config import config
from data_pipeline.dataset_loader import load_raw_dataset
from data_pipeline.effort_cleaning import clean_effort_dataset
from data_pipeline.incident_cleaning import clean_incident_dataset
from data_pipeline.incident_note_cleaning import clean_incident_note_dataset
from data_pipeline.quality_profiler import (profile_dataset, profile_effort_details,
                                            profile_incident_details, profile_note_details,
                                            write_quality_report)


def _dataset_name(raw_path):
    return os.path.splitext(os.path.basename(raw_path))[0]


JOBS = [
    {"dataset": _dataset_name(config.RAW_INCIDENTS_TRAIN_FILE),
     "raw_file": config.RAW_INCIDENTS_TRAIN_FILE, "clean_file": config.CLEAN_INCIDENTS_TRAIN_FILE,
     "cleaner": clean_incident_dataset, "target_column": config.INCIDENT_TARGET_COLUMN,
     "range_limits": config.INCIDENT_RANGE_LIMITS, "detail_profiler": profile_incident_details},
    {"dataset": _dataset_name(config.RAW_INCIDENTS_EVAL_FILE),
     "raw_file": config.RAW_INCIDENTS_EVAL_FILE, "clean_file": config.CLEAN_INCIDENTS_EVAL_FILE,
     "cleaner": clean_incident_dataset, "target_column": config.INCIDENT_TARGET_COLUMN,
     "range_limits": config.INCIDENT_RANGE_LIMITS, "detail_profiler": profile_incident_details},
    {"dataset": _dataset_name(config.RAW_EFFORT_TRAIN_FILE),
     "raw_file": config.RAW_EFFORT_TRAIN_FILE, "clean_file": config.CLEAN_EFFORT_TRAIN_FILE,
     "cleaner": clean_effort_dataset, "target_column": config.EFFORT_TARGET_COLUMN,
     "range_limits": config.EFFORT_RANGE_LIMITS, "detail_profiler": profile_effort_details},
    {"dataset": _dataset_name(config.RAW_EFFORT_EVAL_FILE),
     "raw_file": config.RAW_EFFORT_EVAL_FILE, "clean_file": config.CLEAN_EFFORT_EVAL_FILE,
     "cleaner": clean_effort_dataset, "target_column": config.EFFORT_TARGET_COLUMN,
     "range_limits": config.EFFORT_RANGE_LIMITS, "detail_profiler": profile_effort_details},
    {"dataset": _dataset_name(config.RAW_INCIDENT_NOTES_FILE),
     "raw_file": config.RAW_INCIDENT_NOTES_FILE, "clean_file": config.CLEAN_INCIDENT_NOTES_FILE,
     "cleaner": clean_incident_note_dataset, "target_column": config.NOTE_TARGET_COLUMN,
     "range_limits": config.NOTE_RANGE_LIMITS, "detail_profiler": profile_note_details},
]


def main():
    """Clean every extract in JOBS order, profile each and write the report."""
    for folder in {os.path.dirname(job["clean_file"]) for job in JOBS} | {
            os.path.dirname(config.DATA_QUALITY_REPORT_FILE)}:
        if folder:
            os.makedirs(folder, exist_ok=True)

    profiles = {}
    for job in JOBS:
        raw_frame = load_raw_dataset(job["raw_file"], config.NULL_TOKEN_LIST)
        clean_frame = job["cleaner"](job["raw_file"], job["clean_file"])
        profile = profile_dataset(raw_frame, clean_frame, job["target_column"],
                                  job["range_limits"])
        profile.update(job["detail_profiler"](raw_frame, clean_frame))
        profiles[job["dataset"]] = profile
        print(f"{job['dataset']:<28}{profile['rows_received']:>7} received -> "
              f"{profile['rows_kept']:>6} kept  ({profile['rows_removed']} removed)", flush=True)

    write_quality_report(profiles, config.DATA_QUALITY_REPORT_FILE)
    print(f"\nquality report written to {config.DATA_QUALITY_REPORT_FILE}")
    return profiles


if __name__ == "__main__":
    main()
