"""Turns a cleaned table into something a model can be fitted on."""

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, OrdinalEncoder

from config import config


def build_model_inputs(dataframe, identifier_columns, target_column):
    """Split a table into the inputs a model may learn from and the answer it predicts."""
    excluded = set(identifier_columns) | {target_column}
    feature_columns = [name for name in dataframe.columns if name not in excluded]
    return dataframe[feature_columns].copy(), dataframe[target_column].copy()


def split_column_kinds(feature_frame):
    """Numeric and category columns, told apart from the frame itself."""
    numeric = [name for name in feature_frame.columns
               if pd.api.types.is_numeric_dtype(feature_frame[name])
               and not pd.api.types.is_bool_dtype(feature_frame[name])]
    categorical = [name for name in feature_frame.columns if name not in numeric]
    return numeric, categorical


def as_text(values):
    """Category values as plain text, with gaps kept as gaps for the imputer."""
    frame = pd.DataFrame(values).astype(object)
    return frame.where(frame.notna(), np.nan).to_numpy(dtype=object)


def as_number(values):
    """Measured values as floats, with anything unreadable as a gap."""
    frame = pd.DataFrame(values)
    return frame.apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)


def _numeric_branch():
    return Pipeline([
        ("to_number", FunctionTransformer(as_number, feature_names_out="one-to-one")),
        ("fill", SimpleImputer(strategy="median")),
    ])


def build_model_pipeline(estimator, feature_frame):
    """Preparation (imputation and one-hot encoding) and the estimator, as one object."""
    numeric, categorical = split_column_kinds(feature_frame)
    preparation = ColumnTransformer([
        ("numeric", _numeric_branch(), numeric),
        ("category", Pipeline([
            ("to_text", FunctionTransformer(as_text, feature_names_out="one-to-one")),
            ("fill", SimpleImputer(strategy="constant",
                                   fill_value=config.UNKNOWN_CATEGORY_VALUE)),
            ("encode", OneHotEncoder(handle_unknown="ignore")),
        ]), categorical),
    ], remainder="drop")
    return Pipeline([("prepare", preparation), ("model", estimator)])


def build_native_category_pipeline(estimator, feature_frame):
    """Preparation (imputation and ordinal codes) for an estimator that reads categories."""
    numeric, categorical = split_column_kinds(feature_frame)
    preparation = ColumnTransformer([
        ("numeric", _numeric_branch(), numeric),
        ("category", Pipeline([
            ("to_text", FunctionTransformer(as_text, feature_names_out="one-to-one")),
            ("fill", SimpleImputer(strategy="constant",
                                   fill_value=config.UNKNOWN_CATEGORY_VALUE)),
            ("encode", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1,
                                      dtype=float)),
        ]), categorical),
    ], remainder="drop")
    category_mask = [False] * len(numeric) + [True] * len(categorical)
    if "categorical_features" in estimator.get_params():
        estimator.set_params(categorical_features=category_mask)
    return Pipeline([("prepare", preparation), ("model", estimator)])
