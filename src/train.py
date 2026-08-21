import mlflow
import mlflow.sklearn
import pandas as pd
import yaml
import json
import joblib
import os
from sklearn.ensemble import (
    RandomForestClassifier,
    GradientBoostingClassifier,
    HistGradientBoostingClassifier,
    VotingClassifier,
)
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

EVAL_THRESHOLD = 0.68


def train(
    params: dict,
    data_path: str = "data/train_phase1.csv",
    eval_path: str = "data/eval.csv",
) -> float:
    """
    Huan luyen mo hinh va ghi nhan ket qua vao MLflow.

    Tham so:
        params     : dict chua cac sieu tham so cho mo hinh.
                      Co the co key "model_type": "random_forest" (mac dinh)
                      hoac "gradient_boosting" de doi thuat toan.
        data_path  : duong dan den file du lieu huan luyen.
        eval_path  : duong dan den file du lieu danh gia.

    Tra ve:
        accuracy (float): do chinh xac tren tap danh gia.
    """

    # TODO 1: Doc du lieu huan luyen va danh gia
    df_train = pd.read_csv(data_path)
    df_eval = pd.read_csv(eval_path)

    # TODO 2: Tach dac trung (X) va nhan (y)
    X_train = df_train.drop(columns=["target"])
    y_train = df_train["target"]
    X_eval = df_eval.drop(columns=["target"])
    y_eval = df_eval["target"]

    # Tach model_type ra khoi params truoc khi truyen vao model,
    # vi sklearn khong nhan tham so nay.
    model_params = dict(params)
    model_type = model_params.pop("model_type", "random_forest")

    with mlflow.start_run():

        # TODO 3: Ghi nhan cac sieu tham so (bao gom ca model_type de biet
        # lan chay nay dung thuat toan nao khi so sanh tren MLflow UI)
        mlflow.log_params(params)

        # TODO 4: Khoi tao va huan luyen mo hinh
        # random_state=42 de dam bao tinh tai tao
        if model_type == "gradient_boosting":
            model = GradientBoostingClassifier(**model_params, random_state=42)
        elif model_type == "hist_gradient_boosting":
            model = HistGradientBoostingClassifier(
                **model_params, random_state=42
            )
        elif model_type == "voting_ensemble":
            # Ket hop RandomForest + HistGradientBoosting bang soft voting.
            # model_params o day co the chua tien to "rf__" / "hgb__" de
            # tuy chinh tung mo hinh con, con lai dung mac dinh hop ly.
            rf_params = {
                k[len("rf__"):]: v
                for k, v in model_params.items()
                if k.startswith("rf__")
            }
            hgb_params = {
                k[len("hgb__"):]: v
                for k, v in model_params.items()
                if k.startswith("hgb__")
            }
            model = VotingClassifier(
                estimators=[
                    (
                        "rf",
                        RandomForestClassifier(
                            **rf_params, random_state=42, n_jobs=-1
                        ),
                    ),
                    (
                        "hgb",
                        HistGradientBoostingClassifier(
                            **hgb_params, random_state=42
                        ),
                    ),
                ],
                voting="soft",
            )
        elif model_type == "logistic_regression":
            model = make_pipeline(
                StandardScaler(),
                LogisticRegression(**model_params, random_state=42),
            )
        else:
            model = RandomForestClassifier(
                **model_params, random_state=42, n_jobs=-1
            )
        model.fit(X_train, y_train)

        # TODO 5: Du doan tren tap danh gia va tinh chi so
        preds = model.predict(X_eval)
        acc = float(accuracy_score(y_eval, preds))
        f1 = float(f1_score(y_eval, preds, average="weighted"))
        label_distribution = {
            str(label): float((y_train == label).mean())
            for label in (0, 1, 2)
        }
        rare_labels = [
            label for label, proportion in label_distribution.items()
            if proportion < 0.10
        ]
        if rare_labels:
            print(
                "WARNING: label distribution below 10% for classes: "
                + ", ".join(rare_labels)
            )

        # TODO 6: Ghi nhan chi so vao MLflow
        mlflow.log_metric("accuracy", acc)
        mlflow.log_metric("f1_score", f1)
        mlflow.sklearn.log_model(model, "model")

        # TODO 7: In ket qua ra man hinh
        print(f"[{model_type}] Accuracy: {acc:.4f} | F1: {f1:.4f}")

        # TODO 8: Luu metrics ra file outputs/metrics.json
        os.makedirs("outputs", exist_ok=True)
        with open("outputs/metrics.json", "w", encoding="utf-8") as f:
            json.dump(
                {
                    "accuracy": acc,
                    "f1_score": f1,
                    "label_distribution": label_distribution,
                },
                f,
            )

        report = classification_report(
            y_eval,
            preds,
            labels=[0, 1, 2],
            target_names=["thap", "trung_binh", "cao"],
            zero_division=0,
        )
        with open("outputs/report.txt", "w", encoding="utf-8") as report_file:
            report_file.write("Confusion matrix (rows=true, columns=predicted):\n")
            report_file.write(str(confusion_matrix(y_eval, preds, labels=[0, 1, 2])))
            report_file.write("\n\nPrecision and recall by class:\n")
            report_file.write(report)

        # TODO 9: Luu mo hinh ra file models/model.pkl
        os.makedirs("models", exist_ok=True)
        joblib.dump(model, "models/model.pkl")

    # TODO 10: Tra ve acc
    return acc


if __name__ == "__main__":
    with open("params.yaml") as f:
        params = yaml.safe_load(f)
    train(params)