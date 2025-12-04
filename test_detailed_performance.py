#!/usr/bin/env python3
"""
Detailed performance testing with timing breakdowns.
Identifies exactly where time is spent in the RAG pipeline.
"""
import time
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from src.file_search_client import FileSearchClient
from src.search_manager import SearchManager
import google.generativeai as genai


def measure_file_retrieval_time(client, store_name):
    """Measure time to retrieve all files from a store."""
    print("\n" + "=" * 80)
    print("BENCHMARK 1: File Retrieval Performance")
    print("=" * 80)

    file_names = client.get_files_for_generation(store_name)
    print(f"Files to retrieve: {len(file_names)}")

    # Test 1: Sequential retrieval (uncached)
    print("\n--- Test 1a: Sequential File Retrieval (Cold - No Cache) ---")
    start = time.time()
    files_retrieved = []
    for i, file_name in enumerate(file_names, 1):
        file_start = time.time()
        file_obj = genai.get_file(file_name)
        file_time = time.time() - file_start
        files_retrieved.append(file_obj)
        print(f"  File {i}/{len(file_names)}: {file_time:.3f}s - {file_name}")

    total_time_cold = time.time() - start
    avg_time_cold = total_time_cold / len(file_names)
    print(f"\n  Total time (cold): {total_time_cold:.2f}s")
    print(f"  Average per file: {avg_time_cold:.3f}s")

    # Test 1b: Sequential retrieval (cached - immediate retry)
    print("\n--- Test 1b: Sequential File Retrieval (Warm - Immediate Retry) ---")
    start = time.time()
    for i, file_name in enumerate(file_names, 1):
        file_start = time.time()
        file_obj = genai.get_file(file_name)
        file_time = time.time() - file_start
        print(f"  File {i}/{len(file_names)}: {file_time:.3f}s - {file_name}")

    total_time_warm = time.time() - start
    avg_time_warm = total_time_warm / len(file_names)
    print(f"\n  Total time (warm): {total_time_warm:.2f}s")
    print(f"  Average per file: {avg_time_warm:.3f}s")
    print(f"  Improvement: {((total_time_cold - total_time_warm) / total_time_cold * 100):.1f}% faster")

    return {
        'file_count': len(file_names),
        'cold_total': total_time_cold,
        'cold_avg': avg_time_cold,
        'warm_total': total_time_warm,
        'warm_avg': avg_time_warm
    }


def measure_query_processing_time(search_manager, store_name, query):
    """Measure time for query processing with detailed breakdowns."""
    print("\n" + "=" * 80)
    print("BENCHMARK 2: Query Processing Performance")
    print("=" * 80)
    print(f"Query: {query}")

    # Get file names
    file_names = search_manager.client.get_files_for_generation(store_name)
    print(f"Files in store: {len(file_names)}")

    # Measure each step
    timings = {}

    # Step 1: File retrieval with cache
    print("\n--- Step 1: File Retrieval (with cache) ---")
    start = time.time()
    content = [query]
    for i, file_name in enumerate(file_names, 1):
        file_start = time.time()
        file_obj = search_manager._get_file_cached(file_name)
        file_time = time.time() - file_start
        content.append(file_obj)
        if i <= 3:  # Show first 3
            print(f"  File {i}: {file_time:.3f}s (cached: {file_time < 0.01})")

    timings['file_retrieval'] = time.time() - start
    print(f"  Total file retrieval: {timings['file_retrieval']:.2f}s")

    # Step 2: Model initialization
    print("\n--- Step 2: Model Initialization ---")
    start = time.time()
    generation_config = genai.GenerationConfig(
        temperature=0.1,
        max_output_tokens=None
    )
    model = genai.GenerativeModel(
        model_name=search_manager.model_name,
        generation_config=generation_config,
        system_instruction="You are a helpful AI assistant."
    )
    timings['model_init'] = time.time() - start
    print(f"  Model initialization: {timings['model_init']:.3f}s")

    # Step 3: Content generation
    print("\n--- Step 3: Content Generation (API Call) ---")
    start = time.time()
    response = model.generate_content(content)
    timings['generation'] = time.time() - start
    print(f"  Generation time: {timings['generation']:.2f}s")
    print(f"  Response length: {len(response.text)} characters")

    # Step 4: Response processing
    print("\n--- Step 4: Response Processing ---")
    start = time.time()
    search_response = search_manager.response_handler.process_response(
        response=response,
        query=query,
        model_name=search_manager.model_name
    )
    timings['response_processing'] = time.time() - start
    print(f"  Processing time: {timings['response_processing']:.3f}s")
    print(f"  Citations found: {len(search_response.citations)}")

    # Total time
    timings['total'] = sum(timings.values())

    print("\n--- Timing Breakdown ---")
    for step, duration in timings.items():
        percentage = (duration / timings['total'] * 100) if timings['total'] > 0 else 0
        print(f"  {step:20s}: {duration:7.2f}s ({percentage:5.1f}%)")

    return timings


