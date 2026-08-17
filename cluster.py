#!/usr/bin/env python3
"""cluster_hamer_frames_maha.py

Global finger‑angle hand‑shape clustering with Mahalanobis support
=================================================================
This version clusters hand shapes based on **finger‑angle vectors** and lets you
measure distance in three different ways:

1. Pure Euclidean (legacy)
2. Pure Mahalanobis (covariance‑aware)
3. A weighted combination of the two

The Mahalanobis option whitens the feature space via the inverse covariance, so
classical algorithms like K‑means (which assume Euclidean space) can be run
without modification while still respecting the true correlated geometry of the
hand.

Noise filtering can likewise use a Mahalanobis cutoff.

Multithreading is retained for speed on large datasets.
"""

import argparse
import json
import warnings
from pathlib import Path
from typing import Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
import time

import numpy as np
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.neighbors import LocalOutlierFactor
from sklearn.ensemble import IsolationForest

# New: SciPy for Mahalanobis / whitening
import scipy.linalg as la
from scipy.spatial.distance import mahalanobis

# Progress bar
try:
    from tqdm import tqdm
    _HAVE_TQDM = True
except ImportError:
    _HAVE_TQDM = False
    print("Install tqdm for progress bars: pip install tqdm")

# Optional – HDBSCAN (pip install hdbscan)
try:
    from hdbscan import HDBSCAN  # type: ignore
    _HAVE_HDBSCAN = True
except ImportError:
    _HAVE_HDBSCAN = False

# Hand keypoint indices for each finger
FINGER_INDICES = {
    'thumb': [0, 1, 2, 3, 4],
    'index': [0, 5, 6, 7, 8],
    'middle': [0, 9, 10, 11, 12],
    'ring': [0, 13, 14, 15, 16],
    'pinky': [0, 17, 18, 19, 20]
}

# ---------------------------------------------------------------------------
# IO helpers
# ---------------------------------------------------------------------------

def load_hamer(path: Path) -> Dict[str, List]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

# ---------------------------------------------------------------------------
# Angle calculation functions
# ---------------------------------------------------------------------------

def calculate_angle_between_vectors(v1: np.ndarray, v2: np.ndarray) -> float:
    """Angle between two 3‑D vectors in **radians**."""
    v1_norm = v1 / (np.linalg.norm(v1) + 1e-8)
    v2_norm = v2 / (np.linalg.norm(v2) + 1e-8)
    cos_angle = np.clip(np.dot(v1_norm, v2_norm), -1.0, 1.0)
    return np.arccos(cos_angle)


def extract_finger_angles(keypoints: np.ndarray) -> np.ndarray:
    """Convert 21×3 hand keypoints to a 16‑D finger‑angle vector."""
    if keypoints.shape != (21, 3):
        return np.full(16, np.nan)

    angles = []

    for indices in FINGER_INDICES.values():
        finger_points = keypoints[indices]
        for i in range(len(indices) - 2):
            v1 = finger_points[i + 1] - finger_points[i]
            v2 = finger_points[i + 2] - finger_points[i + 1]
            angles.append(calculate_angle_between_vectors(v1, v2))

    # Thumb abduction (thumb tip – wrist vs index tip – wrist)
    thumb_vec = keypoints[4] - keypoints[0]
    index_vec = keypoints[8] - keypoints[0]
    angles.append(calculate_angle_between_vectors(thumb_vec, index_vec))

    return np.array(angles)


def hand_frames_to_angle_features(frames: List) -> np.ndarray:
    feat_list: List[np.ndarray] = []
    for frame in frames:
        if not frame:
            continue
        pts = np.asarray(frame[0], dtype=float)
        if pts.shape != (21, 3):
            continue
        angles = extract_finger_angles(pts)
        if np.any(np.isnan(angles)):
            continue
        feat_list.append(angles)
    return np.stack(feat_list, axis=0) if feat_list else np.empty((0, 16))

# ---------------------------------------------------------------------------
# NEW – root–translated key-point features
# ---------------------------------------------------------------------------

def keypoints_to_root_features(frames: List) -> np.ndarray:
    """
    Convert a list of per-frame key-point lists into an N×60 matrix.

    • Each frame must contain one 21×3 numpy array.  
    • The wrist (index 0) is translated to the origin, then **omitted**
      so the resulting vector is 20 key-points × 3 coords = 60 dims.
    """
    feat_list: List[np.ndarray] = []
    for frame in frames:
        if not frame:
            continue
        pts = np.asarray(frame[0], dtype=float)        # (21,3)
        if pts.shape != (21, 3):
            continue
        pts_rel = pts - pts[0]                         # translate wrist→0
        vec = pts_rel[1:].reshape(-1)                  # drop wrist, flatten
        feat_list.append(vec)
    return np.stack(feat_list, axis=0) if feat_list else np.empty((0, 60))

