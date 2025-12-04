#!/usr/bin/env python3
"""
Compare performance between original and optimized SearchManager.
Tests multiple optimization strategies and measures improvements.
"""
import time
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from src.file_search_client import FileSearchClient
from src.search_manager import SearchManager
from src.search_manager_optimized import SearchManagerOptimized


def test_original_vs_optimized(store_name: str, queries: list):
    """
    Test original vs optimized search manager.

    Args:
        store_name: Store to search
        queries: List of test queries
    """
    print("=" * 80)
    print("PERFORMANCE COMPARISON: Original vs Optimized SearchManager")
    print("=" * 80)

    client = FileSearchClient()

    # Check store exists
    files = client.list_files_in_store(store_name)
    if not files:
        print(f"\nError: Store '{store_name}' not found or empty")
        return

    print(f"\nStore: {store_name}")
    print(f"Files: {len(files)}")
    total_size_mb = sum(f['size_bytes'] for f in files) / (1024 * 1024)
    print(f"Total size: {total_size_mb:.2f} MB")

    # Test configurations
    test_configs = [
        {
            'name': 'BASELINE - Original (No Limits)',
            'manager_class': SearchManager,
            'params': {}
        },
        {
            'name': 'OPTIMIZATION 1 - Max Tokens 2048',
            'manager_class': SearchManagerOptimized,
            'params': {'max_tokens': 2048}
        },
        {
            'name': 'OPTIMIZATION 2 - Max Tokens 1024',
            'manager_class': SearchManagerOptimized,
            'params': {'max_tokens': 1024}
        },
        {
            'name': 'OPTIMIZATION 3 - Max Files 5 + Max Tokens 2048',
            'manager_class': SearchManagerOptimized,
            'params': {'max_files': 5, 'max_tokens': 2048}
        },
        {
            'name': 'OPTIMIZATION 4 - Max Files 3 + Max Tokens 1024',
            'manager_class': SearchManagerOptimized,
            'params': {'max_files': 3, 'max_tokens': 1024}
        }
    ]

    results = []

    for config in test_configs:
        print("\n" + "=" * 80)
        print(f"Testing: {config['name']}")
        print("=" * 80)

        # Initialize manager
        manager = config['manager_class'](client)

        config_results = {
            'name': config['name'],
            'queries': []
        }

        # Test each query
        for i, query in enumerate(queries, 1):
            print(f"\n--- Query {i}/{len(queries)} ---")
            print(f"Query: {query}")

            start = time.time()
            try:
                response = manager.search_and_generate(
                    query=query,
                    store_name=store_name,
                    **config['params']
                )
                duration = time.time() - start

                print(f"  ✅ Time: {duration:.2f}s")
                print(f"  Response length: {len(response.answer)} characters")
                print(f"  Citations: {len(response.citations)}")

                config_results['queries'].append({
                    'query': query,
                    'time': duration,
                    'response_length': len(response.answer),
                    'citations': len(response.citations),
                    'success': True
                })

            except Exception as e:
                duration = time.time() - start
                print(f"  ❌ Error: {e}")
                print(f"  Time before error: {duration:.2f}s")

                config_results['queries'].append({
                    'query': query,
                    'time': duration,
                    'response_length': 0,
                    'citations': 0,
                    'success': False,
                    'error': str(e)
                })

        # Calculate statistics
        times = [q['time'] for q in config_results['queries'] if q['success']]
        if times:
            config_results['avg_time'] = sum(times) / len(times)
            config_results['min_time'] = min(times)
            config_results['max_time'] = max(times)
            config_results['total_time'] = sum(times)
            config_results['success_rate'] = len(times) / len(queries) * 100
        else:
            config_results['avg_time'] = 0
            config_results['success_rate'] = 0

        results.append(config_results)

        # Clear cache between tests for fair comparison
        if hasattr(manager, 'clear_cache'):
            manager.clear_cache()

    # Print comparison summary
    print("\n" + "=" * 80)
    print("PERFORMANCE COMPARISON SUMMARY")
    print("=" * 80)

    print(f"\nStore: {store_name}")
    print(f"Files: {len(files)} ({total_size_mb:.2f} MB)")
    print(f"Queries tested: {len(queries)}")

    print("\n" + "-" * 80)
    print(f"{'Configuration':<45} {'Avg Time':>10} {'Total':>10} {'Success':>8}")
    print("-" * 80)

    baseline_avg = results[0]['avg_time'] if results[0]['avg_time'] > 0 else 1

    for result in results:
        avg_time = result['avg_time']
        total_time = result.get('total_time', 0)
        success_rate = result['success_rate']

        improvement = ((baseline_avg - avg_time) / baseline_avg * 100) if avg_time > 0 else 0
        speedup = (baseline_avg / avg_time) if avg_time > 0 else 0

        name = result['name'][:44]
        print(f"{name:<45} {avg_time:>9.2f}s {total_time:>9.2f}s {success_rate:>7.0f}%")

        if result != results[0]:  # Don't show improvement for baseline
            print(f"  └─> Improvement: {improvement:+.1f}% | Speedup: {speedup:.2f}x faster")

    # Show detailed improvements
    print("\n" + "=" * 80)
    print("OPTIMIZATION IMPACT ANALYSIS")
    print("=" * 80)

    baseline = results[0]
    print(f"\nBaseline Performance:")
    print(f"  - Average time: {baseline['avg_time']:.2f}s")
    print(f"  - Total time: {baseline.get('total_time', 0):.2f}s")

    best_config = min(results[1:], key=lambda x: x['avg_time'] if x['avg_time'] > 0 else float('inf'))
    print(f"\nBest Optimized Configuration: {best_config['name']}")
    print(f"  - Average time: {best_config['avg_time']:.2f}s")
    print(f"  - Total time: {best_config.get('total_time', 0):.2f}s")
    print(f"  - Time saved per query: {baseline['avg_time'] - best_config['avg_time']:.2f}s")
    print(f"  - Speedup: {baseline['avg_time'] / best_config['avg_time']:.2f}x faster")
    print(f"  - Total improvement: {((baseline['avg_time'] - best_config['avg_time']) / baseline['avg_time'] * 100):.1f}%")

    # Identify key optimizations
    print("\n" + "=" * 80)
    print("KEY FINDINGS")
    print("=" * 80)

    # Compare configs to identify which optimizations help most
    max_tokens_2048 = results[1]
    max_tokens_1024 = results[2]
    max_files_5 = results[3]
    max_files_3 = results[4]

    print("\n1. Impact of Response Length Limiting:")
    print(f"   - 2048 tokens: {max_tokens_2048['avg_time']:.2f}s")
    print(f"   - 1024 tokens: {max_tokens_1024['avg_time']:.2f}s")
    if max_tokens_2048['avg_time'] > 0:
        improvement = ((max_tokens_2048['avg_time'] - max_tokens_1024['avg_time']) / max_tokens_2048['avg_time'] * 100)
        print(f"   - Benefit of shorter responses: {improvement:.1f}% faster")

    print("\n2. Impact of File Limiting:")
    print(f"   - All 10 files: {max_tokens_2048['avg_time']:.2f}s")
    print(f"   - 5 files: {max_files_5['avg_time']:.2f}s")
    print(f"   - 3 files: {max_files_3['avg_time']:.2f}s")
    if max_tokens_2048['avg_time'] > 0:
        improvement_5 = ((max_tokens_2048['avg_time'] - max_files_5['avg_time']) / max_tokens_2048['avg_time'] * 100)
        improvement_3 = ((max_tokens_2048['avg_time'] - max_files_3['avg_time']) / max_tokens_2048['avg_time'] * 100)
        print(f"   - Benefit of 5 files: {improvement_5:.1f}% faster")
        print(f"   - Benefit of 3 files: {improvement_3:.1f}% faster")

    print("\n3. Recommendations:")
    if best_config == max_files_3:
        print("   ⭐ File limiting provides the most significant improvement")
        print("   ⭐ Reducing files from 10 to 3 dramatically speeds up queries")
        print("   ⭐ Consider implementing semantic file ranking to select most relevant files")
    elif best_config == max_files_5:
        print("   ⭐ File limiting to 5 files offers good balance of speed and context")
        print("   ⭐ Consider implementing file relevance scoring")
    elif best_config == max_tokens_1024:
        print("   ⭐ Response length limiting provides significant speedup")
        print("   ⭐ 1024 tokens is often sufficient for most queries")

    print("\n4. Implementation Strategy:")
    print("   - Enable max_tokens=1024 by default for faster responses")
    print("   - Implement file ranking/filtering to select most relevant files")
    print("   - Use streaming responses for better user experience")
    print("   - Cache file objects (already implemented)")

    return results


