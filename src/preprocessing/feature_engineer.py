import pandas as pd
import numpy as np


# def advanced_hybrid_fe_direct(data, h=1):
#     """
#     Feature engineering for Direct Multi-Step Forecasting (YoY Target).
#     Includes Vectorized Smart Fallback Anchors + MACRO INFLATION.
#     """
#     df = data.copy()

#     # 1. Sort correctly to prevent data leakage in shifts
#     df = df.sort_values(["roomId", "month_period"]).reset_index(drop=True)

#     # ======================
#     # TIME & SEASON FEATURES
#     # ======================
#     df["date"] = pd.to_datetime(df["month_period"].astype(str))
#     df["month"] = df["date"].dt.month
#     df["quarter"] = df["date"].dt.quarter
#     df["year"] = df["date"].dt.year

#     season_map = {
#         1: 0,
#         2: 0,
#         11: 0,
#         3: 1,
#         4: 1,
#         5: 1,
#         6: 1,
#         10: 1,
#         7: 2,
#         8: 2,
#         9: 2,
#         12: 3,
#     }
#     df["season_strength"] = df["month"].map(season_map)

#     # Peak Lombok/Gili season
#     df["is_peak_season"] = df["month"].isin([7, 8, 12]).astype(int)

#     eid_months = {2022: 5, 2023: 4, 2024: 4, 2025: 3, 2026: 3, 2027: 3}
#     df["is_eid_month"] = df.apply(
#         lambda row: 1 if eid_months.get(row["year"]) == row["month"] else 0, axis=1
#     )
#     df["is_major_holiday_month"] = (
#         (df["month"] == 12) | (df["is_eid_month"] == 1)
#     ).astype(int)

#     df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
#     df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)

#     # ======================
#     # DYNAMIC LAGS
#     # ======================
#     base_lag = h

#     lags_to_create = list(
#         set(
#             [
#                 base_lag,
#                 base_lag + 1,
#                 base_lag + 2,
#                 base_lag + 5,
#                 base_lag + 11,
#                 base_lag + 12,
#                 12,
#                 24,
#                 36,
#             ]
#         )
#     )

#     for lag in lags_to_create:
#         df[f"price_lag_{lag}"] = df.groupby("roomId")["price"].shift(lag)

#         # Shift inflation just like we shift price!
#         if "inflation_rate" in df.columns:
#             # We don't group by roomId for inflation since it's global,
#             # but doing it guarantees row alignment per room
#             df[f"inflation_lag_{lag}"] = df.groupby("roomId")["inflation_rate"].shift(
#                 lag
#             )

#     # ======================
#     # SMART DYNAMIC ANCHOR + MACRO INFLATION
#     # ======================
#     df["dynamic_anchor_price"] = df["price_lag_12"]
#     df["anchor_age_months"] = 12

#     if "inflation_rate" in df.columns:
#         df["dynamic_anchor_inflation"] = df["inflation_lag_12"]

#     # Fallback 1: 2 Years Ago (24 months)
#     mask_24 = df["dynamic_anchor_price"].isna() & df["price_lag_24"].notna()
#     df.loc[mask_24, "dynamic_anchor_price"] = df.loc[mask_24, "price_lag_24"]
#     df.loc[mask_24, "anchor_age_months"] = 24
#     if "inflation_rate" in df.columns:
#         df.loc[mask_24, "dynamic_anchor_inflation"] = df.loc[
#             mask_24, "inflation_lag_24"
#         ]

#     # Fallback 2: 3 Years Ago (36 months)
#     mask_36 = df["dynamic_anchor_price"].isna() & df["price_lag_36"].notna()
#     df.loc[mask_36, "dynamic_anchor_price"] = df.loc[mask_36, "price_lag_36"]
#     df.loc[mask_36, "anchor_age_months"] = 36
#     if "inflation_rate" in df.columns:
#         df.loc[mask_36, "dynamic_anchor_inflation"] = df.loc[
#             mask_36, "inflation_lag_36"
#         ]

#     # Fallback 3: Most Recent Known Price (base_lag)
#     mask_base = df["dynamic_anchor_price"].isna() & df[f"price_lag_{base_lag}"].notna()
#     df.loc[mask_base, "dynamic_anchor_price"] = df.loc[
#         mask_base, f"price_lag_{base_lag}"
#     ]
#     df.loc[mask_base, "anchor_age_months"] = base_lag
#     if "inflation_rate" in df.columns:
#         df.loc[mask_base, "dynamic_anchor_inflation"] = df.loc[
#             mask_base, f"inflation_lag_{base_lag}"
#         ]

