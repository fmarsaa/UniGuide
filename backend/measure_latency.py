"""Times the recommendation pipeline (feature construction, XGBoost
probabilities, eligibility and cutoff ranking, TreeSHAP explanations) for the
three demo profiles, in preview mode so nothing is saved.

    python measure_latency.py [runs_per_profile]
"""
import contextlib
import io
import statistics
import sys
import time

with contextlib.redirect_stdout(io.StringIO()):
    import main
    from demo_profiles import DEMO_USER, PROFILES

RUNS = int(sys.argv[1]) if len(sys.argv) > 1 else 50

main.get_recommendations(PROFILES[0][1], DEMO_USER, preview=True)  # warm-up, not timed
times = []
for name, payload in PROFILES:
    for _ in range(RUNS):
        start = time.perf_counter()
        main.get_recommendations(payload, DEMO_USER, preview=True)
        times.append(time.perf_counter() - start)
times.sort()
print(f"Model: {main.MODEL_FILENAME}, version {main.model_version()}")
print(f"Requests timed: {len(times)} ({RUNS} per profile x {len(PROFILES)} profiles)")
print(f"median {statistics.median(times) * 1000:.0f} ms | 95th percentile {times[int(0.95 * len(times)) - 1] * 1000:.0f} ms | max {times[-1] * 1000:.0f} ms")