def test_streaming_response(store_name: str, query: str):
    """Test streaming response feature."""
    print("\n" + "=" * 80)
    print("BONUS TEST: Streaming Response")
    print("=" * 80)

    client = FileSearchClient()
    manager = SearchManagerOptimized(client)

    print(f"\nQuery: {query}")
    print("\nStreaming response:")
    print("-" * 80)

    start = time.time()
    first_chunk_time = None
    chunk_count = 0

    try:
        for chunk in manager.search_and_generate_streaming(
            query=query,
            store_name=store_name,
            max_tokens=1024,
            max_files=3
        ):
            if first_chunk_time is None:
                first_chunk_time = time.time() - start
                print(f"\n(First chunk received in {first_chunk_time:.2f}s)")
            print(chunk, end='', flush=True)
            chunk_count += 1

        total_time = time.time() - start
        print("\n" + "-" * 80)
        print(f"Total time: {total_time:.2f}s")
        print(f"Time to first chunk: {first_chunk_time:.2f}s")
        print(f"Chunks received: {chunk_count}")
        print("\n⭐ Streaming provides immediate feedback to users!")

    except Exception as e:
        print(f"\n❌ Error: {e}")


def main():
    """Run comprehensive optimization comparison tests."""
    store_name = "nursing-knowledge"

    # Test queries
    queries = [
        "What are the nursing requirements?",
        "What documents are required?",
        "What is the eligibility criteria?"
    ]

    # Run comparison tests
    results = test_original_vs_optimized(store_name, queries)

    # Test streaming (optional - commented out to save time)
    # test_streaming_response(store_name, "What are the nursing requirements?")

    print("\n" + "=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
