import os
import json
import numpy as np
import pandas as pd
import lightgbm as lgb

# from tqdm import tqdm  # Run 'pip install tqdm' if you don't have it
from warnings import simplefilter

simplefilter(action="ignore", category=pd.errors.PerformanceWarning)


def generate_all_predictions(
    model_dir="../models/model_12_bulan_v5",
    output_path="precalculated_forecasts_2027.json",
):
    print("Loading Models & Schemas into memory...")

    with open(os.path.join(model_dir, "feature_schemas.json"), "r") as f:
        schemas = json.load(f)
        feature_schemas = {int(k): v for k, v in schemas.items()}

    models = {}
    for h in range(1, 13):
        model_path = os.path.join(model_dir, f"lgb_h{h}.txt")
        if os.path.exists(model_path):
            models[h] = lgb.Booster(model_file=model_path)

    print("Loading 2027 Feature Cache...")
    cache_df = pd.read_parquet(os.path.join(model_dir, "inference_cache_2027.parquet"))

    # Convert categories globally
    cat_cols = [
        "roomId",
        "propertyId",
        "room_cfg_room_type",
        "room_cfg_restriction_strategy",
        "room_cfg_unit_allocation",
        "room_cfg_tier",
    ]
    for c in cat_cols:
        if c in cache_df.columns:
            cache_df[c] = cache_df[c].astype("category")

    # Set MultiIndex for fast slicing
    cache_df.set_index(["roomId", "target_horizon"], drop=False, inplace=True)
    cache_df.sort_index(inplace=True)

    # Get all unique room IDs
    all_rooms = cache_df.index.get_level_values("roomId").unique()
    print(f"Found {len(all_rooms)} unique rooms. Starting bulk prediction...")

    final_predictions = {}

    # Loop through every single room
    for room_id in all_rooms:
        # Convert room_id to standard int/string for JSON serialization
        clean_room_id = str(room_id)
        room_results = []

        for h in range(1, 13):
            try:
                month_data = cache_df.loc[[(room_id, h)]]
            except KeyError:
                continue

            model = models.get(h)
            expected_features = feature_schemas.get(h)

            anchor = month_data["dynamic_anchor_price"].values[0]
            X_infer = month_data[expected_features]

            # Since this is local, we let LightGBM use all cores (no num_threads=1)
            pred_diff = model.predict(X_infer)[0]
            final_price = np.expm1(np.log1p(anchor) + pred_diff)

            room_results.append(
                {
                    "month": f"2027-{h:02d}",
                    "prediction": (
                        int(round(final_price)) if not np.isnan(final_price) else None
                    ),
                    "baseline_anchor_used_idr": (
                        int(round(anchor)) if not np.isnan(anchor) else None
                    ),
                }
            )

        if room_results:
            final_predictions[clean_room_id] = room_results

    # Save to JSON
    print(f"\nSaving results to {output_path}...")
    with open(output_path, "w") as f:
        json.dump(final_predictions, f)

    print("✅ Done! Upload this JSON file to your Render server.")


if __name__ == "__main__":
    generate_all_predictions()
