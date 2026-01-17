"""
Tests for adapter analyzer functionality.
"""

from django.test import TestCase
from wholesale.adapter_analyzer import FieldCompatibilityAnalyzer


class FieldCompatibilityAnalyzerTest(TestCase):
    """Test cases for FieldCompatibilityAnalyzer."""

    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = FieldCompatibilityAnalyzer()

    def test_analyze_tour_structure(self):
        """Test tour structure analysis."""
        sample = {
            'tour_id': 'BKK001',
            'name': 'Bangkok Tour',
            'price': 25000,
            'nested': {'field1': 'value1'}
        }

        result = self.analyzer.analyze_tour_structure(sample)

        self.assertEqual(result['total_fields'], 4)
        self.assertIn('tour_id', result['fields_found'])
        self.assertEqual(result['field_types']['price'], 'int')
        self.assertIn('nested', result['nested_fields'])

    def test_compare_with_adapter_high_score(self):
        """Test comparison with high compatibility."""
        structure = {
            'fields_found': ['ProductID', 'ProductCode', 'ProductName', 'Days'],
            'field_types': {},
            'nested_fields': {}
        }

        result = self.analyzer.compare_with_adapter(structure, 'zego')

        self.assertGreater(result['score'], 0)
        self.assertIn('matching_fields', result)

    def test_get_recommendation_reuse(self):
        """Test recommendation for high compatibility."""
        scores = {
            'zego': {'score': 85},
            'unique_inter': {'score': 45}
        }

        recommendation = self.analyzer.get_recommendation(scores)

        self.assertEqual(recommendation['action'], 'REUSE')
        self.assertEqual(recommendation['recommended_adapter'], 'zego')
        self.assertFalse(recommendation['requires_normalizer'])

    def test_get_recommendation_with_normalizer(self):
        """Test recommendation for moderate compatibility."""
        scores = {
            'zego': {'score': 65},
            'unique_inter': {'score': 45}
        }

        recommendation = self.analyzer.get_recommendation(scores)

        self.assertEqual(recommendation['action'], 'REUSE_WITH_NORMALIZER')
        self.assertTrue(recommendation['requires_normalizer'])

    def test_get_recommendation_create_new(self):
        """Test recommendation for low compatibility."""
        scores = {
            'zego': {'score': 30},
            'unique_inter': {'score': 25}
        }

        recommendation = self.analyzer.get_recommendation(scores)

        self.assertEqual(recommendation['action'], 'CREATE_NEW')
        self.assertIsNone(recommendation['recommended_adapter'])
