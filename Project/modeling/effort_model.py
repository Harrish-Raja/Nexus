"""The model that estimates how many analyst hours containment and fact-finding will take."""

import numpy as np
from sklearn.compose import TransformedTargetRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.pipeline import Pipeline

from config import config
from data_pipeline.feature_builder import build_native_category_pipeline
from modeling.model_evaluation import evaluate_regressor

EFFORT_ALGORITHM = "HistGradientBoostingRegressor on log hours (native categories)"


def train_effort_model(train_features, train_target, eval_features, eval_target):
    """Fit a gradient-boosted regressor on log hours, so every estimate is positive."""
    booster = HistGradientBoostingRegressor(max_iter=400, learning_rate=0.06,
                                            random_state=config.RANDOM_SEED)
    prepared = build_native_category_pipeline(booster, train_features)
    model = Pipeline([
        ("prepare", prepared.named_steps["prepare"]),
        ("model", TransformedTargetRegressor(regressor=prepared.named_steps["model"],
                                             func=np.log, inverse_func=np.exp)),
    ])
    model.fit(train_features, train_target.astype(float))
    scores = evaluate_regressor(model, train_features, train_target, eval_features, eval_target)
    return model, scores
