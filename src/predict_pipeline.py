import joblib
import os
import numpy as np
import pandas as pd
import lightgbm as lgb
from src.preprocessing.feature_engineer import advanced_hybrid_fe_direct
from src.preprocessing.preprocessing import preprocess
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from warnings import simplefilter
import json

simplefilter(action="ignore", category=pd.errors.PerformanceWarning)


class PredictPipeline:
    def __init__(self, model_dir="../models/model_12_bulan_v4"):
        self.model_dir = model_dir
        self.models = {}
        self.feature_schemas = {}

        print("Loading Models & Schemas into memory...")
        # Load Schemas
        with open(os.path.join(model_dir, "feature_schemas.json"), "r") as f:
            schemas = json.load(f)
            self.feature_schemas = {int(k): v for k, v in schemas.items()}

        # Load Models
        for h in range(1, 13):
            model_path = os.path.join(model_dir, f"lgb_h{h}.txt")
            if os.path.exists(model_path):
                self.models[h] = lgb.Booster(model_file=model_path)

        # Load the Pre-computed Inference Cache (Acting as your Database)
        print("Loading 2027 Feature Cache...")
        self.cache_df = pd.read_parquet(
            os.path.join(model_dir, "inference_cache_2027.parquet")
        )
        print("✅ Backend API Ready!")

    def predict(self, room_id, property_id=None):
        """Simulates an API endpoint: GET /api/v1/forecast/2027?roomId=X"""

        # 1. Query the cache for this specific room
        room_data = self.cache_df[self.cache_df["roomId"] == room_id].copy()
        print("room_data", room_data)
        if room_data.empty:
            return {"error": f"Room ID {room_id} not found in active inventory."}

        results = []

        # 2. Iterate through the 12 months (Horizons)
        for h in range(1, 13):
            month_data = room_data[room_data["target_horizon"] == h].copy()
            if month_data.empty:
                continue

            model = self.models.get(h)
            expected_features = self.feature_schemas.get(h)
            anchor = month_data["dynamic_anchor_price"].iloc[0]

            # Align features exactly as the model expects
            X_infer = month_data.reindex(columns=expected_features)

            # Categorical enforcement
            cat_cols = [
                "roomId",
                "propertyId",
                "room_cfg_room_type",
                "room_cfg_restriction_strategy",
                "room_cfg_unit_allocation",
                "room_cfg_tier",
            ]
            for c in cat_cols:
                if c in X_infer.columns:
                    X_infer[c] = X_infer[c].astype("category")

            # 3. Instant Prediction
            pred_diff = model.predict(X_infer)[0]

            # Reverse the Log-Diff using the cached anchor!
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
        print(f"Model Directory: {self.model_dir}")

        return {
            "roomId": room_id,
            "propertyId": property_id,
            #     (
            #     int(room_data["propertyId"].iloc[0])
            #     if "propertyId" in room_data.columns
            #     else None
            # ),
            "forecast": results,
        }


# class PredictPipeline:
#     def __init__(
#         self, anchor_col="dynamic_anchor_price", model_dir="models/model_12_bulan_v1"
#     ):
#         self.anchor_col = anchor_col
#         self.model_dir = model_dir

#     def load_model(self, h):
#         # Load model
#         model_path = os.path.join(self.model_dir, f"model_bulan_{h:02d}.txt")
#         booster = lgb.Booster(model_file=model_path)

#         # Load everything else (Like columns)
#         meta_path = os.path.join(self.model_dir, f"model_bulan_{h:02d}.pkl")
#         meta = joblib.load(meta_path)

#         return booster, meta

# def predict(self, data, room_id, property_id):
#     # --- TIMING SETUP ---
#     import time

#     t_total_start = time.perf_counter()
#     timing_stats = {
#         "initial_preprocess": 0.0,
#         "model_loading": 0.0,
#         "data_filtering_and_concat": 0.0,
#         "feature_engineering": 0.0,
#         "model_prediction": 0.0,
#         "metrics_calc": 0.0,
#     }
#     # --------------------

