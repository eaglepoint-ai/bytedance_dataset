#!/usr/bin/env python3
"""
Evaluation runner for N+1 Query Optimization (Orders Aggregation).

This evaluation script:
- Tests both before and after implementations
- Counts SQL queries to verify N+1 is eliminated
- Measures performance improvements
- Generates structured reports

Run with:
    docker compose run --rm app python evaluation/evaluation.py [options]
"""
import os
import sys
import json
import timeit
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "repository_before"))
sys.path.insert(0, str(Path(__file__).parent.parent / "repository_after"))


def seed_data(session, User, Order, users=200, orders_per_user=300, active_ratio=0.8):
    """Seed test data with users and orders."""
    session.query(Order).delete()
    session.query(User).delete()
    session.commit()

    now = datetime(2024, 1, 1, 0, 0, 0)
    active_count = int(users * active_ratio)
    
    for i in range(users):
        u = User(email=f"user{i}@example.com", is_active=(i < active_count))
        session.add(u)
        session.flush()

        for j in range(orders_per_user):
            session.add(
                Order(
                    id=(i * 1000 + j + 1),
                    user_id=u.id,
                    created_at=now + timedelta(minutes=j),
                    amount=Decimal("1.00"),
                )
            )

    session.commit()
    return {
        "users": users,
        "active_users": active_count,
        "inactive_users": users - active_count,
        "orders_per_user": orders_per_user,
        "total_orders": users * orders_per_user,
    }


def count_sql_statements(engine, fn):
    """Count SQL statements executed by a function."""
    counter = {"n": 0}

    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        counter["n"] += 1

    event.listen(engine, "before_cursor_execute", before_cursor_execute)
    try:
        fn()
    finally:
        event.remove(engine, "before_cursor_execute", before_cursor_execute)

    return counter["n"]


def evaluate_implementation(implementation_name, Base, User, Order, service_func, params):
    """Evaluate a single implementation (before or after)."""
    print(f"\n{'=' * 60}")
    print(f"EVALUATING: {implementation_name.upper()}")
    print(f"{'=' * 60}")
    
    def evaluate_query_count():
        """Evaluate SQL query count for the function."""
        engine = create_engine("sqlite:///:memory:", future=True)
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine, future=True)
        session = SessionLocal()

        try:
            seed_data(session, User, Order, 
                     users=params['users'], 
                     orders_per_user=params['orders_per_user'],
                     active_ratio=params['active_ratio'])
            
            query_count = count_sql_statements(
                engine, 
                lambda: service_func(session, top_n=params['top_n'])
            )
            
            return query_count
        finally:
            session.close()

    def evaluate_performance():
        """Evaluate performance timing for the function."""
        def run_once():
            engine = create_engine("sqlite:///:memory:", future=True)
            Base.metadata.create_all(engine)
            SessionLocal = sessionmaker(bind=engine, future=True)
            session = SessionLocal()

            try:
                seed_data(session, User, Order,
                         users=params['users'],
                         orders_per_user=params['orders_per_user'],
                         active_ratio=params['active_ratio'])
                service_func(session, top_n=params['top_n'])
            finally:
                session.close()

        total_time = timeit.timeit(run_once, number=params['iterations'])
        avg_time = total_time / params['iterations']
        
        return {
            "iterations": params['iterations'],
            "total_time_seconds": total_time,
            "avg_time_seconds": avg_time,
            "avg_time_ms": avg_time * 1000,
        }
    
    # Query count evaluation
    print(f"\nQuery Count Evaluation...")
    query_count = evaluate_query_count()
    print(f"SQL statements executed: {query_count}")
    
    # Performance evaluation
    print(f"\nPerformance Evaluation ({params['iterations']} iterations)...")
    perf_metrics = evaluate_performance()
    print(f"Average time per run: {perf_metrics['avg_time_ms']:.2f}ms")
    
    return {
        "query_count": query_count,
        "performance": perf_metrics,
    }


