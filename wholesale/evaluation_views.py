"""
Views for the Provider Adapter Evaluation Tool.

Provides web interface for:
1. Creating evaluation sessions
2. Uploading API response samples
3. Analyzing compatibility with existing adapters
4. Generating adapter code
5. Getting AI helper prompts
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
import json
import logging

from .models import AdapterEvaluationSession, Provider, RawVendorData
from .adapter_analyzer import (
    FieldCompatibilityAnalyzer,
    AdapterCodeGenerator,
    get_perfect_match_prompt,
    get_reuse_prompt,
    get_normalizer_prompt,
    get_new_adapter_prompt,
    get_troubleshooting_prompt
)
from .provider_mappings import (
    PROVIDER_MAPPINGS,
    PROVIDER_DATA_COMPLETENESS,
    get_provider_mapping,
    get_data_completeness,
    get_available_providers,
)

logger = logging.getLogger(__name__)


@staff_member_required
def evaluation_home(request):
    """Landing page - list all evaluation sessions."""
    sessions = AdapterEvaluationSession.objects.all()
    return render(request, 'wholesale/evaluation/home.html', {
        'sessions': sessions,
        'page_title': 'Provider Adapter Evaluation Tool'
    })


@staff_member_required
def create_session(request):
    """Step 1: Create new evaluation session."""
    if request.method == 'POST':
        provider_name = request.POST.get('provider_name')
        provider_code = request.POST.get('provider_code')
        base_url = request.POST.get('base_url')

        # Capture authentication configuration
        auth_type = request.POST.get('auth_type', 'none')
        auth_token = request.POST.get('auth_token', '')
        auth_username = request.POST.get('auth_username', '')
        auth_header_name = request.POST.get('auth_header_name', '')

        # Build extra config based on auth type
        auth_extra_config = {}
        if auth_type == 'email_param':
            auth_extra_config = {'param_name': 'user'}  # Unique Inter style
        elif auth_type == 'api_key_header' and auth_header_name:
            auth_extra_config = {'header_name': auth_header_name}

        # Create session with auth config
        session = AdapterEvaluationSession.objects.create(
            provider_name=provider_name,
            provider_code=provider_code,
            base_url=base_url,
            auth_type=auth_type,
            auth_token=auth_token if auth_token else None,
            auth_username=auth_username if auth_username else None,
            auth_header_name=auth_header_name if auth_header_name else None,
            auth_extra_config=auth_extra_config if auth_extra_config else None,
            status='draft'
        )

        messages.success(request, f'Created evaluation session for {provider_name}')
        return redirect('wholesale:evaluation_upload_samples', session_id=session.session_id)

    return render(request, 'wholesale/evaluation/create_session.html')


@staff_member_required
def upload_samples(request, session_id):
    """Step 2: Upload API response samples."""
    from django.db.models import Count

    session = get_object_or_404(AdapterEvaluationSession, session_id=session_id)

    # Get providers with raw data for Quick Load
    providers_with_data = Provider.objects.filter(
        raw_data__isnull=False
    ).distinct().annotate(
        record_count=Count('raw_data')
    ).order_by('-record_count')

    if request.method == 'POST':
        # Parse JSON samples
        try:
            sample_tours = json.loads(request.POST.get('sample_tours') or '[]')
            sample_periods = json.loads(request.POST.get('sample_periods') or '[]')
            sample_countries = json.loads(request.POST.get('sample_countries') or '[]')
            sample_flights = json.loads(request.POST.get('sample_flights') or '[]')
            sample_itineraries = json.loads(request.POST.get('sample_itineraries') or '[]')

        except json.JSONDecodeError as e:
            messages.error(request, f'Invalid JSON format: {e}')
            logger.error(f'JSON parsing error in session {session_id}: {e}', exc_info=True)
            return render(request, 'wholesale/evaluation/upload_samples.html', {
                'session': session,
                'providers_with_data': providers_with_data,
            })

        # Validate - at least tours required
        if not sample_tours:
            messages.error(request, 'Tour sample data is required')
            return render(request, 'wholesale/evaluation/upload_samples.html', {
                'session': session,
                'providers_with_data': providers_with_data,
            })

        # Validate data size (prevent huge JSON from breaking database)
        MAX_JSON_SIZE = 10 * 1024 * 1024  # 10MB limit
        for field_name, field_data in [
            ('tours', sample_tours),
            ('periods', sample_periods),
            ('countries', sample_countries),
            ('flights', sample_flights),
            ('itineraries', sample_itineraries)
        ]:
            if field_data:
                json_size = len(json.dumps(field_data))
                if json_size > MAX_JSON_SIZE:
                    messages.error(
                        request,
                        f'{field_name.capitalize()} data is too large ({json_size / 1024 / 1024:.1f}MB). '
                        f'Please reduce the sample size or split into multiple uploads.'
                    )
                    logger.warning(f'Data size limit exceeded for {field_name} in session {session_id}: {json_size} bytes')
                    return render(request, 'wholesale/evaluation/upload_samples.html', {
                        'session': session,
                        'providers_with_data': providers_with_data,
                    })

        # Save samples with comprehensive error handling
        try:
            session.sample_tours = sample_tours
            session.sample_periods = sample_periods
            session.sample_countries = sample_countries
            session.sample_flights = sample_flights
            session.sample_itineraries = sample_itineraries
            session.save()

            messages.success(request, 'Sample data saved successfully')
            return redirect('wholesale:evaluation_analyze', session_id=session.session_id)

        except Exception as e:
            messages.error(request, f'Failed to save data: {str(e)}')
            logger.error(f'Error saving evaluation session {session_id}: {e}', exc_info=True)
            return render(request, 'wholesale/evaluation/upload_samples.html', {
                'session': session,
                'providers_with_data': providers_with_data,
            })

    return render(request, 'wholesale/evaluation/upload_samples.html', {
        'session': session,
        'providers_with_data': providers_with_data,
    })


@staff_member_required
@require_http_methods(["GET"])
def ajax_load_database_samples(request):
    """Load samples from RawVendorData via AJAX."""
    from django.db.models import Count, Q

    provider_code = request.GET.get('provider')
    sample_size = int(request.GET.get('sample_size', 10))
    category_filter = request.GET.get('category', 'all')

    # Validate sample size
    MAX_SAMPLES = 50
    if sample_size > MAX_SAMPLES:
        sample_size = MAX_SAMPLES

    try:
        provider = Provider.objects.get(code=provider_code)
    except Provider.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Provider not found'})

    # Build queryset
    queryset = RawVendorData.objects.filter(provider=provider)

    # Apply category filter for Unique Inter
    if category_filter != 'all' and category_filter:
        queryset = queryset.filter(category=category_filter)

    # Get most recent samples
    samples = queryset.order_by('-fetched_at')[:sample_size]

    # Categorize samples
    tours = []
    periods = []
    countries = []
    flights = []
    itineraries = []

    for record in samples:
        data = record.raw_json

        # Skip if data is not a dict
        if not isinstance(data, dict):
            continue

        # Categorize based on endpoint_type and content
        if record.endpoint_type in ('tour', 'departure'):
            # Check if this looks like a tour (has name/title/product fields)
            if any(k in data for k in ['title', 'name', 'ProductName', 'tour_name', 'product_name']):
                tours.append(data)
            else:
                # Otherwise treat as period/departure
                periods.append(data)
        elif record.endpoint_type == 'country':
            countries.append(data)
        else:
            # For unknown types, try to infer from content
            if any(k in data for k in ['country_name', 'country', 'CountryName']):
                countries.append(data)
            elif any(k in data for k in ['start_date', 'departure_date', 'date_from']):
                periods.append(data)
            elif any(k in data for k in ['flight_no', 'flight_number', 'airline']):
                flights.append(data)
            elif any(k in data for k in ['day', 'itinerary_day', 'day_number']):
                itineraries.append(data)
            else:
                # Default to tour if it has common tour fields
                if any(k in data for k in ['title', 'name', 'code', 'tour_id']):
                    tours.append(data)

        # Extract nested arrays
        for key in ['periods', 'Periods', 'departures', 'Departures']:
            if key in data and isinstance(data[key], list):
                periods.extend(data[key])
        for key in ['flights', 'Flights']:
            if key in data and isinstance(data[key], list):
                flights.extend(data[key])
        for key in ['itineraries', 'Itineraries', 'itinerary']:
            if key in data and isinstance(data[key], list):
                itineraries.extend(data[key])
        for key in ['countries', 'Countries']:
            if key in data and isinstance(data[key], list):
                countries.extend(data[key])

    # Return formatted JSON
    return JsonResponse({
        'success': True,
        'data': {
            'tours': tours[:10],
            'periods': periods[:20],
            'countries': countries[:10],
            'flights': flights[:10],
            'itineraries': itineraries[:10],
        },
        'stats': {
            'tours': len(tours),
            'periods': len(periods),
            'countries': len(countries),
            'flights': len(flights),
            'itineraries': len(itineraries),
        }
    })


@staff_member_required
def analyze_session(request, session_id):
    """Step 3: Analyze and show compatibility results."""
    session = get_object_or_404(AdapterEvaluationSession, session_id=session_id)

    # Run analysis
    analyzer = FieldCompatibilityAnalyzer()

    # Analyze tour structure
    sample_tour = session.sample_tours[0] if session.sample_tours else {}
    tour_structure = analyzer.analyze_tour_structure(sample_tour)

    # Compare with all existing adapters
    compatibility_scores = {}
    for adapter_name in analyzer.existing_adapters:
        result = analyzer.compare_with_adapter(tour_structure, adapter_name)
        compatibility_scores[adapter_name] = result

    # Get recommendation
    recommendation = analyzer.get_recommendation(compatibility_scores)

    # Save analysis results
    session.analysis_results = {
        'tour_structure': tour_structure,
        'compatibility_scores': compatibility_scores,
        'recommendation': recommendation
    }
    session.status = 'complete'
    session.save()

    return render(request, 'wholesale/evaluation/analysis_results.html', {
        'session': session,
        'tour_structure': tour_structure,
        'compatibility_scores': compatibility_scores,
        'recommendation': recommendation
    })


@staff_member_required
def generate_code(request, session_id):
    """Step 4: Generate adapter code (or show reuse instructions)."""
    session = get_object_or_404(AdapterEvaluationSession, session_id=session_id)

    if not session.analysis_results:
        messages.error(request, 'Please run analysis first')
        return redirect('wholesale:evaluation_analyze', session_id=session_id)

    recommendation = session.analysis_results.get('recommendation', {})
    action = recommendation.get('action', 'CREATE_NEW')

    # If perfect match or reuse, show instructions instead of generating code
    if action in ['PERFECT_MATCH', 'REUSE']:
        return render(request, 'wholesale/evaluation/reuse_instructions.html', {
            'session': session,
            'recommendation': recommendation,
        })

    # For normalizer or new adapter scenarios, generate code
    generator = AdapterCodeGenerator(session)

    session.generated_service_code = generator.generate_api_service()
    session.generated_mapper_code = generator.generate_mapper()
    session.generated_command_code = generator.generate_management_command()
    session.generated_mappings_config = generator.generate_mappings_config()
    session.save()

    return render(request, 'wholesale/evaluation/generated_code.html', {
        'session': session
    })


@staff_member_required
@require_http_methods(["GET"])
def download_code(request, session_id, code_type):
    """Download generated code as file."""
    session = get_object_or_404(AdapterEvaluationSession, session_id=session_id)

    code_map = {
        'service': (session.generated_service_code, f'{session.provider_code}_service.py'),
        'mapper': (session.generated_mapper_code, f'{session.provider_code}_mapper.py'),
        'command': (session.generated_command_code, f'sync_{session.provider_code}.py'),
        'mappings': (session.generated_mappings_config, f'{session.provider_code}_mappings.py'),
    }

    if code_type not in code_map:
        return JsonResponse({'error': 'Invalid code type'}, status=400)

    code_content, filename = code_map[code_type]

    if not code_content:
        return JsonResponse({'error': 'Code not generated yet'}, status=400)

    response = HttpResponse(code_content, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@staff_member_required
@require_http_methods(["GET"])
def get_ai_prompt(request, session_id):
    """
    Get AI helper prompt for the current evaluation session.

    Returns a formatted prompt that users can copy and paste into an AI assistant
    to get help implementing the adapter based on the evaluation results.
    """
    session = get_object_or_404(AdapterEvaluationSession, session_id=session_id)

    if not session.analysis_results:
        return JsonResponse({'error': 'Analysis not completed'}, status=400)

    recommendation = session.analysis_results.get('recommendation', {})
    action = recommendation.get('action', 'CREATE_NEW')

    # Build session data for prompt generation
    session_data = {
        'provider_name': session.provider_name,
        'provider_code': session.provider_code,
        'base_url': session.base_url,
        'recommended_adapter': recommendation.get('recommended_adapter', ''),
        'score': recommendation.get('best_match_score', 0),
        'sample_data': session.sample_tours[0] if session.sample_tours else {},
    }

    # Get appropriate prompt based on action
    if action == 'PERFECT_MATCH':
        prompt = get_perfect_match_prompt(session_data)
    elif action == 'REUSE':
        prompt = get_reuse_prompt(session_data)
    elif action == 'REUSE_WITH_NORMALIZER':
        field_mappings = recommendation.get('guidance', {}).get('field_mappings', [])
        prompt = get_normalizer_prompt(session_data, field_mappings)
    else:  # CREATE_NEW
        prompt = get_new_adapter_prompt(session_data)

    return JsonResponse({
        'prompt': prompt,
        'action': action,
        'recommended_adapter': recommendation.get('recommended_adapter'),
        'score': recommendation.get('best_match_score', 0),
    })


@staff_member_required
def compare_providers(request):
    """
    Display side-by-side comparison of selected providers against standard models.

    Allows users to:
    1. Select multiple providers to compare
    2. Choose which entity types to compare (Tour, Period, Flight, Itinerary)
    3. View field coverage analysis
    4. See data completeness comparison
    5. Get recommendations for best provider choice
    """
    from .models import ProgramTour, Period, Flight, Itinerary

    # Get all available providers dynamically from PROVIDER_MAPPINGS
    available_providers = get_available_providers(include_incomplete=False)

    # Get selected providers from query params (default to all if none selected)
    selected_provider_codes = request.GET.getlist('providers')
    if not selected_provider_codes:
        selected_provider_codes = list(available_providers.keys())

    # Get entity types to compare
    entity_types = request.GET.getlist('entities')
    if not entity_types:
        entity_types = ['tour', 'period']  # Default to tour and period

    # Build comparison data
    comparison_data = {}
    for provider_code in selected_provider_codes:
        if provider_code not in PROVIDER_MAPPINGS:
            continue

        provider_info = available_providers[provider_code].copy()
        provider_info['mappings'] = PROVIDER_MAPPINGS[provider_code]
        provider_info['completeness'] = PROVIDER_DATA_COMPLETENESS.get(provider_code, {})
        comparison_data[provider_code] = provider_info

    # Define standard model fields for each entity type
    standard_fields = {
        'tour': {
            'external_id': 'Unique identifier from provider',
            'code': 'Tour/product code',
            'name': 'Tour name',
            'days': 'Duration (days)',
            'nights': 'Duration (nights)',
            'country_name': 'Primary country',
            'airline_code': 'Airline code',
            'airline_name': 'Airline name',
            'file_pdf': 'PDF document URL',
            'file_word': 'Word document URL',
            'image_url': 'Main image URL',
            'highlight': 'Tour highlights',
            'max_hotel_stars': 'Maximum hotel star rating',
            'min_hotel_stars': 'Minimum hotel star rating',
            'plane_meals': 'In-flight meals available',
            'total_meals': 'Total meals included',
            'locations': 'Visited locations',
        },
        'period': {
            'external_id': 'Unique identifier from provider',
            'code': 'Period/departure code',
            'start_date': 'Departure date',
            'end_date': 'Return date',
            'bus': 'Bus/coach information',
            'country_name': 'Country name',
            'airline_code': 'Airline code',
            'airline_name': 'Airline name',
            'airport': 'Airport information',
            'group_size': 'Group size',
            'booked': 'Seats booked',
            'seats': 'Total seats available',
            'status': 'Booking status',
            'promotion': 'Promotion flag',
            'deposit': 'Deposit amount',
            'deposit_end': 'Deposit end date',
            'com_agent': 'Agent commission',
            'com_agent_end': 'Agent commission end',
            'com_sale': 'Sales commission',
            'com_sale_end': 'Sales commission end',
            'update_date': 'Last update timestamp',
            'price_adult': 'Adult price',
            'price_child': 'Child price',
            'price_child_nb': 'Child no bed price',
            'price_infant': 'Infant price',
            'price_join_land': 'Join land service price',
            'price_single_bed': 'Single supplement',
            'price_twin_bed': 'Twin sharing price',
            'price_double_bed': 'Double sharing price',
            'price_triple_bed': 'Triple sharing price',
        },
        'flight': {
            'airline_code': 'Airline code',
            'airline_name': 'Airline name',
            'flight_no': 'Flight number',
            'route': 'Flight route',
            'departure_time': 'Departure time',
            'arrival_time': 'Arrival time',
        },
        'itinerary': {
            'external_id': 'Unique identifier',
            'day': 'Day number',
            'description': 'Day description',
            'hotel': 'Hotel name',
            'hotel_star': 'Hotel star rating',
            'breakfast': 'Breakfast included',
            'breakfast_desc': 'Breakfast description',
            'lunch': 'Lunch included',
            'lunch_desc': 'Lunch description',
            'dinner': 'Dinner included',
            'dinner_desc': 'Dinner description',
        },
    }

    # Calculate field coverage for each provider
    coverage_summary = {}
    for provider_code, provider_data in comparison_data.items():
        coverage_summary[provider_code] = {}
        for entity_type in entity_types:
            if entity_type not in standard_fields:
                continue

            standard = set(standard_fields[entity_type].keys())
            provider_fields = set(provider_data['mappings'].get(entity_type, {}).keys())
            # Count fields that have non-None mappings
            available_fields = {
                field for field in standard
                if field in provider_fields and provider_data['mappings'][entity_type][field] is not None
            }

            total = len(standard)
            available = len(available_fields)
            percentage = int((available / total * 100)) if total > 0 else 0

            coverage_summary[provider_code][entity_type] = {
                'total': total,
                'available': available,
                'percentage': percentage,
                'missing': sorted(standard - available_fields),
            }

    # Calculate overall scores and recommendations
    provider_scores = {}
    for provider_code in selected_provider_codes:
        if provider_code not in comparison_data:
            continue

        completeness = comparison_data[provider_code]['completeness']
        coverage = coverage_summary.get(provider_code, {})

        # Calculate overall field coverage score (weighted)
        tour_coverage = coverage.get('tour', {}).get('percentage', 0)
        period_coverage = coverage.get('period', {}).get('percentage', 0)

        # Overall score: field coverage (70%) + data quality (30%)
        field_score = (tour_coverage * 0.5 + period_coverage * 0.5)
        quality_score = completeness.get('data_quality_score', 50)
        overall_score = int(field_score * 0.7 + quality_score * 0.3)

        provider_scores[provider_code] = {
            'field_coverage': int(field_score),
            'quality_score': quality_score,
            'overall_score': overall_score,
            'has_flights': completeness.get('has_flights', False),
            'has_itineraries': completeness.get('has_itineraries', False),
            'has_full_pricing': completeness.get('has_full_pricing', False),
            'pricing_types': completeness.get('expected_pricing_types', 0),
        }

    # Sort providers by overall score
    ranked_providers = sorted(
        provider_scores.items(),
        key=lambda x: x[1]['overall_score'],
        reverse=True
    )

    # Generate recommendations
    recommendations = []
    if ranked_providers:
        best_provider = ranked_providers[0][0]
        best_data = ranked_providers[0][1]

        recommendations.append({
            'type': 'most_complete',
            'title': 'Most Complete Provider',
            'provider': best_provider,
            'description': f"{available_providers[best_provider]['name']} has the highest overall data completeness with {best_data['overall_score']}% score.",
        })

        # Best for tours (highest tour coverage)
        best_tour = max(
            [(code, data.get('tour', {}).get('percentage', 0))
             for code, data in coverage_summary.items()],
            key=lambda x: x[1]
        )
        if best_tour[1] > 80:
            recommendations.append({
                'type': 'best_tours',
                'title': 'Best for Tour Data',
                'provider': best_tour[0],
                'description': f"{available_providers[best_tour[0]]['name']} has {best_tour[1]}% tour field coverage.",
            })

        # Best for pricing (most pricing types)
        best_pricing = max(
            [(code, data['pricing_types']) for code, data in provider_scores.items()],
            key=lambda x: x[1]
        )
        if best_pricing[1] > 5:
            recommendations.append({
                'type': 'best_pricing',
                'title': 'Best for Pricing',
                'provider': best_pricing[0],
                'description': f"{available_providers[best_pricing[0]]['name']} supports {best_pricing[1]} different pricing types.",
            })

        # Has flights and itineraries
        complete_providers = [
            (code, available_providers[code]['name'])
            for code, data in provider_scores.items()
            if data['has_flights'] and data['has_itineraries']
        ]
        if complete_providers:
            recommendations.append({
                'type': 'complete_data',
                'title': 'Complete Flight & Itinerary Data',
                'providers': [code for code, _ in complete_providers],
                'description': ', '.join([name for _, name in complete_providers]) +
                             ' provide both flight schedules and daily itineraries.',
            })

    return render(request, 'wholesale/evaluation/provider_comparison.html', {
        'available_providers': available_providers,
        'selected_providers': selected_provider_codes,
        'entity_types': entity_types,
        'comparison_data': comparison_data,
        'standard_fields': standard_fields,
        'coverage_summary': coverage_summary,
        'provider_scores': provider_scores,
        'ranked_providers': ranked_providers,
        'recommendations': recommendations,
        'page_title': 'Provider Comparison Tool',
        # Pre-compute field lists for each entity type to avoid template dict access
        'entity_field_lists': {
            entity_type: list(standard_fields[entity_type].items())
            for entity_type in entity_types if entity_type in standard_fields
        },
    })
