"""Scores a fitted model on data it did not learn from, and on the data it did."""

import numpy as np
from sklearn.metrics import (accuracy_score, f1_score, mean_absolute_error, precision_score,
                             r2_score, recall_score, roc_auc_score)


def _plain(value):
    return round(float(value), 4)


def evaluate_classifier(model, train_features, train_target, eval_features, eval_target):
    """ROC AUC on both sides, their gap, and the threshold scores on the held-out rows."""
    train_probability = model.predict_proba(train_features)[:, 1]
    eval_probability = model.predict_proba(eval_features)[:, 1]
    eval_predicted = model.predict(eval_features)
    roc_auc = roc_auc_score(eval_target, eval_probability)
    train_roc_auc = roc_auc_score(train_target, train_probability)
    return {
        "roc_auc": _plain(roc_auc),
        "train_roc_auc": _plain(train_roc_auc),
        "generalisation_gap": _plain(train_roc_auc - roc_auc),
        "accuracy": _plain(accuracy_score(eval_target, eval_predicted)),
        "precision": _plain(precision_score(eval_target, eval_predicted, zero_division=0)),
        "recall": _plain(recall_score(eval_target, eval_predicted, zero_division=0)),
        "f1": _plain(f1_score(eval_target, eval_predicted, zero_division=0)),
    }


def evaluate_regressor(model, train_features, train_target, eval_features, eval_target):
    """R squared on both sides, their gap, and the error against an average-answer baseline."""
    train_predicted = np.asarray(model.predict(train_features), dtype=float)
    eval_predicted = np.asarray(model.predict(eval_features), dtype=float)
    eval_answers = np.asarray(eval_target, dtype=float)
    baseline = float(np.mean(np.asarray(train_target, dtype=float)))
    r2 = r2_score(eval_answers, eval_predicted)
    train_r2 = r2_score(np.asarray(train_target, dtype=float), train_predicted)
    return {
        "r2": _plain(r2),
        "train_r2": _plain(train_r2),
        "generalisation_gap": _plain(train_r2 - r2),
        "mean_absolute_error": _plain(mean_absolute_error(eval_answers, eval_predicted)),
        "baseline_mean_absolute_error": _plain(np.mean(np.abs(eval_answers - baseline))),
        "lowest_prediction": _plain(eval_predicted.min()),
    }


def evaluate_text_classifier(model, train_text, train_target, eval_text, eval_target):
    """Macro F1 on both sides, their gap, and the score for every attack type held out."""
    train_predicted = model.predict(train_text)
    eval_predicted = model.predict(eval_text)
    macro_f1 = f1_score(eval_target, eval_predicted, average="macro", zero_division=0)
    train_macro_f1 = f1_score(train_target, train_predicted, average="macro", zero_division=0)
    labels = sorted({str(label) for label in eval_target})
    per_class = f1_score(eval_target, eval_predicted, labels=labels, average=None,
                         zero_division=0)
    return {
        "macro_f1": _plain(macro_f1),
        "train_macro_f1": _plain(train_macro_f1),
        "generalisation_gap": _plain(train_macro_f1 - macro_f1),
        "accuracy": _plain(accuracy_score(eval_target, eval_predicted)),
        "weighted_f1": _plain(f1_score(eval_target, eval_predicted, average="weighted",
                                       zero_division=0)),
        "per_class_f1": {label: _plain(score) for label, score in zip(labels, per_class)},
    }
