#!/usr/bin/env python3
"""
Quick optimization test - tests key optimizations with minimal queries.
"""
import time
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from src.file_search_client import FileSearchClient
from src.search_manager import SearchManager
from src.search_manager_optimized import SearchManagerOptimized


def main():
    """Quick test of key optimizations."""
    print("=" * 80)
    print("QUICK OPTIMIZATION TEST")
    print("=" * 80)

    client = FileSearchClient()
    store_name = "nursing-knowledge"

    # Check store
    files = client.list_files_in_store(store_name)
    if not files:
        print(f"\nError: Store '{store_name}' not found")
        return

    total_size_mb = sum(f['size_bytes'] for f in files) / (1024 * 1024)
    print(f"\nStore: {store_name}")
    print(f"Files: {len(files)} ({total_size_mb:.2f} MB)")

    # Single test query
    query = "What are the nursing requirements?"
    print(f"\nTest Query: {query}")

    # Test configurations
    tests = [
        {
            'name': 'BASELINE - Original (Unlimited)',
            'manager': SearchManager(client),
            'params': {}
        },
        {
            'name': 'OPT 1 - Max Tokens 1024',
            'manager': SearchManagerOptimized(client),
            'params': {'max_tokens': 1024}
        },
        {
            'name': 'OPT 2 - Max Files 3 + Max Tokens 1024',
            'manager': SearchManagerOptimized(client),
            'params': {'max_files': 3, 'max_tokens': 1024}
        }
    ]

    results = []

    for test in tests:
        print("\n" + "=" * 80)
        print(f"{test['name']}")
        print("=" * 80)

        manager = test['manager']

        start = time.time()
        try:
            response = manager.search_and_generate(
                query=query,
                store_name=store_name,
                **test['params']
            )
            duration = time.time() - start

            print(f"✅ Time: {duration:.2f}s")
            print(f"Response length: {len(response.answer)} characters")
            print(f"Citations: {len(response.citations)}")

            results.append({
                'name': test['name'],
                'time': duration,
                'length': len(response.answer),
                'citations': len(response.citations)
            })

        except Exception as e:
            duration = time.time() - start
            print(f"❌ Error: {e}")
            print(f"Time before error: {duration:.2f}s")

            results.append({
                'name': test['name'],
                'time': duration,
                'error': str(e)
            })

        # Clear cache
        if hasattr(manager, 'clear_cache'):
            manager.clear_cache()

    # Summary
    print("\n" + "=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)

    baseline_time = results[0]['time']

    for i, result in enumerate(results):
        print(f"\n{result['name']}:")
        print(f"  Time: {result['time']:.2f}s")
        if 'length' in result:
            print(f"  Response: {result['length']} chars")
            print(f"  Citations: {result['citations']}")
        if 'error' in result:
            print(f"  Error: {result['error']}")

        if i > 0:  # Show improvement
            improvement = ((baseline_time - result['time']) / baseline_time * 100)
            speedup = baseline_time / result['time']
            print(f"  → Improvement: {improvement:+.1f}%")
            print(f"  → Speedup: {speedup:.2f}x")

    # Best result
    valid_results = [r for r in results if 'error' not in r]
    if len(valid_results) > 1:
        best = min(valid_results[1:], key=lambda x: x['time'])
        print(f"\n⭐ Best Configuration: {best['name']}")
        print(f"   Time: {best['time']:.2f}s")
        print(f"   vs Baseline: {((baseline_time - best['time']) / baseline_time * 100):.1f}% faster")


if __name__ == "__main__":
    main()
