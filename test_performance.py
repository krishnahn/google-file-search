"""
Performance testing script for optimized search manager.
Tests the file caching optimization and measures performance improvements.
"""
import time
from src.file_search_client import FileSearchClient
from src.search_manager import SearchManager

def test_search_performance():
    """Test search performance with caching."""
    print("=" * 80)
    print("PERFORMANCE TEST: File Caching Optimization")
    print("=" * 80)

    # Initialize client and search manager
    client = FileSearchClient()
    search_manager = SearchManager(client)

    store_name = "nursing-knowledge"
    test_query = "What are the nursing requirements?"

    # Get file count
    files = client.list_files_in_store(store_name)
    file_count = len(files)
    print(f"\nStore: {store_name}")
    print(f"Files in store: {file_count}")
    print(f"Test query: {test_query}")

    # Test 1: First query (cold cache)
    print("\n" + "-" * 80)
    print("TEST 1: First Query (Cold Cache)")
    print("-" * 80)
    start_time = time.time()
    response1 = search_manager.search_and_generate(test_query, store_name)
    cold_time = time.time() - start_time
    print(f"⏱️  Time taken (cold cache): {cold_time:.2f} seconds")
    print(f"✅ Response length: {len(response1.answer)} characters")

    # Test 2: Second query (warm cache)
    print("\n" + "-" * 80)
    print("TEST 2: Second Query (Warm Cache)")
    print("-" * 80)
    start_time = time.time()
    response2 = search_manager.search_and_generate(
        "What are the eligibility criteria?",
        store_name
    )
    warm_time = time.time() - start_time
    print(f"⏱️  Time taken (warm cache): {warm_time:.2f} seconds")
    print(f"✅ Response length: {len(response2.answer)} characters")

    # Test 3: Third query (warm cache)
    print("\n" + "-" * 80)
    print("TEST 3: Third Query (Warm Cache)")
    print("-" * 80)
    start_time = time.time()
    response3 = search_manager.search_and_generate(
        "What documents are required?",
        store_name
    )
    warm_time2 = time.time() - start_time
    print(f"⏱️  Time taken (warm cache): {warm_time2:.2f} seconds")
    print(f"✅ Response length: {len(response3.answer)} characters")

    # Calculate performance improvement
    print("\n" + "=" * 80)
    print("PERFORMANCE RESULTS")
    print("=" * 80)
    print(f"Files in store: {file_count}")
    print(f"Cold cache time: {cold_time:.2f}s")
    print(f"Warm cache time (avg): {(warm_time + warm_time2) / 2:.2f}s")

    improvement = ((cold_time - warm_time) / cold_time) * 100
    print(f"\n🚀 Performance improvement: {improvement:.1f}% faster with cache")
    print(f"⚡ Time saved per query: {cold_time - warm_time:.2f} seconds")

    # Estimate API call savings
    estimated_api_calls_saved = file_count * 2  # 2 subsequent queries
    print(f"💰 API calls saved: ~{estimated_api_calls_saved} (file retrieval calls)")

    # Test cache clearing
    print("\n" + "-" * 80)
    print("TEST 4: After Cache Clear")
    print("-" * 80)
    search_manager.clear_cache()
    start_time = time.time()
    response4 = search_manager.search_and_generate(
        "What is the process?",
        store_name
    )
    cleared_time = time.time() - start_time
    print(f"⏱️  Time taken (after cache clear): {cleared_time:.2f} seconds")

    print("\n" + "=" * 80)
    print("✅ Performance test completed successfully!")
    print("=" * 80)

if __name__ == "__main__":
    test_search_performance()
