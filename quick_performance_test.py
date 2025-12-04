#!/usr/bin/env python3
"""
Quick performance test to verify optimization improvements.
Run this to see before/after performance with the new optimizations.
"""
import time
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from src.file_search_client import FileSearchClient
from src.search_manager import SearchManager


def quick_performance_test():
    """Test current performance with optimizations."""
    print("=" * 80)
    print("QUICK PERFORMANCE TEST - Optimized SearchManager")
    print("=" * 80)
    
    client = FileSearchClient()
    manager = SearchManager(client)
    
    # Use the store from tests
    store_name = "nursing-knowledge"
    
    # Check store exists
    files = client.list_files_in_store(store_name)
    if not files:
        print(f"❌ Store '{store_name}' not found. Please run tests first.")
        return
    
    total_size_mb = sum(f['size_bytes'] for f in files) / (1024 * 1024)
    print(f"📊 Store: {store_name}")
    print(f"📄 Files: {len(files)} ({total_size_mb:.2f} MB)")
    
    # Test configurations
    test_configs = [
        {
            'name': 'NEW DEFAULT (5 files, 2048 tokens)',
            'params': {}  # Uses new defaults: max_files=5, max_tokens=2048
        },
        {
            'name': 'AGGRESSIVE (3 files, 1024 tokens)',
            'params': {'max_files': 3, 'max_tokens': 1024}
        },
        {
            'name': 'ULTRA FAST (2 files, 512 tokens)',
            'params': {'max_files': 2, 'max_tokens': 512}
        }
    ]
    
    query = "What are the nursing requirements?"
    
    print(f"\n🔍 Testing query: {query}")
    print("=" * 80)
    
    results = []
    
    for config in test_configs:
        print(f"\n--- {config['name']} ---")
        
        # Clear cache for fair comparison
        manager.clear_cache()
        
        start_time = time.time()
        try:
            response = manager.search_and_generate(
                query=query,
                store_name=store_name,
                **config['params']
            )
            
            duration = time.time() - start_time
            
            print(f"⏱️  Time: {duration:.2f}s")
            print(f"📝 Response: {len(response.answer)} characters")
            print(f"📚 Citations: {len(response.citations)}")
            print(f"✅ Success!")
            
            results.append({
                'name': config['name'],
                'time': duration,
                'response_length': len(response.answer),
                'citations': len(response.citations),
                'success': True
            })
            
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ Error after {duration:.2f}s: {e}")
            results.append({
                'name': config['name'],
                'time': duration,
                'response_length': 0,
                'citations': 0,
                'success': False
            })
    
    # Show comparison
    print("\n" + "=" * 80)
    print("PERFORMANCE COMPARISON")
    print("=" * 80)
    
    print(f"{'Configuration':<35} {'Time':>10} {'Response':>10} {'Citations':>10}")
    print("-" * 80)
    
    for result in results:
        if result['success']:
            print(f"{result['name']:<35} {result['time']:>9.2f}s {result['response_length']:>9} {result['citations']:>9}")
        else:
            print(f"{result['name']:<35} {'FAILED':>10} {'-':>10} {'-':>10}")
    
    # Calculate improvements
    successful_results = [r for r in results if r['success']]
    if len(successful_results) >= 2:
        baseline = successful_results[0]['time']
        fastest = min(r['time'] for r in successful_results[1:])
        improvement = ((baseline - fastest) / baseline) * 100
        speedup = baseline / fastest
        
        print(f"\n📈 Performance Improvement:")
        print(f"   Baseline: {baseline:.2f}s")
        print(f"   Fastest:  {fastest:.2f}s")
        print(f"   Speedup:  {speedup:.2f}x faster")
        print(f"   Time saved: {improvement:.1f}%")
    
    # Recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    
    if any(r['time'] < 20 for r in successful_results):
        print("✅ EXCELLENT: Sub-20 second queries achieved!")
        print("   The optimizations are working well.")
    elif any(r['time'] < 30 for r in successful_results):
        print("✅ GOOD: Sub-30 second queries achieved.")
        print("   Consider further file reduction or language separation.")
    else:
        print("⚠️  NEEDS MORE OPTIMIZATION:")
        print("   Consider separating stores by language.")
        print("   Current store may have too much duplicate content.")
    
    print("\n📋 Next Steps:")
    print("1. If performance is good: Use these optimized defaults")
    print("2. If still slow: Separate multilingual content into different stores")
    print("3. For production: Implement semantic file ranking")
    
    return results


def test_optimized_qa():
    """Test the optimized Q&A method."""
    print("\n" + "=" * 80)
    print("Q&A OPTIMIZATION TEST")
    print("=" * 80)
    
    client = FileSearchClient()
    manager = SearchManager(client)
    
    store_name = "nursing-knowledge"
    questions = [
        "What documents are required?",
        "What is the eligibility criteria?",
        "What are the fees?"
    ]
    
    print(f"🎯 Testing ask_question method (uses max_files=3 by default)")
    print(f"📚 Store: {store_name}")
    
    times = []
    
    for i, question in enumerate(questions, 1):
        print(f"\n--- Question {i}/{len(questions)} ---")
        print(f"❓ {question}")
        
        start = time.time()
        try:
            response = manager.ask_question(
                question=question,
                store_name=store_name
            )
            duration = time.time() - start
            times.append(duration)
            
            print(f"⏱️  Time: {duration:.2f}s")
            print(f"📝 Answer: {len(response.answer)} chars")
            print(f"✅ Success")
            
        except Exception as e:
            duration = time.time() - start
            print(f"❌ Error after {duration:.2f}s: {e}")
    
    if times:
        avg_time = sum(times) / len(times)
        print(f"\n📊 Average Q&A time: {avg_time:.2f}s")
        if avg_time < 15:
            print("✅ EXCELLENT Q&A performance!")
        elif avg_time < 25:
            print("✅ GOOD Q&A performance")
        else:
            print("⚠️  Q&A could be faster - consider smaller store")


if __name__ == "__main__":
    print("🚀 Starting Quick Performance Test...")
    print("   This will test the new optimized defaults.")
    
    try:
        # Test general search performance
        quick_performance_test()
        
        # Test Q&A performance
        test_optimized_qa()
        
        print("\n" + "=" * 80)
        print("✅ TESTING COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()