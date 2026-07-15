"""Outlier check (IQR method)."""

from dataclasses import dataclass, field

import pandas as pd

_IQR_FACTOR = 1.5
_MAX_EXAMPLES = 3


@dataclass
class OutlierStats:
    column: str
    outlier_count: int
    outlier_pct: float
    lower_bound: float
    upper_bound: float
    examples: list[float] = field(default_factory=list)


def check_outliers(df: pd.DataFrame) -> list[OutlierStats]:
    """Detect outliers per numeric column using the IQR method.

    Values outside [Q1 - 1.5*IQR, Q3 + 1.5*IQR] are outliers. Non-numeric
    columns are skipped entirely (not applicable). Percentage is relative
    to the total row count, with up to three example values reported.
    """
    total_rows = len(df)
    stats = []
    for column in df.columns:
        if not pd.api.types.is_numeric_dtype(df[column]) or pd.api.types.is_bool_dtype(
            df[column]
        ):
            continue
        values = df[column].dropna()
        if values.empty:
            continue
        q1 = values.quantile(0.25)
        q3 = values.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - _IQR_FACTOR * iqr
        upper = q3 + _IQR_FACTOR * iqr
        outliers = values[(values < lower) | (values > upper)]
        count = len(outliers)
        pct = round(count / total_rows * 100, 2) if total_rows else 0.0
        stats.append(
            OutlierStats(
                column=column,
                outlier_count=count,
                outlier_pct=pct,
                lower_bound=float(lower),
                upper_bound=float(upper),
                examples=outliers.head(_MAX_EXAMPLES).tolist(),
            )
        )
    return stats
