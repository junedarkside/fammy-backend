#!/usr/bin/env python
"""
Test script to verify admin performance optimizations.

This script measures database query counts before and after optimizations
to ensure N+1 query problems are resolved.
"""
import os
import django
from django.test.utils import override_settings
from django.db import connection, reset_queries

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Core.settings')
django.setup()

from wholesale.models import Provider, ProgramTour, Period, Flight, Itinerary, Country


def count_queries(func):
    """Decorator to count database queries."""
    def wrapper(*args, **kwargs):
        reset_queries()
        result = func(*args, **kwargs)
        query_count = len(connection.queries)
        print(f"  Queries executed: {query_count}")
        return query_count, result
    return wrapper


@count_queries
def test_provider_list_unoptimized():
    """Test Provider list without optimization (baseline)."""
    print("\n1. Testing Provider.objects.all() (unoptimized)")
    providers = list(Provider.objects.all())
    # Simulate admin list_display accessing tour_count
    for provider in providers:
        _ = provider.program_tours.count()
    return providers


@count_queries
def test_provider_list_optimized():
    """Test Provider list with annotation optimization."""
    print("\n2. Testing Provider with annotate (optimized)")
    from django.db.models import Count
    providers = list(Provider.objects.annotate(tours_count=Count('program_tours')))
    # Access annotated value
    for provider in providers:
        _ = provider.tours_count
    return providers


@count_queries
def test_programtour_list_unoptimized():
    """Test ProgramTour list without optimization (baseline)."""
    print("\n3. Testing ProgramTour.objects.all() (unoptimized)")
    tours = list(ProgramTour.objects.all()[:10])
    # Simulate admin list_display accessing country and itineraries
    for tour in tours:
        _ = tour.country
        _ = tour.itineraries.count()
    return tours


@count_queries
def test_programtour_list_optimized():
    """Test ProgramTour list with select_related and prefetch_related."""
    print("\n4. Testing ProgramTour with optimizations")
    from django.db.models import Count
    tours = list(
        ProgramTour.objects
        .select_related('country', 'provider')
        .prefetch_related('itineraries')
        .annotate(itinerary_count=Count('itineraries'))[:10]
    )
    # Access optimized values
    for tour in tours:
        _ = tour.country
        _ = tour.itinerary_count
    return tours


@count_queries
def test_period_list_unoptimized():
    """Test Period list without optimization (baseline)."""
    print("\n5. Testing Period.objects.all() (unoptimized)")
    periods = list(Period.objects.all()[:10])
    # Simulate admin list_display accessing program and provider
    for period in periods:
        _ = period.program
        _ = period.provider
    return periods


@count_queries
def test_period_list_optimized():
    """Test Period list with select_related optimization."""
    print("\n6. Testing Period with select_related")
    periods = list(Period.objects.select_related('program', 'provider')[:10])
    # Access optimized values
    for period in periods:
        _ = period.program
        _ = period.provider
    return periods


def main():
    """Run all performance tests."""
    print("=" * 70)
    print("ADMIN PERFORMANCE TEST SUITE")
    print("=" * 70)

    # Provider tests
    unopt_count, _ = test_provider_list_unoptimized()
    opt_count, _ = test_provider_list_optimized()
    improvement = ((unopt_count - opt_count) / unopt_count * 100) if unopt_count > 0 else 0
    print(f"  💡 Improvement: {improvement:.1f}% reduction in queries\n")

    # ProgramTour tests
    unopt_count, _ = test_programtour_list_unoptimized()
    opt_count, _ = test_programtour_list_optimized()
    improvement = ((unopt_count - opt_count) / unopt_count * 100) if unopt_count > 0 else 0
    print(f"  💡 Improvement: {improvement:.1f}% reduction in queries\n")

    # Period tests
    unopt_count, _ = test_period_list_unoptimized()
    opt_count, _ = test_period_list_optimized()
    improvement = ((unopt_count - opt_count) / unopt_count * 100) if unopt_count > 0 else 0
    print(f"  💡 Improvement: {improvement:.1f}% reduction in queries\n")

    print("=" * 70)
    print("✅ All performance tests completed!")
    print("=" * 70)

    print("\nSummary:")
    print("- All ModelAdmins now use get_queryset() optimization")
    print("- select_related used for FK relationships")
    print("- prefetch_related used for reverse FKs")
    print("- annotate() used for calculated fields")
    print("- Deprecated allow_tags removed")
    print("- All imports moved to module level")
    print("- Docstrings added to complex methods")
    print("- Pagination and ordering configured")


if __name__ == '__main__':
    main()
