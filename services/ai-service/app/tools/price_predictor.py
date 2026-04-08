"""
Price Prediction Tool
Prophet-based 7-day mandi price forecasting with sell/hold recommendation.
"""

import structlog
from datetime import date, timedelta

from app.db.postgres_client import PostgresClient

logger = structlog.get_logger(__name__)

# Lazy-load Prophet (heavy import)
_prophet_available = None


def _check_prophet():
    global _prophet_available
    if _prophet_available is None:
        try:
            from prophet import Prophet  # noqa: F401
            _prophet_available = True
        except ImportError:
            logger.warning("prophet.not_installed", msg="Falling back to simple moving average")
            _prophet_available = False
    return _prophet_available


async def predict_price(db: PostgresClient, commodity: str, market: str,
                         days_ahead: int = 7) -> dict:
    """
    Predict future prices using Prophet or fallback to moving average.
    Returns 7-day forecast with sell/hold recommendation.
    """
    from app.tools.mandi_tools import normalize_commodity
    commodity = normalize_commodity(commodity)

    # Fetch historical data (90 days for good Prophet fit)
    rows = await db.fetch_all(
        """SELECT price_date, modal_price, min_price, max_price, arrival_tonnes
           FROM mandi_prices
           WHERE commodity = $1 AND market = $2
             AND price_date >= CURRENT_DATE - 90
           ORDER BY price_date ASC""",
        commodity, market)

    if not rows or len(rows) < 10:
        return {
            "commodity": commodity,
            "market": market,
            "error": "Insufficient historical data for prediction (need at least 10 days)",
            "data_points": len(rows) if rows else 0,
        }

    history = [{"ds": r["price_date"], "y": float(r["modal_price"])} for r in rows]
    current_price = float(rows[-1]["modal_price"])

    if _check_prophet():
        forecast = _prophet_predict(history, days_ahead)
    else:
        forecast = _moving_average_predict(history, days_ahead)

    # Generate recommendation
    avg_predicted = sum(f["predicted_price"] for f in forecast) / len(forecast)
    max_predicted = max(f["predicted_price"] for f in forecast)
    max_day = next(f for f in forecast if f["predicted_price"] == max_predicted)

    price_change_pct = (avg_predicted - current_price) / current_price * 100

    if price_change_pct > 5:
        recommendation = "HOLD"
        reason = f"Prices expected to rise by {price_change_pct:.1f}%. Best selling day: {max_day['date']} at Rs.{max_predicted:.0f}/quintal"
    elif price_change_pct < -5:
        recommendation = "SELL NOW"
        reason = f"Prices expected to drop by {abs(price_change_pct):.1f}%. Current price Rs.{current_price:.0f}/quintal is favorable."
    else:
        recommendation = "SELL WHEN READY"
        reason = f"Prices expected to remain stable (±{abs(price_change_pct):.1f}%). No significant advantage in waiting."

    # Supply trend
    arrivals = [float(r["arrival_tonnes"]) for r in rows if r.get("arrival_tonnes")]
    supply_trend = "unknown"
    if len(arrivals) >= 14:
        recent_avg = sum(arrivals[-7:]) / 7
        prior_avg = sum(arrivals[-14:-7]) / 7
        if recent_avg > prior_avg * 1.1:
            supply_trend = "increasing"
        elif recent_avg < prior_avg * 0.9:
            supply_trend = "decreasing"
        else:
            supply_trend = "stable"

    return {
        "commodity": commodity,
        "market": market,
        "current_price": current_price,
        "forecast": forecast,
        "recommendation": recommendation,
        "reason": reason,
        "price_change_percent": round(price_change_pct, 2),
        "supply_trend": supply_trend,
        "model_used": "prophet" if _check_prophet() else "moving_average",
        "data_points_used": len(history),
    }


def _prophet_predict(history: list[dict], days_ahead: int) -> list[dict]:
    """Use Facebook Prophet for time series forecasting."""
    import pandas as pd
    from prophet import Prophet

    df = pd.DataFrame(history)
    df["ds"] = pd.to_datetime(df["ds"])

    model = Prophet(
        daily_seasonality=False,
        weekly_seasonality=True,
        yearly_seasonality=True,
        changepoint_prior_scale=0.05,
    )
    model.fit(df)

    future = model.make_future_dataframe(periods=days_ahead)
    forecast = model.predict(future)

    # Extract only future predictions
    future_forecast = forecast.tail(days_ahead)
    results = []
    for _, row in future_forecast.iterrows():
        results.append({
            "date": str(row["ds"].date()),
            "predicted_price": round(float(row["yhat"]), 2),
            "lower_bound": round(float(row["yhat_lower"]), 2),
            "upper_bound": round(float(row["yhat_upper"]), 2),
        })
    return results


def _moving_average_predict(history: list[dict], days_ahead: int) -> list[dict]:
    """Simple weighted moving average fallback when Prophet unavailable."""
    prices = [h["y"] for h in history]
    last_date = history[-1]["ds"]
    if isinstance(last_date, str):
        from datetime import datetime
        last_date = datetime.strptime(last_date, "%Y-%m-%d").date()

    # Weighted moving average (more weight to recent)
    window = min(14, len(prices))
    weights = list(range(1, window + 1))
    recent = prices[-window:]
    wma = sum(p * w for p, w in zip(recent, weights)) / sum(weights)

    # Calculate trend from last 7 days
    if len(prices) >= 7:
        recent_7 = prices[-7:]
        daily_trend = (recent_7[-1] - recent_7[0]) / 6
    else:
        daily_trend = 0

    # Dampen trend over forecast period
    results = []
    for i in range(1, days_ahead + 1):
        forecast_date = last_date + timedelta(days=i)
        damping = 0.9 ** i
        predicted = wma + daily_trend * i * damping

        # Simple confidence interval (widens over time)
        std_dev = (max(prices[-window:]) - min(prices[-window:])) / 4
        margin = std_dev * (1 + i * 0.1)

        results.append({
            "date": str(forecast_date),
            "predicted_price": round(predicted, 2),
            "lower_bound": round(predicted - margin, 2),
            "upper_bound": round(predicted + margin, 2),
        })
    return results
