import time

import pytest

from nodupe.tools.hashing import autotune_logic as at


def test_generate_test_data_length_and_available_algorithms():
    tuner = at.HashAutotuner(sample_size=4096)
    data = tuner._generate_test_data()
    assert isinstance(data, bytes)
    assert len(data) == 4096

    # standard library algorithm should be present
    assert "sha256" in tuner.available_algorithms


def test_benchmark_algorithm_invalid_raises():
    tuner = at.HashAutotuner(sample_size=128)
    with pytest.raises(ValueError):
        tuner.benchmark_algorithm("no_such_algo", b"x", iterations=1)


def test_benchmark_all_and_select_optimal_algorithm():
    tuner = at.HashAutotuner(sample_size=1024)

    # run a very small benchmark to keep tests fast
    results = tuner.benchmark_all_algorithms(iterations=1)
    assert isinstance(results, dict)
    assert "sha256" in results

    # selecting optimal algorithm should return a string and the results dict
    algo, bench = tuner.select_optimal_algorithm(iterations=1)
    assert isinstance(algo, str)
    assert isinstance(bench, dict)
    assert bench.keys() == results.keys() or set(bench.keys()).issubset(set(results.keys()))


def test_get_algorithm_recommendation_and_autotune_function():
    tuner = at.HashAutotuner(sample_size=512)
    recs = tuner.get_algorithm_recommendation(file_size_threshold=1024)

    assert set(recs.keys()) == {"small_files", "large_files", "overall"}
    assert isinstance(recs["small_files"], str)

    # autotune_hash_algorithm should return expected keys quickly
    info = at.autotune_hash_algorithm(sample_size=512, iterations=1)
    assert "optimal_algorithm" in info
    assert "benchmark_results" in info
    assert isinstance(info["has_blake3"], bool)
    assert isinstance(info["has_xxhash"], bool)


def test_create_autotuned_hasher_returns_hasher_and_results():
    # make this reasonably fast in CI
    hasher, results = at.create_autotuned_hasher(sample_size=256, iterations=1)

    # FileHasher exposes algorithm via get_algorithm()
    assert hasattr(hasher, "get_algorithm")
    assert isinstance(hasher.get_algorithm(), strthm")
    assert isinstance(hasher.get_algorithm(), strthm")
    assert isinstance(hasher.get_algorithm(), str)
    assert "optimal_algorithm" in results
    assert isinstance(results["benchmark_results"], dict)
