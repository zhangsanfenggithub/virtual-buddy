import os

# ============================================================
# Project root — derived from this file's location
# config.py lives in <root>/meal_model/, so parent = py-project root
# ============================================================
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ============================================================
# Paths — always absolute, works regardless of CWD
# ============================================================
DATA_PATH = os.path.join(_ROOT, "data", "HUPA0001P.csv")
DATA_SEPARATOR = ";"
MODEL_PATH = os.path.join(_ROOT, "meal_model", "model.pkl")
LOG_PATH = os.path.join(_ROOT, "meal_model", "training_log.txt")
METRICS_PATH = os.path.join(_ROOT, "meal_model", "training_metrics.json")

# ============================================================
# Data preprocessing — bin boundaries
# ============================================================
GLUCOSE_BINS = [-1, 70, 140, 999]
GLUCOSE_LABELS = [1, 2, 3]  # 1: low, 2: normal, 3: high

TP_STATE_BINS = [-1, 6, 24, 48, float("inf")]
TP_STATE_LABELS = [1, 2, 3, 4]  # 1:<30m, 2:30m-2h, 3:2h-4h, 4:>4h

TUN_STATE_BINS = [-0.1, 12, 36, float("inf")]
TUN_STATE_LABELS = [1, 2, 3]  # 1:<1h, 2:1h-3h, 3:>3h

SN_STATE_BINS = [0, 3, 999]
SN_STATE_LABELS = [1, 2]  # 1:snack, 2:normal meal

# ============================================================
# Bayesian network structure
# ============================================================
BN_EDGES = [
    ("GL_State_Prev", "GL_State"),
    ("TC_5m", "TUN_State"),
    ("GL_State", "TUN_State"),
    ("TP_State", "TUN_State"),
    ("TUN_State", "SN_State"),
]

# ============================================================
# Features & targets
# ============================================================
FEATURES = ["GL_State_Prev", "TC_5m", "GL_State", "TP_State"]
TARGETS = ["TUN_State", "SN_State"]

# ============================================================
# Training — cross-validation
# ============================================================
CV_SPLITS = 5
BAYESIAN_PRIOR_STRENGTH = 10  # equivalent_sample_size

# ============================================================
# Training — random seed
# ============================================================
RANDOM_SEED = 42

# ============================================================
# Prediction — thresholds
# ============================================================
MEAL_CUTOFF_1H = 0.55   # P(meal within 1 hour) > this → eat
MEAL_CUTOFF_3H = 0.75   # P(meal within 3 hours) > this → eat

# ============================================================
# Prediction — carbohydrate distributions
# ============================================================
CHO_OPTIONS_SNACK = [20, 30]         # grams, sampled when SN_State == 1
CHO_OPTIONS_NORMAL = [45, 60, 75]    # grams, sampled when SN_State == 2
