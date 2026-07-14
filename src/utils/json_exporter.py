import json
from pathlib import Path

from src.models.request_model import RequestModel


def export_request_to_json(
    request_data: RequestModel,
    output_file: str | Path,
) -> Path:
    output_path = Path(output_file)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        mode="w",
        encoding="utf-8",
    ) as file:
        json.dump(
            request_data.model_dump(),
            file,
            ensure_ascii=False,
            indent=2,
        )

    return output_path