def run_evaluation(params):
    """
    Run complete evaluation for both implementations and collect metrics.
    
    Returns dict with metrics from both before and after implementations.
    """
    print(f"\n{'=' * 60}")
    print("N+1 QUERY OPTIMIZATION EVALUATION")
    print(f"{'=' * 60}")
    
    print(f"\nParameters:")
    print(f"  Users: {params['users']}")
    print(f"  Orders per user: {params['orders_per_user']}")
    print(f"  Active ratio: {params['active_ratio']}")
    print(f"  Top N: {params['top_n']}")
    print(f"  Performance iterations: {params['iterations']}")
    
    # Import both implementations
    try:
        from repository_before.models import Base as BaseBefore, User as UserBefore, Order as OrderBefore
        from repository_before.service import latest_orders_per_active_user as func_before
        
        from repository_after.models import Base as BaseAfter, User as UserAfter, Order as OrderAfter
        from repository_after.service import latest_orders_per_active_user as func_after
    except ImportError as e:
        print(f"\nERROR: Failed to import modules: {e}")
        raise
    
    # Calculate seed stats (same for both)
    engine = create_engine("sqlite:///:memory:", future=True)
    BaseBefore.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, future=True)
    session = SessionLocal()
    
    try:
        seed_stats = seed_data(
            session, UserBefore, OrderBefore,
            users=params['users'],
            orders_per_user=params['orders_per_user'],
            active_ratio=params['active_ratio']
        )
    finally:
        session.close()
    
    print(f"\nSeed Statistics:")
    print(f"  Total users: {seed_stats['users']}")
    print(f"  Active users: {seed_stats['active_users']}")
    print(f"  Inactive users: {seed_stats['inactive_users']}")
    print(f"  Total orders: {seed_stats['total_orders']}")
    
    # Evaluate before implementation
    before_metrics = evaluate_implementation(
        "before",
        BaseBefore, UserBefore, OrderBefore,
        func_before,
        params
    )
    
    # Evaluate after implementation
    after_metrics = evaluate_implementation(
        "after",
        BaseAfter, UserAfter, OrderAfter,
        func_after,
        params
    )
    
    # Calculate improvements
    active_users = seed_stats['active_users']
    expected_before_queries = 1 + active_users  # N+1 pattern
    expected_after_queries = 3  # Optimized
    
    before_query_ok = before_metrics['query_count'] > 3  # Should have N+1
    after_query_ok = after_metrics['query_count'] <= 3  # Should be optimized
    
    speedup = before_metrics['performance']['avg_time_ms'] / after_metrics['performance']['avg_time_ms'] if after_metrics['performance']['avg_time_ms'] > 0 else 0
    improvement_pct = ((before_metrics['performance']['avg_time_ms'] - after_metrics['performance']['avg_time_ms']) / before_metrics['performance']['avg_time_ms']) * 100 if before_metrics['performance']['avg_time_ms'] > 0 else 0
    
    # Compile results
    metrics = {
        "seed_stats": seed_stats,
        "before": {
            "query_count": before_metrics['query_count'],
            "query_optimized": before_query_ok,
            "performance": before_metrics['performance'],
        },
        "after": {
            "query_count": after_metrics['query_count'],
            "query_optimized": after_query_ok,
            "performance": after_metrics['performance'],
        },
        "comparison": {
            "query_count_reduction": before_metrics['query_count'] - after_metrics['query_count'],
            "query_count_reduction_pct": ((before_metrics['query_count'] - after_metrics['query_count']) / before_metrics['query_count']) * 100 if before_metrics['query_count'] > 0 else 0,
            "speedup": round(speedup, 2),
            "improvement_pct": round(improvement_pct, 1),
        },
    }
    
    # Print summary
    print(f"\n{'=' * 60}")
    print("EVALUATION SUMMARY")
    print(f"{'=' * 60}")
    print(f"\nQuery Count:")
    print(f"  Before: {before_metrics['query_count']} queries (expected: ~{expected_before_queries} for N+1)")
    print(f"  After:  {after_metrics['query_count']} queries (expected: <= {expected_after_queries} optimized)")
    print(f"  Reduction: {metrics['comparison']['query_count_reduction']} queries ({metrics['comparison']['query_count_reduction_pct']:.1f}%)")
    
    print(f"\nPerformance:")
    print(f"  Before: {before_metrics['performance']['avg_time_ms']:.2f}ms")
    print(f"  After:  {after_metrics['performance']['avg_time_ms']:.2f}ms")
    print(f"  Speedup: {metrics['comparison']['speedup']:.2f}x faster")
    print(f"  Improvement: {metrics['comparison']['improvement_pct']:.1f}%")
    
    if after_query_ok:
        print(f"\n✅ N+1 Query Pattern Successfully Eliminated!")
    else:
        print(f"\n⚠️  Warning: After implementation still has high query count")
    
    return metrics


def main():
    """Main entry point for evaluation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run N+1 query optimization evaluation")
    parser.add_argument("--users", type=int, default=200, help="Number of users (default: 200)")
    parser.add_argument("--orders-per-user", type=int, default=300, help="Orders per user (default: 300)")
    parser.add_argument("--active-ratio", type=float, default=0.8, help="Ratio of active users (default: 0.8)")
    parser.add_argument("--top-n", type=int, default=2, help="Top N orders per user (default: 2)")
    parser.add_argument("--iterations", type=int, default=10, help="Performance test iterations (default: 10)")
    parser.add_argument("--output", type=str, help="Output JSON file path (optional)")
    
    args = parser.parse_args()
    
    params = {
        "users": args.users,
        "orders_per_user": args.orders_per_user,
        "active_ratio": args.active_ratio,
        "top_n": args.top_n,
        "iterations": args.iterations,
    }
    
    started_at = datetime.now()
    
    try:
        metrics = run_evaluation(params)
        success = True
        error_message = None
    except Exception as e:
        import traceback
        print(f"\nERROR: {str(e)}")
        traceback.print_exc()
        metrics = None
        success = False
        error_message = str(e)
    
    finished_at = datetime.now()
    duration = (finished_at - started_at).total_seconds()
    
    # Build report
    report = {
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "duration_seconds": duration,
        "success": success,
        "error": error_message,
        "parameters": params,
        "metrics": metrics,
    }
    
    # Output JSON if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\n✅ Report saved to: {output_path}")
    else:
        # Print JSON to stdout
        print(f"\n{'=' * 60}")
        print("JSON REPORT")
        print(f"{'=' * 60}")
        print(json.dumps(report, indent=2))
    
    print(f"\n{'=' * 60}")
    print(f"EVALUATION COMPLETE")
    print(f"{'=' * 60}")
    print(f"Duration: {duration:.2f}s")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
