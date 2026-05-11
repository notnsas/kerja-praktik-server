import joblib
import os
import numpy as np
import pandas as pd
import lightgbm as lgb
import json
from warnings import simplefilter

simplefilter(action="ignore", category=pd.errors.PerformanceWarning)


class PredictPipeline:
    def __init__(self, model_dir="../models/model_12_bulan_v4"):
        self.model_dir = model_dir
        self.models = {}
        self.feature_schemas = {}

        print("Loading Models & Schemas into memory...")
        # 1. Load Schemas
        with open(os.path.join(model_dir, "feature_schemas.json"), "r") as f:
            schemas = json.load(f)
            self.feature_schemas = {int(k): v for k, v in schemas.items()}

        # 2. Load Models
        for h in range(1, 13):
            model_path = os.path.join(model_dir, f"lgb_h{h}.txt")
            if os.path.exists(model_path):
                self.models[h] = lgb.Booster(model_file=model_path)

        # 3. Load and Optimize the Cache (DO THIS ONCE ON STARTUP)
        print("Loading and Optimizing 2027 Feature Cache...")
        self.cache_df = pd.read_parquet(
            os.path.join(model_dir, "inference_cache_2027.parquet")
        )

        # Convert categories globally during startup so we don't do it per request
        cat_cols = [
            "roomId",
            "propertyId",
            "room_cfg_room_type",
            "room_cfg_restriction_strategy",
            "room_cfg_unit_allocation",
            "room_cfg_tier",
        ]
        for c in cat_cols:
            if c in self.cache_df.columns:
                self.cache_df[c] = self.cache_df[c].astype("category")

        # Set roomId as the index for O(1) lookups, but DO NOT drop it from the columns
        self.cache_df.set_index("roomId", drop=False, inplace=True)

        print("✅ Backend API Ready!")

    def predict(self, room_id, property_id=None):
        """Simulates an API endpoint: GET /api/v1/forecast/2027?roomId=X"""

        # 1. Query the cache (Instant lookup using the index)
        try:
            # Use .loc to get all rows for this room.
            # If room_id isn't in the index, this safely raises a KeyError
            room_data = self.cache_df.loc[[room_id]]
        except KeyError:
            return {"error": f"Room ID {room_id} not found in active inventory."}

        results = []

        # 2. Iterate through the 12 horizons
        for h in range(1, 13):
            # Filter for the specific month without making heavy Pandas copies
            month_data = room_data[room_data["target_horizon"] == h]
            if month_data.empty:
                continue

            model = self.models.get(h)
            expected_features = self.feature_schemas.get(h)

            # Get scalar anchor value
            anchor = month_data["dynamic_anchor_price"].iloc[0]

            # Align features exactly as the model expects
            X_infer = month_data.reindex(columns=expected_features)
            # --- ADD THIS: Lightweight safety net ---
            # Ensures Pandas didn't accidentally drop the 'category' type during reindex
            cat_cols = [
                "roomId",
                "propertyId",
                "room_cfg_room_type",
                "room_cfg_restriction_strategy",
                "room_cfg_unit_allocation",
                "room_cfg_tier",
            ]
            for c in cat_cols:
                if c in X_infer.columns and X_infer[c].dtype.name != "category":
                    X_infer[c] = X_infer[c].astype("category")
            # ----------------------------------------

            # 3. Instant Prediction (Limit threads to 1 for weak cloud CPUs)
            pred_diff = model.predict(X_infer, num_threads=1)[0]

            # Reverse the Log-Diff
            final_price = np.expm1(np.log1p(anchor) + pred_diff)

            results.append(
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

        return {
            "roomId": room_id,
            "propertyId": property_id,
            "forecast": results,
        }