# ---------------------------------------------------------------------------
# Mahalanobis helpers
# ---------------------------------------------------------------------------

def whiten_for_mahalanobis(feats: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return whitened features Xw, column mean μ, and whitening matrix W.

    Mahalanobis(x, y | Σ) == || (x − y) @ W ||₂
    with W = chol(Σ^{-1}).
    """
    if feats.shape[0] < 3:
        raise ValueError("Need at least 3 samples to compute covariance")
    mu = feats.mean(axis=0)
    cov = np.cov(feats, rowvar=False)
    VI = la.pinvh(cov)
    W = la.cholesky(VI, lower=False)  # upper‑triangular
    Xw = (feats - mu) @ W
    return Xw, mu, W

# ---------------------------------------------------------------------------
# Parallel processing helpers
# ---------------------------------------------------------------------------

def process_single_file(file_path: Path, feature_extractor) -> Tuple[np.ndarray, List[Dict], np.ndarray, List[Dict]]:
    try:
        data = load_hamer(file_path)

        feats_l = feats_r = np.empty((0, 16 if feature_extractor == hand_frames_to_angle_features else 60))
        meta_l = meta_r = []

        for hk, hand_data in [("l_hand", data.get("l_hand", [])), ("r_hand", data.get("r_hand", []))]:
            if not hand_data:
                continue
            fmat = feature_extractor(hand_data)
            metadata = [{"file": file_path.name, "frame": i} for i in range(fmat.shape[0])]
            if hk == "l_hand":
                feats_l, meta_l = fmat, metadata
            else:
                feats_r, meta_r = fmat, metadata
        return feats_l, meta_l, feats_r, meta_r

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        empty_dims = 16 if feature_extractor == hand_frames_to_angle_features else 60
        return np.empty((0, empty_dims)), [], np.empty((0, empty_dims)), []


def parallel_noise_filter(hand_data: Tuple[str, np.ndarray, List[Dict]], method: str, contamination: float, seed: int) -> Tuple[str, np.ndarray, List[Dict]]:
    hand_name, feats, meta = hand_data
    filtered_feats, filtered_meta = filter_noise(feats, meta, method, contamination, seed)
    return hand_name, filtered_feats, filtered_meta


def parallel_clustering(hand_data: Tuple[str, np.ndarray, List[Dict]], method: str, k: int, seed: int, distance: str, alpha: float) -> Tuple[str, List[Dict]]:
    hand_name, feats, meta = hand_data
    labels, cents = cluster_features(feats, method, k, seed, distance, alpha)
    clusters = build_clusters_json(labels, cents, meta)
    return hand_name, clusters

# ---------------------------------------------------------------------------
# Noise filtering
# ---------------------------------------------------------------------------

def filter_noise(feats: np.ndarray, meta: List[Dict], method: str = "lof", contamination: float = 0.05, seed: int = 0) -> Tuple[np.ndarray, List[Dict]]:
    if feats.size == 0:
        return feats, meta

    if method == "lof":
        lof = LocalOutlierFactor(n_neighbors=20, contamination=contamination)
        mask = lof.fit_predict(feats) == 1  # 1=inlier
    elif method == "isoforest":
        iso = IsolationForest(contamination=contamination, random_state=seed, n_estimators=100).fit(feats)
        mask = iso.predict(feats) == 1
    elif method == "maha":
        if feats.shape[0] < 3:
            mask = np.ones(len(feats), dtype=bool)
        else:
            mu = feats.mean(0)
            VI = la.pinv(np.cov(feats, rowvar=False))
            d = np.array([mahalanobis(f, mu, VI) for f in feats])
            thresh = np.percentile(d, 100 * (1 - contamination))
            mask = d <= thresh
    elif method == "none":
        mask = np.ones(len(feats), dtype=bool)
    else:
        raise ValueError("Unknown noise‑filter method: " + method)

    kept = mask.sum()
    removed = len(mask) - kept
    if removed:
        print(f"  noise filter removed {removed} of {len(mask)} frames ({removed/len(mask):.1%})")
    feats_f = feats[mask]
    meta_f = [m for m, ok in zip(meta, mask) if ok]
    return feats_f, meta_f

# ---------------------------------------------------------------------------
# Clustering helpers
# ---------------------------------------------------------------------------

def cluster_features(feats: np.ndarray, method: str = "kmeans", k: int = 10, seed: int = 0, distance: str = "euclidean", alpha: float = 0.5) -> Tuple[np.ndarray, np.ndarray]:
    """Return (labels, centroids) for the chosen algorithm and distance metric."""
    if feats.size == 0:
        return np.array([]), np.empty((0, feats.shape[1]))

    # ----------------------------
    # Build feature space
    # ----------------------------
    if distance == "euclidean":
        X = feats
    elif distance == "mahalanobis":
        X, mu, W = whiten_for_mahalanobis(feats)
    elif distance == "combined":
        X_euc = (feats - feats.mean(0)) / (feats.std(0) + 1e-8)
        X_mah, mu, W = whiten_for_mahalanobis(feats)
        X_mah = (X_mah - X_mah.mean(0)) / (X_mah.std(0) + 1e-8)
        X = alpha * X_euc + (1.0 - alpha) * X_mah
    else:
        raise ValueError("Unsupported distance metric: " + distance)

    # ----------------------------
    # Run clustering algorithm
    # ----------------------------
    method = method.lower()

    if method == "kmeans":
        model = KMeans(n_clusters=k, n_init=10, random_state=seed, algorithm="lloyd").fit(X)
        labels = model.labels_
        if distance == "mahalanobis":
            cents = (model.cluster_centers_ @ la.inv(W)) + mu
        elif distance == "combined":
            cents = None  # Centroid back‑projection is ambiguous in combo space
        else:
            cents = model.cluster_centers_
    elif method == "dbscan":
        if distance == "euclidean" or distance == "combined":
            model = DBSCAN(eps=0.5, min_samples=5, n_jobs=-1).fit(X)
        else:  # pure Mahalanobis
            VI = la.inv(np.cov(feats, rowvar=False))
            maha_metric = lambda u, v: mahalanobis(u, v, VI)
            model = DBSCAN(eps=1.0, min_samples=5, metric=maha_metric, n_jobs=-1).fit(feats)
        labels = model.labels_
        cents = _centroids_from_labels(feats, labels)
    elif method == "agglom":
        model = AgglomerativeClustering(n_clusters=k, linkage="ward").fit(X)
        labels = model.labels_
        cents = _centroids_from_labels(feats, labels)
    elif method == "hdbscan":
        if not _HAVE_HDBSCAN:
            raise SystemExit("hdbscan package not installed – `pip install hdbscan` to use this method")
        model = HDBSCAN(min_cluster_size=15, prediction_data=False).fit(X)
        labels = model.labels_
        cents = _centroids_from_labels(feats, labels)
    else:
        raise ValueError("Unknown clustering method: " + method)

    if cents is None:
        cents = _centroids_from_labels(feats, labels)

    return labels, cents


def _centroids_from_labels(feats: np.ndarray, labels: np.ndarray) -> np.ndarray:
    cents = [feats[labels == lab].mean(axis=0) for lab in sorted(set(labels)) if lab != -1]
    return np.vstack(cents) if cents else np.empty((0, feats.shape[1]))

# ---------------------------------------------------------------------------
# Pipeline helpers
# ---------------------------------------------------------------------------

def ingest_files(files: List[Path], max_workers: int = 4, feature_extractor=hand_frames_to_angle_features) -> Tuple[np.ndarray, List[Dict], np.ndarray, List[Dict]]:
    print(f"Processing {len(files)} files with {max_workers} threads…")
    start_time = time.time()

    all_feats_l, all_feats_r = [], []
    all_meta_l, all_meta_r = [], []

    pbar = tqdm(total=len(files), desc="Processing files", unit="files") if _HAVE_TQDM else None

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {executor.submit(process_single_file, f, feature_extractor): f for f in files}
        for future in as_completed(future_to_file):
            file_path = future_to_file[future]
            try:
                feats_l, meta_l, feats_r, meta_r = future.result()
                if feats_l.size > 0:
                    all_feats_l.append(feats_l)
                    all_meta_l.extend(meta_l)
                if feats_r.size > 0:
                    all_feats_r.append(feats_r)
                    all_meta_r.extend(meta_r)
            except Exception as e:
                print(f"Failed to process {file_path}: {e}")
            if pbar:
                pbar.update(1)
    if pbar:
        pbar.close()

    expected_dims = 16 if feature_extractor == hand_frames_to_angle_features else 60
    feats_l = np.concatenate(all_feats_l, axis=0) if all_feats_l else np.empty((0, expected_dims))
    feats_r = np.concatenate(all_feats_r, axis=0) if all_feats_r else np.empty((0, expected_dims))

    elapsed = time.time() - start_time
    print(f"File processing completed in {elapsed:.1f}s")
    print(f"Loaded {len(all_meta_l)} left‑hand frames, {len(all_meta_r)} right‑hand frames")

    return feats_l, all_meta_l, feats_r, all_meta_r


def build_clusters_json(labels: np.ndarray, cents: np.ndarray, meta: List[Dict]) -> List[Dict]:
    clusters: Dict[int, List[int]] = {}
    for idx, lab in enumerate(labels):
        if lab == -1:
            continue
        clusters.setdefault(int(lab), []).append(idx)

    out = []
    for lab, indices in sorted(clusters.items()):
        centroid = cents[lab].tolist() if 0 <= lab < len(cents) else []
        members = [meta[i] for i in indices]
        out.append({"id": lab, "count": len(members), "members": members, "centroid": centroid})
    return out

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Cluster hand shapes based on finger angles across many .hamer files")
    ap.add_argument("source", help=".hamer file or directory")
    ap.add_argument("-o", "--output", help="Output JSON path (default: angle_hand_clusters.json)")

    # Performance
    ap.add_argument("--threads", type=int, default=4, help="Number of threads for parallel processing")

    # Feature representation
    ap.add_argument("--feature", choices=["angle", "keypoints"],
                    default="angle",
                    help="Which per-frame descriptor to build")

    # Noise filtering
    ap.add_argument("--filter", choices=["lof", "isoforest", "maha", "none"], default="lof", help="Outlier filter")
    ap.add_argument("--contamination", type=float, default=0.05, help="Expected noise proportion (0‑1)")

    # Clustering
    ap.add_argument("--method", choices=["kmeans", "dbscan", "agglom", "hdbscan"], default="kmeans", help="Clustering algorithm")
    ap.add_argument("-k", "--n_clusters", type=int, default=10, help="k for kmeans/agglom (ignored otherwise)")
    ap.add_argument("--seed", type=int, default=0, help="Random seed where relevant")

    # Distance metric
    ap.add_argument("--distance", choices=["euclidean", "mahalanobis", "combined"], default="euclidean", help="Distance metric inside clustering")
    ap.add_argument("--alpha", type=float, default=0.5, help="Weight of Euclidean in the combined metric (0–1)")

    args = ap.parse_args()

    # Select feature extractor based on CLI argument
    FEATURE_EXTRACTOR = hand_frames_to_angle_features if args.feature == "angle" \
                        else keypoints_to_root_features

    src = Path(args.source)
    if src.is_file() and src.suffix == ".hamer":
        files = [src]
    elif src.is_dir():
        files = sorted(src.glob("*.hamer"))
        if not files:
            raise SystemExit(f"No .hamer files in {src}")
    else:
        raise SystemExit("Source must be a .hamer file or directory")

    out_path = Path(args.output) if args.output else (src if src.is_dir() else src.parent) / "angle_hand_clusters.json"

    # Parallel file processing
    feats_l, meta_l, feats_r, meta_r = ingest_files(files, max_workers=args.threads, feature_extractor=FEATURE_EXTRACTOR)

    # Parallel noise filtering
    hand_data = [("l_hand", feats_l, meta_l), ("r_hand", feats_r, meta_r)]
    if args.filter != "none":
        print("Applying noise filtering…")
        filter_func = partial(parallel_noise_filter, method=args.filter, contamination=args.contamination, seed=args.seed)
        with ThreadPoolExecutor(max_workers=2) as executor:
            filter_results = list(executor.map(filter_func, hand_data))
        for hand_name, filtered_feats, filtered_meta in filter_results:
            if hand_name == "l_hand":
                feats_l, meta_l = filtered_feats, filtered_meta
            else:
                feats_r, meta_r = filtered_feats, filtered_meta

    # Parallel clustering
    print("Performing clustering…")
    updated_hand_data = [("l_hand", feats_l, meta_l), ("r_hand", feats_r, meta_r)]
    cluster_func = partial(parallel_clustering, method=args.method, k=args.n_clusters, seed=args.seed, distance=args.distance, alpha=args.alpha)
    with ThreadPoolExecutor(max_workers=2) as executor:
        cluster_results = list(executor.map(cluster_func, updated_hand_data))

    # Build final output
    out_data = {}
    total_clusters = 0
    for hand_name, clusters in cluster_results:
        out_data[hand_name] = clusters
        total_clusters += len(clusters)
        frame_count = len(meta_l) if hand_name == "l_hand" else len(meta_r)
        print(f"{hand_name}: {len(clusters)} clusters | {frame_count} frames after filtering")

    save_json(out_path, out_data)
    print(f"Wrote {out_path} with {total_clusters} angle‑based clusters from {len(files)} file(s).")


if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=FutureWarning)
    main()