#     df["is_fallback_anchor"] = (df["anchor_age_months"] != 12).astype(int)

#     # 🚨 NEW MACRO FEATURE: The change in inflation between the old anchor and right now
#     if "inflation_rate" in df.columns:
#         # Current known inflation (at base_lag) minus inflation when the anchor was recorded
#         df["inflation_diff_since_anchor"] = (
#             df[f"inflation_lag_{base_lag}"] - df["dynamic_anchor_inflation"]
#         )

#         # Absolute inflation at the time of prediction origin
#         df["current_known_inflation"] = df[f"inflation_lag_{base_lag}"]

#     # ======================
#     # ROLLING FEATURES (Anchored to base_lag)
#     # ======================
#     windows = [3, 6, 12]
#     for w in windows:
#         df[f"price_roll_mean_{w}"] = df.groupby("roomId")[
#             f"price_lag_{base_lag}"
#         ].transform(lambda x: x.rolling(w, min_periods=1).mean())
#         df[f"price_roll_std_{w}"] = df.groupby("roomId")[
#             f"price_lag_{base_lag}"
#         ].transform(lambda x: x.rolling(w, min_periods=2).std())
#         df[f"price_roll_max_{w}"] = df.groupby("roomId")[
#             f"price_lag_{base_lag}"
#         ].transform(lambda x: x.rolling(w, min_periods=1).max())
#         df[f"price_roll_min_{w}"] = df.groupby("roomId")[
#             f"price_lag_{base_lag}"
#         ].transform(lambda x: x.rolling(w, min_periods=1).min())

#     df["price_diff_1"] = df[f"price_lag_{base_lag}"] - df[f"price_lag_{base_lag + 1}"]
#     df["price_diff_12"] = df[f"price_lag_{base_lag}"] - df[f"price_lag_{base_lag + 11}"]

#     eps = 1e-5
#     df["price_growth_1"] = df["price_diff_1"] / (df[f"price_lag_{base_lag + 1}"] + eps)
#     df["price_ema_3"] = df.groupby("roomId")[f"price_lag_{base_lag}"].transform(
#         lambda x: x.ewm(span=3, adjust=False).mean()
#     )

#     df["price_base_vs_anchor"] = df[f"price_lag_{base_lag}"] / (
#         df["dynamic_anchor_price"] + eps
#     )

#     # ======================
#     # BEHAVIOR & OCCUPANCY
#     # ======================
#     leaky_numerical_cols = [
#         "used_room_nights",
#         "leftover_rooms",
#         "range_booking_arrival",
#         "num_of_nights",
#         "commission",
#         "numChild",
#     ]
#     leaky_numerical_cols = [c for c in leaky_numerical_cols if c in df.columns]

#     for col in leaky_numerical_cols:
#         for rl in [0, 1, 11]:
#             actual_lag = base_lag + rl
#             df[f"{col}_lag_{actual_lag}"] = df.groupby("roomId")[col].shift(actual_lag)

#         df[f"{col}_roll_mean_3"] = df.groupby("roomId")[
#             f"{col}_lag_{base_lag}"
#         ].transform(lambda x: x.rolling(3, min_periods=1).mean())

#     if (
#         f"used_room_nights_lag_{base_lag}" in df.columns
#         and f"used_room_nights_lag_{base_lag+1}" in df.columns
#     ):
#         df["occupancy_trend"] = (
#             df[f"used_room_nights_lag_{base_lag}"]
#             - df[f"used_room_nights_lag_{base_lag+1}"]
#         )

#     # ======================
#     # INTERACTION FEATURES
#     # ======================
#     df["price_to_mean_ratio"] = df[f"price_lag_{base_lag}"] / (
#         df["price_roll_mean_12"] + eps
#     )

#     if "propertyId" in df.columns:
#         prop_mean = df.groupby("propertyId")[f"price_lag_{base_lag}"].transform("mean")
#         prop_std = df.groupby("propertyId")[f"price_lag_{base_lag}"].transform("std")
#         df["price_vs_property_avg"] = df[f"price_lag_{base_lag}"] / (prop_mean + eps)
#         df["price_zscore_property"] = (df[f"price_lag_{base_lag}"] - prop_mean) / (
#             prop_std + eps
#         )

