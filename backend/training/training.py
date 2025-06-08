import os
import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix, ConfusionMatrixDisplay
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier, early_stopping  
from tqdm import tqdm
import warnings
warnings.filterwarnings("ignore")

# === Directories ===
MODEL_DIR = "../data/saved_models"
RESULTS_DIR = "../data/results"
CM_DIR = os.path.join(RESULTS_DIR, "confusion_matrices")
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(CM_DIR, exist_ok=True)

train_files = [    
    "train_embed_10.csv",
    "train_embed_30.csv",
    "train_embed_50.csv",
    "train_embed_smote_10.csv",
    "train_embed_smote_30.csv",
    "train_embed_smote_50.csv"
    ]

"""
    "train_embed_10.csv",
    "train_embed_30.csv",
    "train_embed_50.csv",
    "train_embed_smote_10.csv",
    "train_embed_smote_30.csv",
    "train_embed_smote_50.csv"
"""

val_df = pd.read_csv("../data/preprocessed/val_embed.csv")
test_df = pd.read_csv("../data/preprocessed/test_embed.csv")

X_val, y_val = val_df.drop(columns=["Label"]), val_df["Label"]
X_test, y_test = test_df.drop(columns=["Label"]), test_df["Label"]

for train_file in train_files:
    model_prefix = os.path.splitext(train_file)[0]
    print(f"\n\n=== Training on: {train_file} ===")
    train_df = pd.read_csv(f"../data/preprocessed/{train_file}")
    X_train, y_train = train_df.drop(columns=["Label"]), train_df["Label"]

    models = {
        'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
        'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
        'XGBoost': XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42),
        'LightGBM': LGBMClassifier(random_state=42)
    }

    eval_records = []

    print("\n--- Individual Model Evaluation (Validation Set) ---")
    for name, model in tqdm(models.items(), desc="Training models"):
        model_path = os.path.join(MODEL_DIR, f"{model_prefix}_{name.replace(' ', '_')}.joblib")
        if os.path.exists(model_path):
            model = joblib.load(model_path)
        else:
            if name == 'XGBoost':  
                model.fit(
                    X_train, y_train,
                    eval_set=[(X_val, y_val)],
                    verbose=False
                )
            elif name == 'LightGBM':  
                model.fit(
                    X_train, y_train,
                    eval_set=[(X_val, y_val)],
                    eval_metric='logloss',
                    callbacks=[early_stopping(stopping_rounds=10)]
                )
            else:
                model.fit(X_train, y_train)
            joblib.dump(model, model_path)

        preds = model.predict(X_val)
        acc = accuracy_score(y_val, preds)
        report = classification_report(y_val, preds, output_dict=True)
        cm = confusion_matrix(y_val, preds)

        disp = ConfusionMatrixDisplay(confusion_matrix=cm)
        disp.plot()
        plt.title(f"{name} - Confusion Matrix (Val)")
        plt.savefig(os.path.join(CM_DIR, f"{model_prefix}_{name.replace(' ', '_')}_val_cm.png"))
        plt.close()

        pd.DataFrame(cm).to_csv(os.path.join(CM_DIR, f"{model_prefix}_{name.replace(' ', '_')}_val_cm.csv"), index=False)

        eval_records.append({
            "Dataset": train_file,
            "Model": name,
            "Accuracy": acc,
            "Precision": report["weighted avg"]["precision"],
            "Recall": report["weighted avg"]["recall"],
            "F1-Score": report["weighted avg"]["f1-score"]
        })

    # === Voting Ensemble ===
    ensemble_path = os.path.join(MODEL_DIR, f"{model_prefix}_Ensemble.joblib")
    if os.path.exists(ensemble_path):
        ensemble = joblib.load(ensemble_path)
    else:
        ensemble = VotingClassifier(
            estimators=[
                ('lr', models['Logistic Regression']),
                ('rf', models['Random Forest']),
                ('xgb', models['XGBoost']),
                ('lgbm', models['LightGBM']),
            ],
            voting='soft'
        )
        ensemble.fit(X_train, y_train)
        joblib.dump(ensemble, ensemble_path)

    # Evaluate on test set
    test_preds = ensemble.predict(X_test)
    test_acc = accuracy_score(y_test, test_preds)
    test_report = classification_report(y_test, test_preds, output_dict=True)
    test_cm = confusion_matrix(y_test, test_preds)

    disp = ConfusionMatrixDisplay(confusion_matrix=test_cm)
    disp.plot()
    plt.title(f"Voting Ensemble - Confusion Matrix (Test)")
    plt.savefig(os.path.join(CM_DIR, f"{model_prefix}_Ensemble_test_cm.png"))
    plt.close()

    pd.DataFrame(test_cm).to_csv(os.path.join(CM_DIR, f"{model_prefix}_Ensemble_test_cm.csv"), index=False)

    eval_records.append({
        "Dataset": train_file,
        "Model": "Voting Ensemble",
        "Accuracy": test_acc,
        "Precision": test_report["weighted avg"]["precision"],
        "Recall": test_report["weighted avg"]["recall"],
        "F1-Score": test_report["weighted avg"]["f1-score"]
    })

    result_df = pd.DataFrame(eval_records)
    result_df.to_csv(os.path.join(RESULTS_DIR, f"{model_prefix}_results.csv"), index=False)
    print(f"Evaluation results saved to {os.path.join(RESULTS_DIR, f'{model_prefix}_results.csv')}")