def measure_end_to_end_performance(search_manager, store_name):
    """Measure complete end-to-end query performance."""
    print("\n" + "=" * 80)
    print("BENCHMARK 3: End-to-End Query Performance")
    print("=" * 80)

    queries = [
        "What are the nursing requirements?",
        "What are the eligibility criteria?",
        "What documents are required?"
    ]

    results = []

    for i, query in enumerate(queries, 1):
        print(f"\n--- Query {i}/{len(queries)} ---")
        print(f"Query: {query}")

        start = time.time()
        response = search_manager.search_and_generate(query, store_name)
        total_time = time.time() - start

        print(f"  Time: {total_time:.2f}s")
        print(f"  Response length: {len(response.answer)} chars")
        print(f"  Citations: {len(response.citations)}")

        results.append({
            'query': query,
            'time': total_time,
            'response_length': len(response.answer),
            'citations': len(response.citations)
        })

    # Statistics
    times = [r['time'] for r in results]
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)

    print("\n--- Performance Statistics ---")
    print(f"  Average query time: {avg_time:.2f}s")
    print(f"  Fastest query: {min_time:.2f}s")
    print(f"  Slowest query: {max_time:.2f}s")
    print(f"  Time variation: {(max_time - min_time):.2f}s")

    return results


def measure_cache_effectiveness(search_manager, store_name):
    """Measure cache hit rates and effectiveness."""
    print("\n" + "=" * 80)
    print("BENCHMARK 4: Cache Effectiveness")
    print("=" * 80)

    # Clear cache first
    search_manager.clear_cache()

    file_names = search_manager.client.get_files_for_generation(store_name)
    print(f"Files in store: {len(file_names)}")

    # First access - should be slow
    print("\n--- First Access (Populating Cache) ---")
    start = time.time()
    for i, file_name in enumerate(file_names, 1):
        search_manager._get_file_cached(file_name)
    first_access_time = time.time() - start
    print(f"  Time: {first_access_time:.2f}s")
    print(f"  Cache populated: {len(search_manager._file_cache)} files")

    # Second access - should be fast
    print("\n--- Second Access (Reading from Cache) ---")
    start = time.time()
    for i, file_name in enumerate(file_names, 1):
        search_manager._get_file_cached(file_name)
    second_access_time = time.time() - start
    print(f"  Time: {second_access_time:.2f}s")
    print(f"  Cache hits: {len(file_names)}/{len(file_names)}")

    # Calculate improvement
    speedup = first_access_time / second_access_time if second_access_time > 0 else 0
    improvement = ((first_access_time - second_access_time) / first_access_time * 100) if first_access_time > 0 else 0

    print(f"\n--- Cache Performance ---")
    print(f"  First access: {first_access_time:.2f}s")
    print(f"  Second access: {second_access_time:.2f}s")
    print(f"  Speedup: {speedup:.1f}x faster")
    print(f"  Improvement: {improvement:.1f}%")

    return {
        'first_access': first_access_time,
        'second_access': second_access_time,
        'speedup': speedup,
        'improvement': improvement
    }