#     if f"used_room_nights_lag_{base_lag}" in df.columns:
#         df["occupancy_price_interaction"] = (
#             df[f"used_room_nights_lag_{base_lag}"] * df[f"price_lag_{base_lag}"]
#         )

#     if "price_roll_mean_3" in df.columns and "price_roll_mean_12" in df.columns:
#         df["trend_3_vs_12"] = df["price_roll_mean_3"] / (df["price_roll_mean_12"] + eps)

#     if "price_roll_mean_6" in df.columns:
#         df["trend_slope"] = df[f"price_lag_{base_lag}"] - df["price_roll_mean_6"]
#         df["price_vs_roll_mean_6"] = df[f"price_lag_{base_lag}"] / (
#             df["price_roll_mean_6"] + eps
#         )
#         df["price_cv_6"] = df["price_roll_std_6"] / (df["price_roll_mean_6"] + eps)

#         median_std = df["price_roll_std_6"].median()
#         if pd.notna(median_std):
#             df["is_volatile_room"] = (df["price_roll_std_6"] > median_std).astype(int)

#         df["is_spike"] = (
#             abs(df[f"price_lag_{base_lag}"] - df["price_roll_mean_6"])
#             > 2 * df["price_roll_std_6"]
#         ).astype(int)

#     df["season_price_interaction"] = df["season_strength"] * df[f"price_lag_{base_lag}"]
#     df["peak_price_interaction"] = df["is_peak_season"] * df[f"price_lag_{base_lag}"]

#     if "occupancy_trend" in df.columns:
#         df["occupancy_season_interaction"] = (
#             df["occupancy_trend"] * df["is_peak_season"]
#         )

#     # ======================
#     # EXTRA LONG-HORIZON SIGNAL
#     # ======================
#     if (
#         f"price_lag_{base_lag}" in df.columns
#         and f"price_lag_{base_lag+12}" in df.columns
#     ):
#         df["price_yoy_historical"] = df[f"price_lag_{base_lag}"] / (
#             df[f"price_lag_{base_lag+12}"] + eps
#         )

#     if "price_roll_mean_12" in df.columns:
#         df["price_vs_trend_12"] = df[f"price_lag_{base_lag}"] / (
#             df["price_roll_mean_12"] + eps
#         )

#     if "price_roll_mean_3" in df.columns and "price_roll_mean_12" in df.columns:
#         df["trend_strength"] = df["price_roll_mean_3"] - df["price_roll_mean_12"]

#     df["month_price_interaction"] = df["month"] * df[f"price_lag_{base_lag}"]
#     df["month_sin_price"] = df["month_sin"] * df[f"price_lag_{base_lag}"]
#     df["month_cos_price"] = df["month_cos"] * df[f"price_lag_{base_lag}"]

#     # ======================
#     # SHIFT REMAINING CATEGORICALS / UNKNOWN COLUMNS
#     # ======================
#     safe_current_month_cols = {
#         "id",
#         "propertyId",
#         "roomId",
#         "month_period",
#         "date",
#         "month",
#         "quarter",
#         "year",
#         "season_strength",
#         "is_peak_season",
#         "is_eid_month",
#         "is_major_holiday_month",
#         "total_capacity_nights",
#         "price",
#         "month_sin",
#         "month_cos",
#         "dynamic_anchor_price",
#         "anchor_age_months",
#         "is_fallback_anchor",
#         "inflation_rate",
#         "dynamic_anchor_inflation",
#         "inflation_diff_since_anchor",
#         "current_known_inflation",
#     }

#     all_raw_cols = set(data.columns)
#     other_leaky_cols = list(
#         all_raw_cols - safe_current_month_cols - set(leaky_numerical_cols)
#     )

#     for col in other_leaky_cols:
#         df[f"{col}_lag_{base_lag}"] = df.groupby("roomId")[col].shift(base_lag)

#     cols_to_drop = list(set(leaky_numerical_cols) | set(other_leaky_cols))
#     if "id" in df.columns:
#         cols_to_drop.append("id")

#     df = df.drop(columns=[c for c in cols_to_drop if c in df.columns])

