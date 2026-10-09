import pytest
from src.evaluation import Evaluator

def test_hit_rate():
    results = [
        ["A", "B", "C"],
        ["X", "Y", "Z"]
    ]
    gt = [
        ["B"],
        ["M"]
    ]
    # k=2: ["A", "B"] hits "B", ["X", "Y"] misses "M". Hit rate 1/2 = 0.5
    assert Evaluator.calculate_hit_rate(results, gt, k=2) == 0.5
    # k=1: ["A"] misses "B". Hit rate 0.0
    assert Evaluator.calculate_hit_rate(results, gt, k=1) == 0.0

def test_mrr():
    results = [
        ["A", "B", "C"],
        ["X", "Y", "Z"]
    ]
    gt = [
        ["B"], # Rank 2 -> 1/2
        ["Z"]  # Rank 3 -> 1/3
    ]
    assert Evaluator.calculate_mrr(results, gt, k=3) == pytest.approx((0.5 + 1/3) / 2)
    assert Evaluator.calculate_mrr(results, gt, k=2) == pytest.approx((0.5 + 0.0) / 2)

def test_recall():
    results = [
        ["A", "B", "C"],
    ]
    gt = [
        ["B", "C"]
    ]
    # k=3: retrieves both B and C -> recall 2/2 = 1.0
    assert Evaluator.calculate_recall(results, gt, k=3) == 1.0
    # k=2: retrieves only B -> recall 1/2 = 0.5
    assert Evaluator.calculate_recall(results, gt, k=2) == 0.5

def test_empty():
    assert Evaluator.calculate_hit_rate([], [], 5) == 0.0
    assert Evaluator.calculate_mrr([], [], 5) == 0.0
    assert Evaluator.calculate_recall([], [], 5) == 0.0
