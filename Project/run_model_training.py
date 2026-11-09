"""Entry point 3: train, save and score the harm, effort and attack models."""

from sklearn.model_selection import train_test_split

from config import config
from data_pipeline.dataset_loader import load_processed_dataset
from data_pipeline.feature_builder import build_model_inputs
from modeling.attack_model import ATTACK_ALGORITHM, train_attack_model
from modeling.effort_model import EFFORT_ALGORITHM, train_effort_model
from modeling.harm_model import HARM_ALGORITHM, train_harm_model
from modeling.model_registry import save_feature_schema, save_metrics, save_model


def _train_tabular(train_file, eval_file, identifiers, target, trainer):
    train_features, train_target = build_model_inputs(load_processed_dataset(train_file),
                                                      identifiers, target)
    eval_features, eval_target = build_model_inputs(load_processed_dataset(eval_file),
                                                    identifiers, target)
    model, scores = trainer(train_features, train_target, eval_features, eval_target)
    return model, scores, list(train_features.columns)


def main():
    """Train all three models; a model below its minimum is reported, never hidden."""
    print("training three models")
    metrics = {}

    harm, harm_scores, harm_columns = _train_tabular(
        config.CLEAN_INCIDENTS_TRAIN_FILE, config.CLEAN_INCIDENTS_EVAL_FILE,
        config.INCIDENT_IDENTIFIER_COLUMNS, config.INCIDENT_TARGET_COLUMN, train_harm_model)
    save_model(harm, config.HARM_MODEL_FILE)
    save_feature_schema(harm_columns, config.HARM_SCHEMA_FILE)
    metrics["harm"] = {"algorithm": HARM_ALGORITHM, "metric": "roc_auc",
                       "minimum_required": config.MINIMUM_HARM_ROC_AUC,
                       "minimum_met": harm_scores["roc_auc"] >= config.MINIMUM_HARM_ROC_AUC,
                       "scores": harm_scores}
    print(f"  harm    {HARM_ALGORITHM:<55} eval ROC AUC {harm_scores['roc_auc']:.4f}  "
          f"(train {harm_scores['train_roc_auc']:.4f}, gap {harm_scores['generalisation_gap']:+.4f})",
          flush=True)

    effort, effort_scores, effort_columns = _train_tabular(
        config.CLEAN_EFFORT_TRAIN_FILE, config.CLEAN_EFFORT_EVAL_FILE,
        config.EFFORT_IDENTIFIER_COLUMNS, config.EFFORT_TARGET_COLUMN, train_effort_model)
    save_model(effort, config.EFFORT_MODEL_FILE)
    save_feature_schema(effort_columns, config.EFFORT_SCHEMA_FILE)
    metrics["effort"] = {"algorithm": EFFORT_ALGORITHM, "metric": "r2",
                         "minimum_required": config.MINIMUM_EFFORT_R2,
                         "minimum_met": effort_scores["r2"] >= config.MINIMUM_EFFORT_R2,
                         "scores": effort_scores}
    print(f"  effort  {EFFORT_ALGORITHM:<55} eval R2 {effort_scores['r2']:.4f}  "
          f"MAE {effort_scores['mean_absolute_error']:.2f} h  (train {effort_scores['train_r2']:.4f}, "
          f"gap {effort_scores['generalisation_gap']:+.4f})", flush=True)

    notes = load_processed_dataset(config.CLEAN_INCIDENT_NOTES_FILE)
    train_text, eval_text, train_target, eval_target = train_test_split(
        notes[config.NOTE_TEXT_COLUMN], notes[config.NOTE_TARGET_COLUMN],
        test_size=config.VALIDATION_SPLIT_RATIO, stratify=notes[config.NOTE_TARGET_COLUMN],
        random_state=config.RANDOM_SEED)
    attack, attack_scores = train_attack_model(train_text, train_target, eval_text, eval_target)
    save_model(attack, config.ATTACK_MODEL_FILE)
    metrics["attack"] = {"algorithm": ATTACK_ALGORITHM, "metric": "macro_f1",
                         "minimum_required": config.MINIMUM_ATTACK_MACRO_F1,
                         "minimum_met": attack_scores["macro_f1"] >= config.MINIMUM_ATTACK_MACRO_F1,
                         "scores": attack_scores}
    print(f"  attack  {ATTACK_ALGORITHM:<55} eval macro F1 {attack_scores['macro_f1']:.4f}  "
          f"(train {attack_scores['train_macro_f1']:.4f}, "
          f"gap {attack_scores['generalisation_gap']:+.4f})", flush=True)

    save_metrics(metrics, config.MODEL_METRICS_FILE)
    print(f"\nmetrics written to {config.MODEL_METRICS_FILE}")
    short = [name for name, entry in metrics.items() if not entry["minimum_met"]]
    if short:
        print("below the minimum config sets: " + ", ".join(short))
    else:
        print("every model is above the minimum config sets for it")
    return metrics


if __name__ == "__main__":
    main()