#     t_start = time.perf_counter()
#     # Initialize
#     y_pred_final = np.array([])
#     y_test_final = np.array([])

#     # --- NEW: Initialize our JSON-friendly list ---
#     results_list = []

#     # Preprocess
#     data = preprocess(df=data)

#     full_production_data = data.copy()

#     # --- PRE-LOOP OPTIMIZATIONS ---
#     # 1. Format dates once
#     if "date" not in full_production_data.columns:
#         full_production_data["date"] = pd.to_datetime(
#             full_production_data["month_period"], errors="coerce"
#         )
#     else:
#         full_production_data["date"] = pd.to_datetime(
#             full_production_data["date"], errors="coerce"
#         )

#     # 2. Sort and create anchor_col (lag 12) once for the whole dataset
#     full_production_data = full_production_data.sort_values(
#         ["roomId", "month_period"]
#     ).reset_index(drop=True)

#     if (
#         hasattr(self, "anchor_col")
#         and self.anchor_col not in full_production_data.columns
#     ):
#         print(f"{self.anchor_col} not in data, creating it using price lag 12...")
#         print(
#             "the anchor price is ",
#             full_production_data.groupby("roomId")["price"].shift(12),
#         )
#         full_production_data[self.anchor_col] = full_production_data.groupby(
#             "roomId"
#         )["price"].shift(12)

#     # 3. Isolate the target room's history to make loop operations lightning fast
#     room_history = full_production_data[
#         full_production_data["roomId"] == room_id
#     ].copy()
#     # ------------------------------

#     timing_stats["initial_preprocess"] += time.perf_counter() - t_start

#     # Loop for 12 months
#     for h in range(1, 13):
#         # Initialize needed variables
#         month_period = f"2024-{h:02d}"

#         t_start = time.perf_counter()
#         booster, meta = self.load_model(h=h)
#         timing_stats["model_loading"] += time.perf_counter() - t_start

#         t_start = time.perf_counter()

#         # --- THE FIX: USE .LOC MASKING INSTEAD OF CONCAT ---
#         # 1. Copy the pristine room history
#         filtered_production_data = room_history.copy()

#         # 2. Locate the current target month
#         current_month_mask = (
#             filtered_production_data["month_period"] == month_period
#         )

#         # 3. Extract test price before masking
#         y_test_price = filtered_production_data.loc[
#             current_month_mask, "price"
#         ].copy()

#         # 4. Define columns that represent the "dummy row" you used to create
#         cols_to_keep = ["propertyId", "roomId", "month_period", "date"]
#         if (
#             hasattr(self, "anchor_col")
#             and self.anchor_col in filtered_production_data.columns
#         ):
#             cols_to_keep.append(self.anchor_col)

#         # 5. Mask all other columns (price, targets, features) to NaN
#         # This perfectly simulates an unknown future month without any concat or sorting overhead
#         cols_to_mask = [
#             c for c in filtered_production_data.columns if c not in cols_to_keep
#         ]
#         filtered_production_data.loc[current_month_mask, cols_to_mask] = np.nan

#         # ---------------------------------------------------
#         timing_stats["data_filtering_and_concat"] += time.perf_counter() - t_start

#         t_start = time.perf_counter()

#         # FE now runs on the masked dataframe
#         prod_step_data = advanced_hybrid_fe_direct(
#             filtered_production_data, h=h
#         ).copy()

#         filt_prod = prod_step_data["month_period"] == month_period
#         prod_step_data = prod_step_data[filt_prod].copy()
#         # print("prod_step_data", prod_step_data)

#         feature_columns = meta["feature_columns"]
#         categorical_columns = meta["categorical_columns"]

#         cols_to_drop_prod = [
#             "price",
#             "log_price",
#             "target_diff",
#             "target_pct",
#             "date",
#             "month_period",
#             f"log_price_lag_{h}",
#             "log_price_lag_12",
#             "id",
#         ]

