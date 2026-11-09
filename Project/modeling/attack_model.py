"""The NLP model that reads one analyst note and names the attack type it describes."""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC

from modeling.model_evaluation import evaluate_text_classifier

ATTACK_ALGORITHM = "TF-IDF word and character n-grams with LinearSVC"


def train_attack_model(train_text, train_target, eval_text, eval_target):
    """Fit a text classifier that turns words into numbers itself, then score it."""
    model = Pipeline([
        ("vectorise", FeatureUnion([
            ("words", TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True,
                                      lowercase=True)),
            ("characters", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=3,
                                           sublinear_tf=True, lowercase=True)),
        ])),
        ("classify", LinearSVC(C=0.5, class_weight="balanced")),
    ])
    model.fit(train_text.astype(str), train_target.astype(str))
    scores = evaluate_text_classifier(model, train_text.astype(str), train_target.astype(str),
                                      eval_text.astype(str), eval_target.astype(str))
    return model, scores
