"""Xác minh nguồn công bố và tuyển bộ 150 spam/50 ham có trích dẫn.

Không thay file gốc, nhãn hoặc các split đã bàn giao.
"""
from pathlib import Path
import hashlib
import io
import json
import sys
import urllib.request

import pandas as pd
from privacy import redact

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ML = ROOT / "traditional_ml/TV2_hoc_may"
REPOSITORY = "trannguyenthaituan251209/vietnamese_sms_dataset"
COMMIT = "464a028878023598e16f2f344ee36f7d5d74257f"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def attach_provenance(manifest):
    path = HERE / "reports/source_verification.json"
    if path.exists():
        report = json.loads(path.read_text(encoding="utf-8"))
        verified = {item["local_file"]: item for item in report["verified_files"]}
        for source in manifest["sources"]:
            item = verified[source["path"]]
            if source["sha256"] != item["local_sha256"]:
                raise ValueError("Nguồn đã thay đổi; cần xác minh lại")
            source["origin"] = item["upstream_url"]
        manifest["source_verification_report"] = "reports/source_verification.json"
        manifest["source_validation"] = "Khớp nguồn công bố sau chuẩn hóa CRLF; license theo README nhà công bố. Chưa kiểm toán độc lập quá trình thu thập."
    return manifest


def main():
    report_dir = HERE / "reports"
    report_dir.mkdir(exist_ok=True)
    expected_hashes = {"train.csv": "d2e2be037bd7f1f63979c1dd8ec2a2c44c4247bb7730467b37976c1a93936732",
                       "test.csv": "1b71ae4f9af49e319612e608eb9154ff26eb23981294ab1a89887d078e97ec10"}
    frames, verified = [], []
    for upstream, local_name, split in (("train.csv", "train_goc.csv", "train"),
                                        ("test.csv", "test_goc.csv", "test")):
        url = f"https://raw.githubusercontent.com/{REPOSITORY}/{COMMIT}/{upstream}"
        with urllib.request.urlopen(url, timeout=30) as response:
            data = response.read()
        if sha(data) != expected_hashes[upstream]:
            raise ValueError("Nguồn tải về không khớp bản đã cố định")
        original = (ML / "data/raw" / local_name).read_bytes()
        if data.replace(b"\r\n", b"\n") != original.replace(b"\r\n", b"\n"):
            raise ValueError(f"Nội dung nguồn khác dữ liệu nhóm: {local_name}")
        frame = pd.read_csv(io.BytesIO(data))
        frame["source_id"] = [f"vi-{split}-{i:05d}" for i in range(len(frame))]
        frame["source_csv"] = upstream
        frame["source_row"] = range(2, len(frame) + 2)  # Bản ghi CSV, tính cả hàng tiêu đề.
        frame["text"] = frame.message.map(redact)
        frame["y"] = frame.label.astype(int)
        frames.append(frame)
        verified.append({"upstream_url": url, "local_file": str((ML / "data/raw" / local_name).relative_to(ROOT)).replace("\\", "/"),
                         "upstream_sha256": sha(data), "local_sha256": sha(original),
                         "comparison": "exact bytes after CRLF-to-LF normalization", "rows": len(frame)})
    all_data = pd.concat(frames, ignore_index=True)
    # Chỉ tuyển các bản ghi đã qua bước QA TV1; giữ nguồn từng tin.
    eligible = pd.concat([pd.read_csv(HERE / f"data/{split}_clean.csv") for split in ("train", "test")])
    all_data = all_data[all_data.source_id.isin(eligible.source_id)].drop_duplicates("text")
    sample = pd.concat([all_data[all_data.y == 1].sample(150, random_state=42),
                        all_data[all_data.y == 0].sample(50, random_state=42)]).reset_index(drop=True)
    sample["source_repository"] = f"https://github.com/{REPOSITORY}"
    sample["source_commit"] = COMMIT
    sample["source_license"] = "CC-BY-4.0 (publisher README)"
    sample_path = report_dir / "vi_sourced_sample_150spam_50ham.csv"
    sample[["source_id", "text", "y", "source_csv", "source_row", "source_repository",
            "source_commit", "source_license"]].to_csv(sample_path, index=False)
    report = {"repository": f"https://github.com/{REPOSITORY}", "commit": COMMIT,
              "readme": f"https://github.com/{REPOSITORY}/blob/{COMMIT}/README.md",
              "license_declared_by_publisher": "Creative Commons Attribution 4.0 International",
              "authors": ["Tran Nguyen Thai Tuan", "Le Hoang Khang", "Nguyen Minh Tai", "Nguyen Van Thang", "Mai Hoang Dinh"],
              "verified_files": verified,
              "sample": {"path": sample_path.name, "spam": 150, "ham": 50,
                         "sha256": sha(sample_path.read_bytes()), "seed": 42,
                         "independent_of_vietnamese_train_test": False},
              "attribution": "Vietnamese SMS Dataset with Quality Assurance, Tran Nguyen Thai Tuan et al., publisher repository (2026).",
              "modifications": "Subset selection, Unicode/whitespace normalization and extra identifier redaction; original labels unchanged.",
              "collection_note": "Collected from a public published corpus; not newly solicited messages and not a new independent holdout.",
              "verification_limit": "File identity and the publisher license statement verified; contributor consent/ethics claims not independently audited."}
    (report_dir / "source_verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest_path = HERE / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_path.write_text(json.dumps(attach_provenance(manifest), ensure_ascii=False, indent=2), encoding="utf-8")
    print("Verified source identity. Curated 150 spam + 50 ham; original splits unchanged.")


if __name__ == "__main__":
    main()
