"""Reproducible loader for the official BCIE approvals resource."""

from io import BytesIO
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd
import requests


class CKANLoader:
    REQUIRED_COLUMNS = {
        "PAIS",
        "ANIO_APROBACION",
        "SECTOR_INSTITUCIONAL",
        "MONTO_BRUTO_USD",
        "CANTIDAD_APROBACIONES",
    }

    def __init__(
        self,
        base_url="https://datosabiertos.bcie.org",
        resource_id="ce88a753-57f5-4266-a57e-394600c8435d",
        download_url=None,
    ):
        self.base_url = base_url.rstrip("/")
        self.resource_id = resource_id
        self.download_url = download_url or (
            f"{self.base_url}/dataset/45876cb4-d8b8-4635-b999-0df1c19b831a/"
            f"resource/{resource_id}/download/aprobaciones-prestamos.csv"
        )
        self.last_metadata = None
        self.last_bytes = None

    def _validate(self, df):
        missing = self.REQUIRED_COLUMNS.difference(df.columns)
        if missing:
            raise ValueError(f"BCIE resource is missing required columns: {sorted(missing)}")
        if df.empty:
            raise ValueError("BCIE resource returned no records")
        return df

    def _resource_metadata(self, session):
        url = f"{self.base_url}/api/3/action/package_show"
        response = session.get(url, params={"id": "prestamos"}, timeout=60)
        response.raise_for_status()
        payload = response.json()
        if not payload.get("success"):
            raise RuntimeError("CKAN package_show did not return success")
        resource = next(
            item for item in payload["result"]["resources"]
            if item["id"] == self.resource_id
        )
        return {
            "resource_id": self.resource_id,
            "resource_url": self.download_url,
            "resource_last_modified": resource.get("last_modified"),
            "metadata_modified": resource.get("metadata_modified"),
            "ckan_hash": resource.get("hash"),
            "ckan_size": resource.get("size"),
        }

    def fetch_data(self, source_path=None):
        """Load a frozen CSV or download the authoritative uploaded CSV.

        The uploaded CSV is preferred over ``datastore_search`` because CKAN marks
        whether the datastore mirrors every source record independently.
        """
        if source_path:
            path = Path(source_path)
            raw = path.read_bytes()
            source = str(path.resolve())
            metadata = {"source_path": source, "resource_id": self.resource_id}
        else:
            print("--- Starting Data Extraction (official CSV) ---")
            session = requests.Session()
            session.headers.update({"User-Agent": "bcie-research-client/2.0"})
            response = session.get(self.download_url, timeout=60)
            response.raise_for_status()
            raw = response.content
            source = self.download_url
            metadata = self._resource_metadata(session)

        df = self._validate(pd.read_csv(BytesIO(raw)))
        metadata.update({
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            "source": source,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
            "rows": int(len(df)),
            "columns": list(df.columns),
            "min_year": int(pd.to_numeric(df["ANIO_APROBACION"]).min()),
            "max_year": int(pd.to_numeric(df["ANIO_APROBACION"]).max()),
        })
        self.last_bytes = raw
        self.last_metadata = metadata
        return df

    def save_snapshot(self, output_dir, stem="aprobaciones_prestamos_bcie"):
        if self.last_bytes is None or self.last_metadata is None:
            raise RuntimeError("Call fetch_data() before save_snapshot()")
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        csv_path = output / f"{stem}.csv"
        metadata_path = output / f"{stem}_metadata.json"
        csv_path.write_bytes(self.last_bytes)
        metadata_path.write_text(
            json.dumps(self.last_metadata, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return csv_path, metadata_path
