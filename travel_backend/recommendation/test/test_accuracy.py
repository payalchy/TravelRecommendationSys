"""
Automated Tests for Accuracy Checking

Tests the accuracy of recommendations using various metrics and scenarios.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from users.models import UserProfile, TravelStyle
from recommendation.models import Destination, TravelPackage, PackageItinerary
from recommendation.accuracy_checker import AccuracyMetrics, SystemAccuracyEvaluator


class AccuracyMetricsTest(TestCase):
    """Test individual accuracy metric calculations"""

    def test_precision_at_k(self):
        """Test Precision@K calculation"""
        recommendations = [1, 2, 3, 4, 5]
        relevant_items = {1, 2, 6, 7}

        # 2 out of 5 recommended items are relevant
        precision = AccuracyMetrics.calculate_precision_at_k(
            recommendations, relevant_items, k=5
        )
        self.assertAlmostEqual(precision, 0.4, places=2)

    def test_precision_at_k_empty(self):
        """Test Precision@K with empty recommendations"""
        precision = AccuracyMetrics.calculate_precision_at_k(
            [], {1, 2, 3}, k=5
        )
        self.assertEqual(precision, 0.0)

    def test_recall_at_k(self):
        """Test Recall@K calculation"""
        recommendations = [1, 2, 3, 4, 5]
        relevant_items = {1, 2}

        # 2 out of 2 relevant items are in top-5
        recall = AccuracyMetrics.calculate_recall_at_k(
            recommendations, relevant_items, k=5
        )
        self.assertAlmostEqual(recall, 1.0, places=2)

    def test_recall_at_k_partial(self):
        """Test Recall@K with partial match"""
        recommendations = [1, 2, 3, 4, 5]
        relevant_items = {1, 2, 6}

        # 2 out of 3 relevant items found
        recall = AccuracyMetrics.calculate_recall_at_k(
            recommendations, relevant_items, k=5
        )
        self.assertAlmostEqual(recall, 2/3, places=2)

    def test_dcg_calculation(self):
        """Test DCG (Discounted Cumulative Gain) calculation"""
        scores = [5, 4, 3, 2, 1]
        
        dcg = AccuracyMetrics.calculate_dcg(scores, k=5)
        
        # DCG = 5/log2(2) + 4/log2(3) + 3/log2(4) + 2/log2(5) + 1/log2(6)
        # = 5/1 + 4/1.585 + 3/2 + 2/2.322 + 1/2.585
        # ≈ 5 + 2.524 + 1.5 + 0.862 + 0.387 = 10.273
        self.assertGreater(dcg, 8.0)

    def test_ndcg_perfect_ranking(self):
        """Test NDCG with perfect ranking"""
        recommendations = [1, 2, 3, 4, 5]
        relevance_scores = {1: 5, 2: 5, 3: 5, 4: 0, 5: 0}
        
        ndcg = AccuracyMetrics.calculate_ndcg(
            recommendations, relevance_scores, k=5
        )
        
        # Perfect ranking should have NDCG close to 1.0
        self.assertGreater(ndcg, 0.95)

    def test_ndcg_poor_ranking(self):
        """Test NDCG with poor ranking"""
        recommendations = [4, 5, 1, 2, 3]
        relevance_scores = {1: 5, 2: 5, 3: 5, 4: 0, 5: 0}
        
        ndcg = AccuracyMetrics.calculate_ndcg(
            recommendations, relevance_scores, k=5
        )
        
        # Poor ranking should have lower NDCG
        self.assertLess(ndcg, 0.7)

    def test_mrr_first_position(self):
        """Test MRR when relevant item is first"""
        recommendations = [1, 2, 3, 4, 5]
        relevant_items = {1, 2, 3}
        
        mrr = AccuracyMetrics.calculate_mrr(recommendations, relevant_items)
        
        # First position = 1/1 = 1.0
        self.assertEqual(mrr, 1.0)

    def test_mrr_third_position(self):
        """Test MRR when relevant item is at position 3"""
        recommendations = [4, 5, 1, 2, 3]
        relevant_items = {1, 2, 3}
        
        mrr = AccuracyMetrics.calculate_mrr(recommendations, relevant_items)
        
        # Third position = 1/3 ≈ 0.333
        self.assertAlmostEqual(mrr, 1/3, places=2)

    def test_mrr_no_match(self):
        """Test MRR when no relevant items are recommended"""
        recommendations = [4, 5, 6]
        relevant_items = {1, 2, 3}
        
        mrr = AccuracyMetrics.calculate_mrr(recommendations, relevant_items)
        
        self.assertEqual(mrr, 0.0)

    def test_coverage(self):
        """Test catalog coverage calculation"""
        all_recommendations = {1, 2, 3, 4, 5}
        total_items = 20
        
        coverage = AccuracyMetrics.calculate_coverage(
            all_recommendations, total_items
        )
        
        # 5 out of 20 = 0.25
        self.assertAlmostEqual(coverage, 0.25, places=2)

    def test_coverage_full(self):
        """Test coverage when all items are recommended"""
        all_recommendations = set(range(1, 21))
        total_items = 20
        
        coverage = AccuracyMetrics.calculate_coverage(
            all_recommendations, total_items
        )
        
        self.assertEqual(coverage, 1.0)

    def test_budget_fitness(self):
        """Test budget fitness calculation"""
        recommendations = [1, 2, 3]
        user_budget = 50000
        budget_map = {
            1: 50000,  # Perfect match
            2: 45000,  # 10% difference
            3: 55000,  # 10% difference
        }
        
        fitness = AccuracyMetrics.calculate_budget_fitness(
            recommendations, user_budget, budget_map
        )
        
        # Average fitness: (1.0 + 0.9 + 0.9) / 3 = 0.933
        self.assertAlmostEqual(fitness, 0.933, places=2)

    def test_duration_fitness(self):
        """Test duration fitness calculation"""
        recommendations = [1, 2, 3]
        user_duration = 5
        duration_map = {
            1: 5,  # Perfect match
            2: 6,  # 20% difference
            3: 4,  # 20% difference
        }
        
        fitness = AccuracyMetrics.calculate_duration_fitness(
            recommendations, user_duration, duration_map
        )
        
        # Average fitness: (1.0 + 0.8 + 0.8) / 3 = 0.867
        self.assertAlmostEqual(fitness, 0.867, places=2)


class SystemAccuracyEvaluatorTest(TestCase):
    """Test the system accuracy evaluator with database models"""

    def setUp(self):
        """Set up test data"""
        # Create users and profiles
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        
        self.profile = UserProfile.objects.create(
            user=self.user,
            budget=50000,
            preferred_duration=5,
            preferred_season="Spring",
            latitude=27.7172,
            longitude=85.3240,
        )

        # Create destinations
        self.dest1 = Destination.objects.create(
            pName="Pokhara",
            province="Gandaki",
            latitude=28.2096,
            longitude=83.9856,
            culture=4,
            adventure=5,
            wildlife=3,
            sightseeing=5,
            history=2,
            avg_package_price=45000,
            recommended_visit_days=3
        )

        self.dest2 = Destination.objects.create(
            pName="Kathmandu",
            province="Bagmati",
            latitude=27.7172,
            longitude=85.3240,
            culture=5,
            adventure=3,
            wildlife=2,
            sightseeing=5,
            history=5,
            avg_package_price=40000,
            recommended_visit_days=4
        )

        # Create travel packages
        self.package1 = TravelPackage.objects.create(
            package_name="Pokhara Adventure",
            package_type="adventure",
            budget=45000,
            days=3,
            start_location=self.dest2,
            end_location=self.dest1,
            province="Gandaki"
        )

        self.package2 = TravelPackage.objects.create(
            package_name="Kathmandu Culture",
            package_type="culture",
            budget=40000,
            days=4,
            start_location=self.dest1,
            end_location=self.dest2,
            province="Bagmati"
        )

    def test_evaluator_initialization(self):
        """Test evaluator can be initialized"""
        evaluator = SystemAccuracyEvaluator()
        
        self.assertIsNotNone(evaluator.metrics)
        self.assertEqual(len(evaluator.test_results), 0)

    def test_single_user_evaluation(self):
        """Test evaluating a single user"""
        evaluator = SystemAccuracyEvaluator()
        
        test_preferences = {
            "budget": 50000,
            "duration": 5,
            "distance": 100,
        }
        
        relevant_packages = {self.package1.id}
        relevant_destinations = {self.dest1.id}
        
        result = evaluator.evaluate_single_user(
            self.profile,
            test_preferences,
            relevant_packages,
            relevant_destinations
        )
        
        # Verify result structure
        self.assertIn("user_id", result)
        self.assertIn("package_precision_5", result)
        self.assertIn("package_recall_5", result)
        self.assertIn("package_ndcg_5", result)
        self.assertIn("package_mrr", result)
        self.assertIn("destination_precision_5", result)
        self.assertIn("destination_recall_5", result)
        self.assertIn("destination_ndcg_5", result)
        self.assertIn("destination_mrr", result)
        
        # Verify metrics are in valid range
        self.assertGreaterEqual(result["package_precision_5"], 0.0)
        self.assertLessEqual(result["package_precision_5"], 1.0)

    def test_coverage_evaluation(self):
        """Test system coverage evaluation"""
        evaluator = SystemAccuracyEvaluator()
        
        coverage = evaluator.evaluate_system_coverage()
        
        # Verify coverage metrics
        self.assertIn("package_coverage", coverage)
        self.assertIn("destination_coverage", coverage)
        self.assertIn("packages_recommended", coverage)
        self.assertIn("destinations_recommended", coverage)
        
        # Verify values are in valid range
        self.assertGreaterEqual(coverage["package_coverage"], 0.0)
        self.assertLessEqual(coverage["package_coverage"], 1.0)

    def test_report_generation(self):
        """Test accuracy report generation"""
        evaluator = SystemAccuracyEvaluator()
        
        test_preferences = {
            "budget": 50000,
            "duration": 5,
        }
        
        # Run evaluation
        evaluator.evaluate_single_user(
            self.profile,
            test_preferences,
            {self.package1.id},
            {self.dest1.id}
        )
        
        # Generate report
        report = evaluator.generate_accuracy_report()
        
        # Verify report structure
        self.assertIn("total_tests", report)
        self.assertIn("timestamp", report)
        self.assertEqual(report["total_tests"], 1)

    def test_multiple_user_evaluation(self):
        """Test evaluating multiple users"""
        # Create another user
        user2 = User.objects.create_user(
            username="testuser2",
            password="testpass123"
        )
        
        profile2 = UserProfile.objects.create(
            user=user2,
            budget=60000,
            preferred_duration=6,
            latitude=28.5,
            longitude=84.5,
        )
        
        evaluator = SystemAccuracyEvaluator()
        
        # Evaluate both users
        for profile in [self.profile, profile2]:
            evaluator.evaluate_single_user(
                profile,
                {"budget": 50000, "duration": 5},
                {self.package1.id},
                {self.dest1.id}
            )
        
        # Verify results
        self.assertEqual(len(evaluator.test_results), 2)
        
        report = evaluator.generate_accuracy_report()
        self.assertEqual(report["total_tests"], 2)


class RecommendationAccuracyIntegrationTest(TestCase):
    """Integration tests for recommendation accuracy via API"""

    def setUp(self):
        self.client = APIClient()
        
        self.user = User.objects.create_user(
            username="apiuser",
            password="testpass123"
        )
        
        self.profile = UserProfile.objects.create(
            user=self.user,
            budget=50000,
            preferred_duration=5,
            latitude=27.7172,
            longitude=85.3240,
        )
        
        # Create test destinations
        for i in range(5):
            Destination.objects.create(
                pName=f"Destination {i}",
                province="Test",
                latitude=27.7 + i*0.1,
                longitude=85.3 + i*0.1,
                culture=4,
                adventure=3,
                wildlife=2,
                sightseeing=4,
                history=3,
                avg_package_price=50000,
                recommended_visit_days=3
            )

        # Create test packages
        for i in range(10):
            pkg = TravelPackage.objects.create(
                package_name=f"Package {i}",
                package_type="adventure",
                budget=45000 + (i*1000),
                days=3 + i,
                start_location=Destination.objects.first(),
                end_location=Destination.objects.all()[i % 5],
                province="Test"
            )

    def test_recommendation_returns_valid_results(self):
        """Test that recommendations return valid results"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post(
            "/api/recommend/",
            {
                "budget": 50000,
                "duration": 5,
                "user_latitude": 27.7172,
                "user_longitude": 85.3240,
            },
            format="json"
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("destination_results", response.data)
        
        # Check that results are non-empty
        destinations = response.data.get("destination_results", [])
        self.assertGreater(len(destinations), 0)

    def test_recommendation_respects_budget_constraint(self):
        """Test that recommendations respect budget constraints"""
        self.client.force_authenticate(user=self.user)
        
        budget = 50000
        response = self.client.post(
            "/api/recommend/",
            {
                "budget": budget,
                "duration": 5,
                "user_latitude": 27.7172,
                "user_longitude": 85.3240,
            },
            format="json"
        )
        
        if response.status_code == 200:
            packages = response.data.get("package_results", [])
            
            # Check that recommended packages are within reasonable budget range
            for package in packages[:3]:  # Check top 3 recommendations
                package_budget = package.get("budget", budget)
                # Allow 20% deviation
                self.assertLess(package_budget, budget * 1.2)

    def test_recommendation_respects_duration_constraint(self):
        """Test that recommendations respect duration constraints"""
        self.client.force_authenticate(user=self.user)
        
        duration = 5
        response = self.client.post(
            "/api/recommend/",
            {
                "budget": 50000,
                "duration": duration,
                "user_latitude": 27.7172,
                "user_longitude": 85.3240,
            },
            format="json"
        )
        
        if response.status_code == 200:
            packages = response.data.get("package_results", [])
            
            # Check that recommended packages are within reasonable duration range
            for package in packages[:3]:  # Check top 3 recommendations
                package_duration = package.get("days", duration)
                # Allow 30% deviation
                self.assertLess(package_duration, duration * 1.3)
