"""Saves and loads the models, their feature schemas and their scores."""

import json
import os

import joblib


def _ensure_folder(file_path):
    folder = os.path.dirname(file_path)
    if folder:
        os.makedirs(folder, exist_ok=True)


def save_model(model, file_path):
    """Save the whole fitted pipeline, preparation and estimator together."""
    _ensure_folder(file_path)
    joblib.dump(model, file_path)
    return file_path


def load_model(file_path):
    """Load a fitted pipeline, ready to score."""
    return joblib.load(file_path)


def save_feature_schema(feature_names, file_path):
    """Record the columns a model was fitted on, in order."""
    _ensure_folder(file_path)
    with open(file_path, "w", encoding="utf-8") as schema_file:
        json.dump([str(name) for name in feature_names], schema_file, indent=2)
        schema_file.write("\n")
    return file_path


def load_feature_schema(file_path):
    """Read back the columns a model expects, in the order they were saved."""
    with open(file_path, encoding="utf-8") as schema_file:
        return list(json.load(schema_file))


def save_metrics(metrics, file_path):
    """Write every model's scores as readable JSON."""
    _ensure_folder(file_path)
    with open(file_path, "w", encoding="utf-8") as metrics_file:
        json.dump(metrics, metrics_file, indent=2, default=str)
        metrics_file.write("\n")
    return file_path
