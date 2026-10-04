"""Shows Kaggle Model Proxy spend quota (daily and monthly) and refill times.

kaggle CLI 2.2.4 has no `kaggle b quota`; this calls the same API the newer
CLI uses (kagglesdk ModelProxyApi.get_model_proxy_quotas), read-only.
Refill times come back without a time zone; every Kaggle run timestamp we
have seen is UTC, so they are printed as UTC with WAT (UTC+1) alongside.
Observed 2026-10-02: the daily refill time was exactly 24 h after the first
spend of the window (04:52:01 UTC), so the window may be rolling, not a
fixed daily reset. Run this before every full run.
"""
from datetime import timedelta

from kaggle.api.kaggle_api_extended import KaggleApi
from kagglesdk.models.types.model_proxy_api_service import ApiGetModelProxyQuotasRequest

api = KaggleApi()
api.authenticate()
with api.build_kaggle_client() as kaggle:
    r = kaggle.models.model_proxy_api_client.get_model_proxy_quotas(ApiGetModelProxyQuotasRequest())
for b in r.quota_balances:
    t = b.refill_time
    when = (f"refill {t:%Y-%m-%d %H:%M} UTC ({t + timedelta(hours=1):%Y-%m-%d %H:%M} WAT)" if t
            else "no window open (no spend yet); a window starts at the next spend")
    print(f"{b.refill_period.name.split('.')[-1]:8} used ${b.quota_used:6.2f} of ${b.total_quota_allowed:6.2f}"
          f"  remaining ${max(b.total_quota_allowed - b.quota_used, 0):6.2f}  {when}")
