"""The model that predicts whether the people whose data is involved are at high risk."""

from sklearn.ensemble import HistGradientBoostingClassifier

from config import config
from data_pipeline.feature_builder import build_native_category_pipeline
from modeling.model_evaluation import evaluate_classifier

HARM_ALGORITHM = "HistGradientBoostingClassifier (native categories)"


def train_harm_model(train_features, train_target, eval_features, eval_target):
    """Fit a gradient-boosted classifier on the training rows and score it on the held-out."""
    estimator = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.06,
                                               l2_regularization=1.0,
                                               random_state=config.RANDOM_SEED)
    model = build_native_category_pipeline(estimator, train_features)
    model.fit(train_features, train_target.astype(int))
    scores = evaluate_classifier(model, train_features, train_target.astype(int),
                                 eval_features, eval_target.astype(int))
    return model, scores
