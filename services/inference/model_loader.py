import logging
import mlflow
import mlflow.lightgbm
from config import MLFLOW_TRACKING_URI

log = logging.getLogger(__name__)

_model_cache: dict = {}


def load_model(run_name: str = "LightGBM"):
    """Load the latest MLflow run for a given model name. Cached in memory."""
    if run_name in _model_cache:
        return _model_cache[run_name]

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    client = mlflow.tracking.MlflowClient()

    experiment = client.get_experiment_by_name("finsignal")
    if not experiment:
        raise RuntimeError("MLflow experiment 'finsignal' not found — run training first")

    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        filter_string=f"tags.mlflow.runName = '{run_name}'",
        order_by=["start_time DESC"],
        max_results=1,
    )
    if not runs:
        raise RuntimeError(f"No runs found for model '{run_name}'")

    run = runs[0]
    model_uri = f"runs:/{run.info.run_id}/model"
    model = mlflow.lightgbm.load_model(model_uri)
    _model_cache[run_name] = (model, run.info.run_id)
    log.info(f"Loaded {run_name} from run {run.info.run_id}")
    return model, run.info.run_id


def get_run_metrics(run_name: str) -> dict:
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    client = mlflow.tracking.MlflowClient()
    experiment = client.get_experiment_by_name("finsignal")
    if not experiment:
        return {}
    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        filter_string=f"tags.mlflow.runName = '{run_name}'",
        order_by=["start_time DESC"],
        max_results=1,
    )
    return runs[0].data.metrics if runs else {}
