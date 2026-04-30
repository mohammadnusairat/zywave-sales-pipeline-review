from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from pathlib import Path

app = FastAPI(title="Zywave Pipeline Variance Analyzer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

INPUT_FILE = Path(__file__).parent / "AI_Ops_Assessment.xlsx"

FORECAST_RANK = {
    "Lost": 0,
    "In The Door": 1,
    "Pipeline": 2,
    "Best Case": 3,
    "Commit": 4,
}


def load_weeks():
    excel = pd.ExcelFile(INPUT_FILE)
    return [sheet for sheet in excel.sheet_names if sheet.lower().startswith("week")]


def calculate_risk_object(row):
    """Calculate rich risk object with drivers for a deal."""
    drivers = []
    score = 0
    
    # ACV Contraction Driver
    if row["ACV Movement"] == "Contraction":
        acv_change = row["ACV Variance"]
        drivers.append({
            "label": "ACV contraction",
            "points": 2,
            "detail": f"ACV decreased by ${abs(acv_change):,.0f}"
        })
        score += 2
    
    # Close Date Push-out Driver
    if row["Close Date Movement"] == "Pushed Out":
        days = row["Close Date Variance"]
        drivers.append({
            "label": "Close date pushed out",
            "points": 1,
            "detail": f"Close date moved out by {days} days"
        })
        score += 1
    
    # Forecast Regression Driver
    if row["Forecast Direction"] == "Regression":
        forecast_var = row["Forecast Variance"]
        drivers.append({
            "label": "Forecast regression",
            "points": 2,
            "detail": f"Forecast moved from {row['Forecast_Prior']} to {row['Forecast_Current']}"
        })
        score += 2
    
    # If no drivers, add neutral driver
    if not drivers:
        drivers.append({
            "label": "No negative movement",
            "points": 0,
            "detail": "No ACV contraction, close date push-out, or forecast regression detected"
        })
    
    # Determine risk level
    if score == 0:
        level = "Low"
    elif score <= 2:
        level = "Medium"
    else:
        level = "High"
    
    return {
        "score": score,
        "level": level,
        "drivers": drivers
    }


def generate_decision_brief(summary, changed_deals):
    """Generate a rich decision brief synthesizing variance data."""
    
    # Overall read
    total_acv = summary["totalACVVariance"]
    num_deals = summary["dealsWithChanges"]
    direction = "down" if total_acv < 0 else "up"
    overall_read = f"Opportunity movement is concentrated in **{num_deals} changed {'deal' if num_deals == 1 else 'deals'}**, with **net ACV {direction} ${abs(total_acv):,.0f}**."
    
    # Top review priority - find highest risk deal
    if len(changed_deals) > 0:
        highest_risk = changed_deals.iloc[0]
        top_priority_opp = highest_risk["Opportunity"]
        
        # Build narrative about top deal using positive context + negative review drivers
        positive_details = []
        negative_details = []

        # Forecast movement
        if highest_risk["Forecast Direction"] == "Progression":
            positive_details.append(
                f"the deal progressed from **{highest_risk['Forecast_Prior']} to {highest_risk['Forecast_Current']}**"
            )
        elif highest_risk["Forecast Direction"] == "Regression":
            negative_details.append(
                f"forecast regressed from **{highest_risk['Forecast_Prior']} to {highest_risk['Forecast_Current']}**"
            )

        # Close date movement
        if highest_risk["Close Date Movement"] == "Pulled In":
            positive_details.append(
                f"the close date pulled in by **{abs(highest_risk['Close Date Variance'])}** days"
            )
        elif highest_risk["Close Date Movement"] == "Pushed Out":
            negative_details.append(
                f"the close date pushed out by **{highest_risk['Close Date Variance']}** days"
            )

        # ACV movement
        acv_movement = highest_risk["ACV Variance"]
        if acv_movement < 0:
            negative_details.append(f"ACV decreased by **${abs(acv_movement):,.0f}**")
        elif acv_movement > 0:
            positive_details.append(f"ACV increased by **${acv_movement:,.0f}**")

        negative_str = ", and ".join(negative_details)

        if positive_details and negative_details:
            positive_str = ", and ".join(positive_details)
            top_review = (
                f"Top review priority: **{top_priority_opp}**. "
                f"Although {positive_str}, the opportunity has {negative_str}. "
                f"Review is recommended to ensure alignment with opportunity strategy."
            )
        elif negative_details:
            top_review = (
                f"Top review priority: **{top_priority_opp}**. "
                f"The opportunity has {negative_str}. "
                f"Review is recommended to ensure alignment with opportunity strategy."
            )
        elif positive_details:
            positive_str = ", and ".join(positive_details)
            top_review = (
                f"Top review priority: **{top_priority_opp}**. "
                f"The opportunity shows positive movement: {positive_str}. "
                f"Review is recommended to confirm the movement is reflected accurately in the pipeline."
            )
        else:
            top_review = (
                f"Top review priority: **{top_priority_opp}**. "
                f"The opportunity changed without a clear negative risk driver. "
                f"Review is recommended to validate the pipeline update."
            )
    else:
        top_review = "No deals with concerning movements."
    
    # Forecast confidence
    progressions = summary["forecastProgressions"]
    regressions = summary["forecastRegressions"]
    if regressions == 0 and progressions > 0:
        forecast_conf = f"Forecast confidence is **strong**. {progressions} deal{'s' if progressions != 1 else ''} progressed and no regressions detected."
    elif regressions > 0 and progressions == 0:
        forecast_conf = f"Forecast confidence is **weak**. {regressions} deal{'s' if regressions != 1 else ''} regressed with no offsetting progressions."
    elif regressions > 0 and progressions > 0:
        forecast_conf = f"Forecast confidence is **mixed**. {progressions} deal{'s' if progressions != 1 else ''} progressed but {regressions} deal{'s' if regressions != 1 else ''} regressed."
    else:
        forecast_conf = "Forecast status unchanged across deals in analysis."
    
    # Recommended actions
    recommended_actions = []
    
    if summary["dealsContracted"] > 0:
        recommended_actions.append(f"Review the **{summary['dealsContracted']} {'deal' if summary['dealsContracted'] == 1 else 'deals'} with ACV contraction** for discounting, scope changes, or data corrections.")
    
    if summary["dealsPushedOut"] > 0:
        recommended_actions.append(f"Assess timing risk on **{summary['dealsPushedOut']} {'deal' if summary['dealsPushedOut'] == 1 else 'deals'}** pushed out. Confirm new close dates align with forecast categories.")
    
    if regressions > 0:
        recommended_actions.append(f"Investigate **{regressions} forecast {'regression' if regressions == 1 else 'regressions'}**. Understand whether movement reflects deal health or forecast correction.")
    
    if not recommended_actions:
        recommended_actions.append("Monitor opportunities for continued movement. Current changes are modest.")
    
    return {
        "overallRead": overall_read,
        "topReviewPriority": top_review,
        "forecastConfidence": forecast_conf,
        "recommendedActions": recommended_actions
    }


def analyze_pipeline(current_week: str):
    week_order = load_weeks()

    if current_week not in week_order:
        raise ValueError(f"{current_week} not found in workbook.")

    current_index = week_order.index(current_week)

    if current_index == 0:
        raise ValueError("Current week must be Week 2 or later.")

    prior_week = week_order[current_index - 1]

    prior_df = pd.read_excel(INPUT_FILE, sheet_name=prior_week)
    current_df = pd.read_excel(INPUT_FILE, sheet_name=current_week)

    prior_df.columns = prior_df.columns.str.strip()
    current_df.columns = current_df.columns.str.strip()

    prior_df["Close Date"] = pd.to_datetime(prior_df["Close Date"])
    current_df["Close Date"] = pd.to_datetime(current_df["Close Date"])

    merged = current_df.merge(
        prior_df,
        on="Opportunity",
        suffixes=("_Current", "_Prior"),
    )

    merged["ACV Variance"] = merged["ACV_Current"] - merged["ACV_Prior"]

    merged["Close Date Variance"] = (
        merged["Close Date_Current"] - merged["Close Date_Prior"]
    ).dt.days

    merged["Forecast Variance"] = (
        merged["Forecast_Prior"] + " → " + merged["Forecast_Current"]
    )

    merged["Forecast Direction"] = merged.apply(
        lambda row: (
            "No Change"
            if row["Forecast_Current"] == row["Forecast_Prior"]
            else "Regression"
            if FORECAST_RANK.get(row["Forecast_Current"], 0)
            < FORECAST_RANK.get(row["Forecast_Prior"], 0)
            else "Progression"
        ),
        axis=1,
    )

    merged["ACV Movement"] = merged["ACV Variance"].apply(
        lambda x: "Expansion" if x > 0 else "Contraction" if x < 0 else "No Change"
    )

    merged["Close Date Movement"] = merged["Close Date Variance"].apply(
        lambda x: "Pushed Out" if x > 0 else "Pulled In" if x < 0 else "No Change"
    )

    changed_deals = merged[
        (merged["ACV Variance"] != 0)
        | (merged["Close Date Variance"] != 0)
        | (merged["Forecast_Current"] != merged["Forecast_Prior"])
    ].copy()

    changed_deals["Risk Score"] = changed_deals.apply(
        lambda row: (
            (2 if row["ACV Movement"] == "Contraction" else 0)
            + (1 if row["Close Date Movement"] == "Pushed Out" else 0)
            + (2 if row["Forecast Direction"] == "Regression" else 0)
        ),
        axis=1,
    )

    changed_deals = changed_deals.sort_values(
        by=["Opportunity"],
        ascending=True,
    )

    variances = []

    for _, row in changed_deals.iterrows():
        risk_obj = calculate_risk_object(row)
        variances.append({
            "opportunity": row["Opportunity"],
            "acvVariance": float(row["ACV Variance"]),
            "acvMovement": row["ACV Movement"],
            "closeDateVariance": int(row["Close Date Variance"]),
            "closeDateMovement": row["Close Date Movement"],
            "forecastVariance": row["Forecast Variance"],
            "forecastDirection": row["Forecast Direction"],
            "priorACV": float(row["ACV_Prior"]),
            "currentACV": float(row["ACV_Current"]),
            "priorCloseDate": row["Close Date_Prior"].strftime("%m/%d/%Y"),
            "currentCloseDate": row["Close Date_Current"].strftime("%m/%d/%Y"),
            "priorForecast": row["Forecast_Prior"],
            "currentForecast": row["Forecast_Current"],
            "riskScore": int(row["Risk Score"]),  # Keep for backwards compatibility
            "risk": risk_obj,
        })

    summary = {
        "currentWeek": current_week,
        "priorWeek": prior_week,
        "totalDealsCompared": int(len(merged)),
        "dealsWithChanges": int(len(changed_deals)),
        "totalACVVariance": float(changed_deals["ACV Variance"].sum()),
        "dealsExpanded": int((changed_deals["ACV Movement"] == "Expansion").sum()),
        "dealsContracted": int((changed_deals["ACV Movement"] == "Contraction").sum()),
        "dealsPulledIn": int((changed_deals["Close Date Movement"] == "Pulled In").sum()),
        "dealsPushedOut": int((changed_deals["Close Date Movement"] == "Pushed Out").sum()),
        "forecastProgressions": int((changed_deals["Forecast Direction"] == "Progression").sum()),
        "forecastRegressions": int((changed_deals["Forecast Direction"] == "Regression").sum()),
    }

    # Generate decision brief instead of basic insights
    decision_brief = generate_decision_brief(summary, changed_deals)

    return {
        "weeks": week_order,
        "summary": summary,
        "variances": variances,
        "decisionBrief": decision_brief,
    }


@app.get("/weeks")
def get_weeks():
    return {"weeks": load_weeks()}


@app.get("/week-data")
def get_week_data(week: str = Query(...)):
    """Get all deals for a specific week with their data."""
    week_order = load_weeks()
    
    if week not in week_order:
        raise ValueError(f"{week} not found in workbook.")
    
    df = pd.read_excel(INPUT_FILE, sheet_name=week)
    df.columns = df.columns.str.strip()
    df["Close Date"] = pd.to_datetime(df["Close Date"])
    
    deals = []
    for _, row in df.iterrows():
        deals.append({
            "opportunity": row["Opportunity"],
            "acv": float(row["ACV"]),
            "closeDate": row["Close Date"].strftime("%m/%d/%Y"),
            "forecast": row["Forecast"],
        })
    
    return {"week": week, "deals": deals}


@app.get("/analyze")
def analyze(current_week: str = Query(..., alias="currentWeek"), category: str = Query(None)):
    """Get variance analysis with optional category filter.
    
    Categories: ACV, CloseDate, Forecast
    """
    result = analyze_pipeline(current_week)
    
    # Filter variances by category if specified
    if category:
        if category == "ACV":
            result["variances"] = [v for v in result["variances"] if v["acvVariance"] != 0]
        elif category == "CloseDate":
            result["variances"] = [v for v in result["variances"] if v["closeDateVariance"] != 0]
        elif category == "Forecast":
            result["variances"] = [v for v in result["variances"] if v["forecastDirection"] != "No Change"]
    
    return result