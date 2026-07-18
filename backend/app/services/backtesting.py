from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel


class CalibrationBucket(BaseModel):
    bucket: str
    predictions: int
    average_probability: Decimal
    actual_win_rate: Decimal
    calibration_error: Decimal


class BacktestMetrics(BaseModel):
    sample_size: int
    brier_score: Decimal
    calibration_error: Decimal
    roi_if_flat_bet: Decimal
    summary: str
    buckets: list[CalibrationBucket]


def _bucket_label(probability: Decimal) -> str:
    lower = int((probability * 10).to_integral_value(rounding="ROUND_FLOOR")) * 10
    upper = min(lower + 10, 100)
    return f"{lower}-{upper}%"


def run_backtest(records) -> BacktestMetrics:
    evaluated = [record for record in records if record.result in {"win", "loss"}]
    if not evaluated:
        return BacktestMetrics(
            sample_size=0,
            brier_score=Decimal("0"),
            calibration_error=Decimal("0"),
            roi_if_flat_bet=Decimal("0"),
            summary="Sin predicciones evaluadas para backtesting.",
            buckets=[],
        )

    brier_total = Decimal("0")
    profit = Decimal("0")
    buckets: dict[str, list] = {}
    for record in evaluated:
        outcome = Decimal("1") if record.result == "win" else Decimal("0")
        probability = record.estimated_probability
        brier_total += (probability - outcome) ** 2
        if record.offered_odds is not None:
            profit += (record.offered_odds - Decimal("1")) if record.result == "win" else Decimal("-1")
        label = _bucket_label(probability)
        buckets.setdefault(label, []).append(record)

    bucket_results = []
    weighted_error = Decimal("0")
    for label, bucket_records in sorted(buckets.items()):
        avg_probability = sum((record.estimated_probability for record in bucket_records), Decimal("0")) / Decimal(
            len(bucket_records)
        )
        actual = sum((Decimal("1") for record in bucket_records if record.result == "win"), Decimal("0")) / Decimal(
            len(bucket_records)
        )
        error = abs(avg_probability - actual)
        weighted_error += error * Decimal(len(bucket_records))
        bucket_results.append(
            CalibrationBucket(
                bucket=label,
                predictions=len(bucket_records),
                average_probability=avg_probability.quantize(Decimal("0.00000001")),
                actual_win_rate=actual.quantize(Decimal("0.00000001")),
                calibration_error=error.quantize(Decimal("0.00000001")),
            )
        )

    sample_size = Decimal(len(evaluated))
    brier = (brier_total / sample_size).quantize(Decimal("0.00000001"))
    calibration_error = (weighted_error / sample_size).quantize(Decimal("0.00000001"))
    roi = (profit / sample_size).quantize(Decimal("0.00000001"))
    summary = (
        f"Backtest con {len(evaluated)} predicciones evaluadas: "
        f"Brier {brier}, calibracion {calibration_error}, ROI plano {roi}."
    )
    return BacktestMetrics(
        sample_size=len(evaluated),
        brier_score=brier,
        calibration_error=calibration_error,
        roi_if_flat_bet=roi,
        summary=summary,
        buckets=bucket_results,
    )