#         X_prod = prod_step_data.drop(
#             columns=[c for c in cols_to_drop_prod if c in prod_step_data.columns]
#         )

#         for c in categorical_columns:
#             if c in X_prod.columns:
#                 X_prod[c] = X_prod[c].astype("category")

#         good_lgbm_dtypes = ["number", "category", "bool"]

#         X_prod = X_prod.select_dtypes(include=good_lgbm_dtypes).copy()
#         X_prod = X_prod.reindex(columns=feature_columns).copy()
#         # print("X_prod", X_prod)
#         timing_stats["feature_engineering"] += time.perf_counter() - t_start

#         t_start = time.perf_counter()
#         # Predict
#         y_pred_diff = booster.predict(X_prod, num_iteration=booster.best_iteration)
#         # print("y_pred_diff", y_pred_diff)
#         y_pred_price = np.expm1(
#             np.log1p(prod_step_data[self.anchor_col].values) + y_pred_diff
#         )
#         # print("prod_step_data", prod_step_data.columns)
#         # print("self.anchor_col", self.anchor_col)
#         # print(
#         #     "prod_step_data[self.anchor_col].values",
#         #     prod_step_data[self.anchor_col].values,
#         # )
#         # print("y_pred_price", y_pred_price)

#         # Add predicted price to the array
#         y_pred_final = np.append(y_pred_final, y_pred_price)
#         y_test_final = np.append(y_test_final, y_test_price)

#         # --- NEW: Append dictionary format for React frontend ---
#         for pred in y_pred_price:
#             results_list.append(
#                 {
#                     "date": month_period,
#                     "prediction": float(
#                         pred
#                     ),  # Cast to float to avoid JSON serialization errors
#                 }
#             )
#         # --------------------------------------------------------

#         timing_stats["model_prediction"] += time.perf_counter() - t_start

#     t_start = time.perf_counter()
#     # print("y_test_final : ", y_test_final)
#     r2 = r2_score(y_test_final, y_pred_final)

#     # MAE
#     mae = mean_absolute_error(y_test_final, y_pred_final)

#     # MAPE (manual)
#     mape = np.mean(np.abs((y_test_final - y_pred_final) / y_test_final)) * 100

#     print(f"R2: {r2}")
#     print(f"MAE: {mae}")
#     print(f"MAPE: {mape}%")
#     print("Predicted prices for 12 months:", y_pred_final)
#     timing_stats["metrics_calc"] += time.perf_counter() - t_start

#     # --- PRINT TIMING SUMMARY ---
#     total_time = time.perf_counter() - t_total_start
#     # print("\n" + "=" * 50)
#     # print("⏱️ EXECUTION TIME SUMMARY")
#     # print("=" * 50)
#     # for step, duration in timing_stats.items():
#     #     percentage = (duration / total_time) * 100 if total_time > 0 else 0
#     # print(f"{step:<30}: {duration:.4f} sec ({percentage:>5.1f}%)")
#     # print("-" * 50)
#     print(f"{'TOTAL TIME':<30}: {total_time:.4f} sec")
#     print("=" * 50 + "\n")
#     # ----------------------------

#     return results_list

# def predict(self, data, room_id, property_id):
#     # Initialize
#     y_pred_final = np.array([])
#     y_test_final = np.array([])

#     # Preprocess
#     data = preprocess(df=data)

#     full_production_data = data.copy()

#     # Loop for 12 months
#     for h in range(1, 13):
#         # Initialize needed variables
#         month_period = f"2024-{h:02d}"
#         booster, meta = self.load_model(h=h)

#         # Load data and remove data so there wont be duplicate
#         full_production_data = full_production_data.sort_values(
#             ["roomId", "month_period"]
#         ).reset_index(drop=True)
#         filt = (full_production_data["roomId"] == room_id) & (
#             full_production_data["month_period"] == month_period
#         )