def main():
    """Run all detailed performance benchmarks."""
    print("=" * 80)
    print("DETAILED PERFORMANCE BENCHMARK")
    print("Google File Search RAG System")
    print("=" * 80)

    # Initialize
    client = FileSearchClient()
    search_manager = SearchManager(client)
    store_name = "nursing-knowledge"

    # Check store exists
    files = client.list_files_in_store(store_name)
    if not files:
        print(f"\nError: Store '{store_name}' not found or empty")
        return

    print(f"\nStore: {store_name}")
    print(f"Files: {len(files)}")
    print(f"Model: {search_manager.model_name}")

    # Run benchmarks
    file_retrieval_results = measure_file_retrieval_time(client, store_name)

    cache_results = measure_cache_effectiveness(search_manager, store_name)

    query_results = measure_query_processing_time(
        search_manager,
        store_name,
        "What are the nursing requirements?"
    )

    end_to_end_results = measure_end_to_end_performance(search_manager, store_name)

    # Final summary
    print("\n" + "=" * 80)
    print("PERFORMANCE SUMMARY")
    print("=" * 80)

    print("\n1. File Retrieval:")
    print(f"   - Cold (uncached): {file_retrieval_results['cold_total']:.2f}s for {file_retrieval_results['file_count']} files")
    print(f"   - Warm (cached): {file_retrieval_results['warm_total']:.2f}s for {file_retrieval_results['file_count']} files")
    print(f"   - Average per file (cold): {file_retrieval_results['cold_avg']:.3f}s")

    print("\n2. Cache Performance:")
    print(f"   - First access: {cache_results['first_access']:.2f}s")
    print(f"   - Cached access: {cache_results['second_access']:.2f}s")
    print(f"   - Speedup: {cache_results['speedup']:.1f}x")
    print(f"   - Cache working: {'YES' if cache_results['speedup'] > 5 else 'NO - ISSUE DETECTED'}")

    print("\n3. Query Processing Breakdown:")
    for step, duration in query_results.items():
        if step != 'total':
            percentage = (duration / query_results['total'] * 100) if query_results['total'] > 0 else 0
            print(f"   - {step:20s}: {duration:7.2f}s ({percentage:5.1f}%)")
    print(f"   - {'Total':20s}: {query_results['total']:7.2f}s")

    print("\n4. End-to-End Performance:")
    avg_time = sum(r['time'] for r in end_to_end_results) / len(end_to_end_results)
    print(f"   - Average query time: {avg_time:.2f}s")
    print(f"   - Range: {min(r['time'] for r in end_to_end_results):.2f}s - {max(r['time'] for r in end_to_end_results):.2f}s")

    # Identify bottlenecks
    print("\n" + "=" * 80)
    print("BOTTLENECK ANALYSIS")
    print("=" * 80)

    if query_results['generation'] > 30:
        print("\n🔴 PRIMARY BOTTLENECK: Content Generation (API)")
        print(f"   - Generation time: {query_results['generation']:.2f}s ({query_results['generation']/query_results['total']*100:.1f}% of total)")
        print("   - Possible causes:")
        print("     * Large number of files being processed (10 files)")
        print("     * Large file sizes requiring extensive context")
        print("     * Model processing time for complex queries")
        print("   - Optimization strategies:")
        print("     * Reduce number of files per query (implement relevance filtering)")
        print("     * Use smaller, more focused document chunks")
        print("     * Consider using Gemini 2.5 Flash for faster responses")
        print("     * Implement streaming responses for better UX")

    if query_results['file_retrieval'] > 5:
        print("\n🟡 SECONDARY BOTTLENECK: File Retrieval")
        print(f"   - Retrieval time: {query_results['file_retrieval']:.2f}s")
        print("   - Cache is working but still slow")

    if cache_results['speedup'] < 10:
        print("\n⚠️  WARNING: Cache not providing expected speedup")
        print(f"   - Expected speedup: 100x+ (network cache)")
        print(f"   - Actual speedup: {cache_results['speedup']:.1f}x")
        print("   - This suggests files are still being fetched from network")

    print("\n" + "=" * 80)
    print("BENCHMARK COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
