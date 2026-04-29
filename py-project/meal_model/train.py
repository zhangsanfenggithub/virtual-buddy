import json
import logging
import os
import pickle
import sys
import time
import random
import warnings

import numpy as np
import pandas as pd
from pgmpy.models import DiscreteBayesianNetwork
from pgmpy.estimators import BayesianEstimator, MaximumLikelihoodEstimator
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, classification_report

_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_here)
if _root not in sys.path:
    sys.path.insert(0, _root)

from meal_model import config

warnings.filterwarnings("ignore")

os.makedirs(os.path.dirname(config.LOG_PATH), exist_ok=True)
os.makedirs(os.path.dirname(config.MODEL_PATH), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(config.LOG_PATH, mode="w", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def _set_seed() -> None:
    random.seed(config.RANDOM_SEED)
    np.random.seed(config.RANDOM_SEED)


def _preprocess(df: pd.DataFrame) -> pd.DataFrame:
    df["time"] = pd.to_datetime(df["time"])
    df["carb_input"] = df["carb_input"].fillna(0.0)

    minute_of_day = df["time"].dt.hour * 60 + df["time"].dt.minute
    df["TC_5m"] = (minute_of_day // 5).astype(int)

    df["glucose"] = df["glucose"].ffill().bfill()
    df["GL_State"] = pd.cut(
        df["glucose"],
        bins=config.GLUCOSE_BINS,
        labels=config.GLUCOSE_LABELS,
    ).astype(int)

    df["last_meal_time"] = df.apply(
        lambda row: row["time"] if row["carb_input"] > 0 else pd.NaT, axis=1
    ).ffill()
    df["time_since_last_5m"] = (
        (df["time"] - df["last_meal_time"]).dt.total_seconds() / 300
    ).fillna(np.inf)
    df["TP_State"] = pd.cut(
        df["time_since_last_5m"],
        bins=config.TP_STATE_BINS,
        labels=config.TP_STATE_LABELS,
    ).astype(int)

    df["next_meal_time"] = df.apply(
        lambda row: row["time"] if row["carb_input"] > 0 else pd.NaT, axis=1
    ).bfill()
    df["next_meal_amount"] = df.apply(
        lambda row: row["carb_input"] if row["carb_input"] > 0 else pd.NA, axis=1
    ).bfill()
    df["time_until_next_5m"] = (
        df["next_meal_time"] - df["time"]
    ).dt.total_seconds() / 300

    df["GL_State_Prev"] = df["GL_State"].shift(1)

    df = df.dropna(subset=["time_until_next_5m", "GL_State_Prev"]).copy()
    df["TUN_State"] = pd.cut(
        df["time_until_next_5m"],
        bins=config.TUN_STATE_BINS,
        labels=config.TUN_STATE_LABELS,
    ).astype(int)
    df["SN_State"] = pd.cut(
        df["next_meal_amount"],
        bins=config.SN_STATE_BINS,
        labels=config.SN_STATE_LABELS,
    ).astype(int)

    for col in config.FEATURES:
        df[col] = df[col].astype(int)

    return df.reset_index(drop=True)


def _cross_validate(df: pd.DataFrame) -> list[dict]:
    all_cols = config.FEATURES + config.TARGETS
    tscv = TimeSeriesSplit(n_splits=config.CV_SPLITS)
    fold_metrics: list[dict] = []

    logger.info("=" * 60)
    logger.info(f"Starting {config.CV_SPLITS}-fold time-series cross-validation")
    logger.info(f"Total samples: {len(df)}")
    logger.info("=" * 60)

    for fold, (train_idx, test_idx) in enumerate(tscv.split(df), start=1):
        train_fold = df.iloc[train_idx]
        test_fold = df.iloc[test_idx]

        model = DiscreteBayesianNetwork(config.BN_EDGES)
        model.fit(
            train_fold[all_cols],
            estimator=BayesianEstimator,
            equivalent_sample_size=config.BAYESIAN_PRIOR_STRENGTH,
        )

        X_test = test_fold[config.FEATURES]
        y_tun_true = test_fold["TUN_State"].values
        y_sn_true = test_fold["SN_State"].values

        predictions = model.predict(X_test)
        acc_tun = accuracy_score(y_tun_true, predictions["TUN_State"])
        acc_sn = accuracy_score(y_sn_true, predictions["SN_State"])

        logger.info(f"Fold {fold}: train={len(train_fold)}, test={len(test_fold)}")
        logger.info(f"  TUN_State accuracy: {acc_tun:.4f}")
        logger.info(f"  SN_State accuracy:  {acc_sn:.4f}")

        tun_report = classification_report(
            y_tun_true, predictions["TUN_State"], output_dict=True, zero_division=0
        )
        sn_report = classification_report(
            y_sn_true, predictions["SN_State"], output_dict=True, zero_division=0
        )

        fold_metrics.append(
            {
                "fold": fold,
                "train_size": len(train_fold),
                "test_size": len(test_fold),
                "tun_accuracy": round(acc_tun, 4),
                "sn_accuracy": round(acc_sn, 4),
                "tun_weighted_f1": round(tun_report["weighted avg"]["f1-score"], 4),
                "sn_weighted_f1": round(sn_report["weighted avg"]["f1-score"], 4),
            }
        )

    return fold_metrics


def train():
    start_time = time.time()
    _set_seed()

    logger.info(f"Random seed: {config.RANDOM_SEED}")
    logger.info(f"Loading data: {config.DATA_PATH}")

    df = pd.read_csv(config.DATA_PATH, sep=config.DATA_SEPARATOR, parse_dates=["time"])
    df = df.sort_values("time").reset_index(drop=True)
    logger.info(f"Raw rows: {len(df)}, columns: {list(df.columns)}")

    train_df = _preprocess(df)
    logger.info(f"Training rows after preprocessing: {len(train_df)}")

    fold_metrics = _cross_validate(train_df)

    avg_tun = np.mean([m["tun_accuracy"] for m in fold_metrics])
    avg_sn = np.mean([m["sn_accuracy"] for m in fold_metrics])

    logger.info("=" * 60)
    logger.info(f"CV average: TUN_State={avg_tun:.4f}, SN_State={avg_sn:.4f}")
    logger.info("=" * 60)

    logger.info("Training final model on full dataset (MaximumLikelihoodEstimator) ...")
    all_cols = config.FEATURES + config.TARGETS
    model = DiscreteBayesianNetwork(config.BN_EDGES)
    model.fit(train_df[all_cols], estimator=MaximumLikelihoodEstimator)

    with open(config.MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    logger.info(f"Model saved → {config.MODEL_PATH}")

    elapsed = time.time() - start_time
    logger.info(f"Training completed in {elapsed:.2f}s ({elapsed/60:.1f} min)")

    metrics = {
        "random_seed": config.RANDOM_SEED,
        "cv_splits": config.CV_SPLITS,
        "bayesian_prior_strength": config.BAYESIAN_PRIOR_STRENGTH,
        "training_samples": len(train_df),
        "cv_avg_tun_accuracy": round(avg_tun, 4),
        "cv_avg_sn_accuracy": round(avg_sn, 4),
        "training_time_seconds": round(elapsed, 2),
        "folds": fold_metrics,
    }

    with open(config.METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    logger.info(f"Metrics saved → {config.METRICS_PATH}")

    return metrics


if __name__ == "__main__":
    train()