#         print("full_production_data", full_production_data)
#         y_test_price = full_production_data[filt]["price"].copy()
#         filtered_production_data = full_production_data[~filt]
#         print("filtered_production_data", filtered_production_data)
#         # Insert new data
#         new_row = {
#             "propertyId": property_id,
#             "roomId": room_id,
#             "month_period": month_period,
#         }
#         new_df = pd.DataFrame([new_row])
#         filtered_production_data = pd.concat(
#             [filtered_production_data, new_df], ignore_index=True
#         )
#         filtered_production_data = filtered_production_data.sort_values(
#             ["roomId", "month_period"]
#         ).reset_index(drop=True)

#         # Preprocessing
#         if "date" not in filtered_production_data.columns:
#             filtered_production_data["date"] = pd.to_datetime(
#                 filtered_production_data["month_period"], errors="coerce"
#             )
#         else:
#             filtered_production_data["date"] = pd.to_datetime(
#                 filtered_production_data["date"], errors="coerce"
#             )

#         if self.anchor_col not in filtered_production_data.columns:
#             print(
#                 f"{self.anchor_col} not in data, creating it using price lag 12..."
#             )
#             print(
#                 "the anchor price is ",
#                 filtered_production_data.groupby("roomId")["price"].shift(12),
#             )
#             filtered_production_data[self.anchor_col] = (
#                 filtered_production_data.groupby("roomId")["price"].shift(12)
#             )

#         prod_step_data = advanced_hybrid_fe_direct(
#             filtered_production_data, h=h
#         ).copy()
#         filt = (filtered_production_data["roomId"] == room_id) & (
#             filtered_production_data["month_period"] == month_period
#         )
#         prod_step_data = prod_step_data[filt].copy()
#         print("prod_step_data", prod_step_data)
#         feature_columns = meta["feature_columns"]
#         categorical_columns = meta["categorical_columns"]

#         cols_to_drop_prod = [
#             "price",
#             "log_price",
#             "target_diff",
#             "target_pct",
#             "date",
#             "month_period",
#             f"log_price_lag_{h}",
#             "log_price_lag_12",
#             "id",
#         ]
#         X_prod = prod_step_data.drop(
#             columns=[c for c in cols_to_drop_prod if c in prod_step_data.columns]
#         )

#         for c in categorical_columns:
#             if c in X_prod.columns:
#                 X_prod[c] = X_prod[c].astype("category")

#         good_lgbm_dtypes = ["number", "category", "bool"]

#         X_prod = X_prod.select_dtypes(include=good_lgbm_dtypes).copy()
#         X_prod = X_prod.reindex(columns=feature_columns).copy()
#         print("X_prod", X_prod)
#         # Predict
#         y_pred_diff = booster.predict(X_prod, num_iteration=booster.best_iteration)
#         print("y_pred_diff", y_pred_diff)
#         y_pred_price = np.expm1(
#             np.log1p(prod_step_data[self.anchor_col].values) + y_pred_diff
#         )
#         print("prod_step_data", prod_step_data.columns)
#         print("self.anchor_col", self.anchor_col)
#         print(
#             "prod_step_data[self.anchor_col].values",
#             prod_step_data[self.anchor_col].values,
#         )
#         print("y_pred_price", y_pred_price)

#         # print(y_test_price)
#         # Add predicted price to the array
#         y_pred_final = np.append(y_pred_final, y_pred_price)
#         y_test_final = np.append(y_test_final, y_test_price)
#     print("y_test_final : ", y_test_final)
#     r2 = r2_score(y_test_final, y_pred_final)

#     # MAE
#     mae = mean_absolute_error(y_test_final, y_pred_final)

#     # MAPE (manual)
#     mape = np.mean(np.abs((y_test_final - y_pred_final) / y_test_final)) * 100

#     print(f"R2: {r2}")
#     print(f"MAE: {mae}")
#     print(f"MAPE: {mape}%")
#     print("Predicted prices for 12 months:", y_pred_final)

#     return y_pred_final
