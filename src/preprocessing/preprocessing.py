import pandas as pd
import numpy as np


def create_continuous_calendar_grid(df):
    """
    Forces the dataframe to have a continuous row for every month
    between the min and max date for every room.
    """
    # print("Building continuous calendar grid...")
    df = df.copy()

    # 1. Ensure date is datetime
    if "date" not in df.columns:
        if pd.api.types.is_period_dtype(df["month_period"]):
            df["date"] = df["month_period"].dt.to_timestamp()
        else:
            df["date"] = pd.to_datetime(df["month_period"])

    # 2. Get global start and end dates
    min_date = df["date"].min()
    max_date = df["date"].max()

    # 3. Create a perfect range of all months
    all_months = pd.date_range(start=min_date, end=max_date, freq="MS")
    all_rooms = df["roomId"].unique()

    # 4. Create Cartesian product (Every room gets every month)
    grid = pd.MultiIndex.from_product(
        [all_rooms, all_months], names=["roomId", "date"]
    ).to_frame(index=False)

    # 5. Merge the real data onto the perfect grid
    full_df = pd.merge(grid, df, on=["roomId", "date"], how="left")

    # 6. Rebuild month_period for the newly created empty rows
    full_df["month_period"] = full_df["date"].dt.to_period("M")

    # 7. Forward/Backward fill static categorical features so they aren't NaN
    static_cols = [
        "propertyId",
        "room_cfg_room_type",
        "room_cfg_restriction_strategy",
        "room_cfg_overbooking_protection",
        "room_cfg_unit_allocation",
        "room_cfg_tier",
    ]
    for col in static_cols:
        if col in full_df.columns:
            full_df[col] = full_df.groupby("roomId")[col].transform(
                lambda x: x.ffill().bfill()
            )

    full_df = full_df.sort_values(["roomId", "date"]).reset_index(drop=True)
    # print(
    #     f"Grid built. Expanded from {len(df)} to {len(full_df)} rows to fill chronological gaps."
    # )

    return full_df


def merge_inflation(data):
    """Merge inflation data with aggregation data"""

    # For date and price col
    # print(data)
    data["price"] = data["price_per_day"]
    data = data.drop("price_per_day", axis=1)
    data["date"] = pd.to_datetime(data["month_period"].astype(str))

    # 1. Load the inflation data
    inflasi_df = pd.read_csv("../data/raw/inflasi.csv", sep=";")

    # 2. Map Indonesian months to numbers
    indo_months = {
        "Januari": "01",
        "Februari": "02",
        "Maret": "03",
        "April": "04",
        "Mei": "05",
        "Juni": "06",
        "Juli": "07",
        "Agustus": "08",
        "September": "09",
        "Oktober": "10",
        "November": "11",
        "Desember": "12",
    }

    # 3. Clean the 'Periode' column and convert to Datetime
    # Example: "Maret 2026" -> "2026-03-01"
    inflasi_df["month_str"] = inflasi_df["Periode"].apply(lambda x: x.split()[0])
    inflasi_df["year_str"] = inflasi_df["Periode"].apply(lambda x: x.split()[1])
    inflasi_df["month_num"] = inflasi_df["month_str"].map(indo_months)
    inflasi_df["date"] = pd.to_datetime(
        inflasi_df["year_str"] + "-" + inflasi_df["month_num"] + "-01"
    )

    # 4. Clean the 'Data Inflasi' column and convert to Float
    # Example: "3.48 %" -> 3.48
    inflasi_df["inflation_rate"] = (
        inflasi_df["Data Inflasi"].str.replace(" %", "").astype(float)
    )

    # Keep only what we need
    inflasi_df = inflasi_df[["date", "inflation_rate"]]

    # 5. Merge into your main 'data'
    # Assuming your main 'data' already has the 'date' column properly formatted
    data = pd.merge(data, inflasi_df, on="date", how="left")

    # Forward fill any missing inflation months just in case
    data["inflation_rate"] = data["inflation_rate"].ffill().bfill()

    return data


def initial_data_prep(data):
    """Initial data prep before feature engineering"""
    # ==========================================
    # 1. INITIAL DATA PREP
    # ==========================================
    # 1. Safely handle the PeriodDtype so Pandas doesn't crash
    if pd.api.types.is_period_dtype(data["month_period"]):
        data["date"] = data["month_period"].dt.to_timestamp()
    else:
        data["date"] = pd.to_datetime(data["month_period"])

    # 2. Extract year and month for global reference
    data["year"] = data["date"].dt.year
    data["month"] = data["date"].dt.month

    # 3. Sort correctly
    data = data.sort_values(["roomId", "date"]).reset_index(drop=True)

    # ---------------------------------------------------------
    # 🚨 OPTIONAL BUT RECOMMENDED: Run the grid fixer here! 🚨
    # data = create_continuous_calendar_grid(data)
    # ---------------------------------------------------------

    # 4. Fill missing prices (ffill/bfill or interpolate)
    data["price"] = data["price"].replace(0, np.nan)
    data["price"] = data.groupby("roomId")["price"].transform(
        lambda x: x.ffill().bfill()
    )

    # 1. Define the specific Property ID
    target_property = 515268

    # 2. Create the masks
    # Mask A: Remove everything before August 2024 for this property
    mask_pre_aug_2024 = (data["propertyId"] == target_property) & (
        data["date"] < "2024-08-01"
    )

    # Mask B: Remove specific "empty" or outlier months in 2026
    # Based on your graph, months 2, 3, 4, 6, 9, 10, 11, 12 in 2026 appear empty/missing
    months_to_remove_2026 = [2, 3, 4, 6, 9, 10, 11, 12]
    mask_empty_2026 = (
        (data["propertyId"] == target_property)
        & (data["date"].dt.year == 2026)
        & (data["date"].dt.month.isin(months_to_remove_2026))
    )

    # 3. Combine masks and filter
    # We use the tilde (~) to keep everything EXCEPT these two conditions
    data = data[~(mask_pre_aug_2024 | mask_empty_2026)].reset_index(drop=True)

    # print(f"Data cleaned for Room {target_property}. Remaining rows: {len(data)}")

    data = data[data["propertyId"] != 194837]
    data = data[data["propertyId"] != 194842]

    return data


def preprocess(df):
    # df = create_continuous_calendar_grid(df)
    # print("=================df===========", df)
    df = merge_inflation(df)
    df = initial_data_prep(df)
    return df