#     # ======================
#     # ROBUSTNESS (REDUCE OVERFITTING)
#     # ======================
#     for col in [
#         "price_to_mean_ratio",
#         "price_vs_property_avg",
#         "price_vs_roll_mean_6",
#         "price_base_vs_anchor",
#         "price_yoy_historical",
#     ]:
#         if col in df.columns:
#             df[col] = df[col].clip(0, 5)

#     for col in ["price_roll_std_6", "price_roll_std_12"]:
#         if col in df.columns:
#             df[f"log_{col}"] = np.log1p(df[col])

#     return df

import pandas as pd
import numpy as np


def advanced_hybrid_fe_direct(data, h=1):
    """
    Feature engineering for Direct Multi-Step Forecasting (YoY Target).
    Includes Vectorized Smart Fallback Anchors + MACRO INFLATION.
    *OPTIMIZED FOR C-LEVEL VECTORIZATION*
    """
    df = data.copy()

    # 1. Sort correctly to prevent data leakage in shifts
    # Crucial: This clean RangeIndex makes the fast rolling calculations safe
    df = df.sort_values(["roomId", "month_period"]).reset_index(drop=True)

    # ======================
    # TIME & SEASON FEATURES
    # ======================
    df["date"] = pd.to_datetime(df["month_period"].astype(str))
    df["month"] = df["date"].dt.month
    df["quarter"] = df["date"].dt.quarter
    df["year"] = df["date"].dt.year

    season_map = {
        1: 0,
        2: 0,
        11: 0,
        3: 1,
        4: 1,
        5: 1,
        6: 1,
        10: 1,
        7: 2,
        8: 2,
        9: 2,
        12: 3,
    }
    df["season_strength"] = df["month"].map(season_map)

    # Peak Lombok/Gili season
    df["is_peak_season"] = df["month"].isin([7, 8, 12]).astype(int)

    # ⚡ OPTIMIZATION 1: Removed slow .apply(lambda)
    eid_months = {2022: 5, 2023: 4, 2024: 4, 2025: 3, 2026: 3, 2027: 3}
    df["is_eid_month"] = (df["month"] == df["year"].map(eid_months)).astype(int)

    df["is_major_holiday_month"] = (
        (df["month"] == 12) | (df["is_eid_month"] == 1)
    ).astype(int)

    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)

    # ======================
    # DYNAMIC LAGS
    # ======================
    base_lag = h

    lags_to_create = list(
        set(
            [
                base_lag,
                base_lag + 1,
                base_lag + 2,
                base_lag + 5,
                base_lag + 11,
                base_lag + 12,
                12,
                24,
                36,
            ]
        )
    )

    for lag in lags_to_create:
        df[f"price_lag_{lag}"] = df.groupby("roomId")["price"].shift(lag)
        if "inflation_rate" in df.columns:
            df[f"inflation_lag_{lag}"] = df.groupby("roomId")["inflation_rate"].shift(
                lag
            )

    # ======================
    # SMART DYNAMIC ANCHOR + MACRO INFLATION
    # ======================
    df["dynamic_anchor_price"] = df["price_lag_12"]
    df["anchor_age_months"] = 12

    if "inflation_rate" in df.columns:
        df["dynamic_anchor_inflation"] = df["inflation_lag_12"]

    # Fallback 1: 2 Years Ago (24 months)
    mask_24 = df["dynamic_anchor_price"].isna() & df["price_lag_24"].notna()
    df.loc[mask_24, "dynamic_anchor_price"] = df.loc[mask_24, "price_lag_24"]
    df.loc[mask_24, "anchor_age_months"] = 24
    if "inflation_rate" in df.columns:
        df.loc[mask_24, "dynamic_anchor_inflation"] = df.loc[
            mask_24, "inflation_lag_24"
        ]

    # Fallback 2: 3 Years Ago (36 months)
    mask_36 = df["dynamic_anchor_price"].isna() & df["price_lag_36"].notna()
    df.loc[mask_36, "dynamic_anchor_price"] = df.loc[mask_36, "price_lag_36"]
    df.loc[mask_36, "anchor_age_months"] = 36
    if "inflation_rate" in df.columns:
        df.loc[mask_36, "dynamic_anchor_inflation"] = df.loc[
            mask_36, "inflation_lag_36"
        ]

    # Fallback 3: Most Recent Known Price (base_lag)
    mask_base = df["dynamic_anchor_price"].isna() & df[f"price_lag_{base_lag}"].notna()
    df.loc[mask_base, "dynamic_anchor_price"] = df.loc[
        mask_base, f"price_lag_{base_lag}"
    ]
    df.loc[mask_base, "anchor_age_months"] = base_lag
    if "inflation_rate" in df.columns:
        df.loc[mask_base, "dynamic_anchor_inflation"] = df.loc[
            mask_base, f"inflation_lag_{base_lag}"
        ]

    df["is_fallback_anchor"] = (df["anchor_age_months"] != 12).astype(int)

    if "inflation_rate" in df.columns:
        df["inflation_diff_since_anchor"] = (
            df[f"inflation_lag_{base_lag}"] - df["dynamic_anchor_inflation"]
        )
        df["current_known_inflation"] = df[f"inflation_lag_{base_lag}"]

    # ======================
    # ROLLING FEATURES (Anchored to base_lag)
    # ======================
    windows = [3, 6, 12]

    # ⚡ OPTIMIZATION 2: Removed slow .transform(lambda). Replaced with direct C-level rolling.
    grp_price = df.groupby("roomId")[f"price_lag_{base_lag}"]

    for w in windows:
        df[f"price_roll_mean_{w}"] = (
            grp_price.rolling(w, min_periods=1).mean().reset_index(level=0, drop=True)
        )
        df[f"price_roll_std_{w}"] = (
            grp_price.rolling(w, min_periods=2).std().reset_index(level=0, drop=True)
        )
        df[f"price_roll_max_{w}"] = (
            grp_price.rolling(w, min_periods=1).max().reset_index(level=0, drop=True)
        )
        df[f"price_roll_min_{w}"] = (
            grp_price.rolling(w, min_periods=1).min().reset_index(level=0, drop=True)
        )

    df["price_diff_1"] = df[f"price_lag_{base_lag}"] - df[f"price_lag_{base_lag + 1}"]
    df["price_diff_12"] = df[f"price_lag_{base_lag}"] - df[f"price_lag_{base_lag + 11}"]

    eps = 1e-5
    df["price_growth_1"] = df["price_diff_1"] / (df[f"price_lag_{base_lag + 1}"] + eps)

    # ⚡ OPTIMIZATION 3: Vectorized EWM
    df["price_ema_3"] = (
        grp_price.ewm(span=3, adjust=False).mean().reset_index(level=0, drop=True)
    )

    df["price_base_vs_anchor"] = df[f"price_lag_{base_lag}"] / (
        df["dynamic_anchor_price"] + eps
    )

    # ======================
    # BEHAVIOR & OCCUPANCY
    # ======================
    leaky_numerical_cols = [
        "used_room_nights",
        "leftover_rooms",
        "range_booking_arrival",
        "num_of_nights",
        "commission",
        "numChild",
    ]
    leaky_numerical_cols = [c for c in leaky_numerical_cols if c in df.columns]

    for col in leaky_numerical_cols:
        for rl in [0, 1, 11]:
            actual_lag = base_lag + rl
            df[f"{col}_lag_{actual_lag}"] = df.groupby("roomId")[col].shift(actual_lag)

        # ⚡ OPTIMIZATION 4: Vectorized leaky columns rolling
        df[f"{col}_roll_mean_3"] = (
            df.groupby("roomId")[f"{col}_lag_{base_lag}"]
            .rolling(3, min_periods=1)
            .mean()
            .reset_index(level=0, drop=True)
        )

    if (
        f"used_room_nights_lag_{base_lag}" in df.columns
        and f"used_room_nights_lag_{base_lag+1}" in df.columns
    ):
        df["occupancy_trend"] = (
            df[f"used_room_nights_lag_{base_lag}"]
            - df[f"used_room_nights_lag_{base_lag+1}"]
        )

    # ======================
    # INTERACTION FEATURES
    # ======================
    df["price_to_mean_ratio"] = df[f"price_lag_{base_lag}"] / (
        df["price_roll_mean_12"] + eps
    )

    if "propertyId" in df.columns:
        prop_mean = df.groupby("propertyId")[f"price_lag_{base_lag}"].transform("mean")
        prop_std = df.groupby("propertyId")[f"price_lag_{base_lag}"].transform("std")
        df["price_vs_property_avg"] = df[f"price_lag_{base_lag}"] / (prop_mean + eps)
        df["price_zscore_property"] = (df[f"price_lag_{base_lag}"] - prop_mean) / (
            prop_std + eps
        )

    if f"used_room_nights_lag_{base_lag}" in df.columns:
        df["occupancy_price_interaction"] = (
            df[f"used_room_nights_lag_{base_lag}"] * df[f"price_lag_{base_lag}"]
        )

    if "price_roll_mean_3" in df.columns and "price_roll_mean_12" in df.columns:
        df["trend_3_vs_12"] = df["price_roll_mean_3"] / (df["price_roll_mean_12"] + eps)

    if "price_roll_mean_6" in df.columns:
        df["trend_slope"] = df[f"price_lag_{base_lag}"] - df["price_roll_mean_6"]
        df["price_vs_roll_mean_6"] = df[f"price_lag_{base_lag}"] / (
            df["price_roll_mean_6"] + eps
        )
        df["price_cv_6"] = df["price_roll_std_6"] / (df["price_roll_mean_6"] + eps)

        median_std = df["price_roll_std_6"].median()
        if pd.notna(median_std):
            df["is_volatile_room"] = (df["price_roll_std_6"] > median_std).astype(int)

        df["is_spike"] = (
            abs(df[f"price_lag_{base_lag}"] - df["price_roll_mean_6"])
            > 2 * df["price_roll_std_6"]
        ).astype(int)

    df["season_price_interaction"] = df["season_strength"] * df[f"price_lag_{base_lag}"]
    df["peak_price_interaction"] = df["is_peak_season"] * df[f"price_lag_{base_lag}"]

    if "occupancy_trend" in df.columns:
        df["occupancy_season_interaction"] = (
            df["occupancy_trend"] * df["is_peak_season"]
        )

    # ======================
    # EXTRA LONG-HORIZON SIGNAL
    # ======================
    if (
        f"price_lag_{base_lag}" in df.columns
        and f"price_lag_{base_lag+12}" in df.columns
    ):
        df["price_yoy_historical"] = df[f"price_lag_{base_lag}"] / (
            df[f"price_lag_{base_lag+12}"] + eps
        )

    if "price_roll_mean_12" in df.columns:
        df["price_vs_trend_12"] = df[f"price_lag_{base_lag}"] / (
            df["price_roll_mean_12"] + eps
        )

    if "price_roll_mean_3" in df.columns and "price_roll_mean_12" in df.columns:
        df["trend_strength"] = df["price_roll_mean_3"] - df["price_roll_mean_12"]

    df["month_price_interaction"] = df["month"] * df[f"price_lag_{base_lag}"]
    df["month_sin_price"] = df["month_sin"] * df[f"price_lag_{base_lag}"]
    df["month_cos_price"] = df["month_cos"] * df[f"price_lag_{base_lag}"]

    # ======================
    # SHIFT REMAINING CATEGORICALS / UNKNOWN COLUMNS
    # ======================
    safe_current_month_cols = {
        "id",
        "propertyId",
        "roomId",
        "month_period",
        "date",
        "month",
        "quarter",
        "year",
        "season_strength",
        "is_peak_season",
        "is_eid_month",
        "is_major_holiday_month",
        "total_capacity_nights",
        "price",
        "month_sin",
        "month_cos",
        "dynamic_anchor_price",
        "anchor_age_months",
        "is_fallback_anchor",
        "inflation_rate",
        "dynamic_anchor_inflation",
        "inflation_diff_since_anchor",
        "current_known_inflation",
    }

    all_raw_cols = set(data.columns)
    other_leaky_cols = list(
        all_raw_cols - safe_current_month_cols - set(leaky_numerical_cols)
    )

    for col in other_leaky_cols:
        df[f"{col}_lag_{base_lag}"] = df.groupby("roomId")[col].shift(base_lag)

    cols_to_drop = list(set(leaky_numerical_cols) | set(other_leaky_cols))
    if "id" in df.columns:
        cols_to_drop.append("id")

    df = df.drop(columns=[c for c in cols_to_drop if c in df.columns])

    # ======================
    # ROBUSTNESS (REDUCE OVERFITTING)
    # ======================
    for col in [
        "price_to_mean_ratio",
        "price_vs_property_avg",
        "price_vs_roll_mean_6",
        "price_base_vs_anchor",
        "price_yoy_historical",
    ]:
        if col in df.columns:
            df[col] = df[col].clip(0, 5)

    for col in ["price_roll_std_6", "price_roll_std_12"]:
        if col in df.columns:
            df[f"log_{col}"] = np.log1p(df[col])

    return df
