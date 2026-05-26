"""
Django Management Command: Check System Accuracy

Usage:
    python manage.py check_accuracy
    python manage.py check_accuracy --verbose
    python manage.py check_accuracy --num-users 10
"""

from django.core.management.base import BaseCommand
from recommendation.accuracy_checker import SystemAccuracyEvaluator
from users.models import UserProfile
from recommendation.models import TravelPackage, Destination


class Command(BaseCommand):
    help = "Check the accuracy of the travel recommendation system"

    def add_arguments(self, parser):
        parser.add_argument(
            '--num-users',
            type=int,
            default=5,
            help='Number of users to test (default: 5)',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Print detailed results for each user',
        )
        parser.add_argument(
            '--save-report',
            action='store_true',
            help='Save report to file',
        )

    def handle(self, *args, **options):
        num_users = options['num_users']
        verbose = options['verbose']
        save_report = options['save_report']

        self.stdout.write(
            self.style.SUCCESS(f"\nStarting Accuracy Evaluation ({num_users} users)...\n")
        )

        evaluator = SystemAccuracyEvaluator()

        # Get sample users
        users = UserProfile.objects.all()[:num_users]
        
        if not users.exists():
            self.stdout.write(
                self.style.ERROR("No users found in database. Create test users first.")
            )
            return

        # Evaluate each user
        for idx, user_profile in enumerate(users, 1):
            self.stdout.write(
                f"Testing User {idx}/{num_users}: {user_profile.user.username}..."
            )

            # Define test preferences
            test_preferences = {
                "budget": user_profile.budget or 50000,
                "duration": user_profile.preferred_duration or 5,
                "distance": 100,
                "travel_type": "adventure",
            }

            # Create mock relevant sets (in real scenario, use user history/ratings)
            # For demo: first 3 packages and 2 destinations are "relevant"
            all_packages = TravelPackage.objects.all()
            all_destinations = Destination.objects.all()

            relevant_packages = set(
                pkg.id for pkg in all_packages[:3]
            ) if all_packages.exists() else set()

            relevant_destinations = set(
                dest.id for dest in all_destinations[:2]
            ) if all_destinations.exists() else set()

            # Evaluate user
            result = evaluator.evaluate_single_user(
                user_profile,
                test_preferences,
                relevant_packages,
                relevant_destinations
            )

            if verbose:
                self.stdout.write(self.style.SUCCESS("\n  Results:"))
                self.stdout.write(f"    Package Precision@5: {result['package_precision_5']:.3f}")
                self.stdout.write(f"    Package Recall@5:    {result['package_recall_5']:.3f}")
                self.stdout.write(f"    Package NDCG@5:      {result['package_ndcg_5']:.3f}")
                self.stdout.write(f"    Package MRR:         {result['package_mrr']:.3f}")
                self.stdout.write(f"    Destination Precision@5: {result['destination_precision_5']:.3f}")
                self.stdout.write(f"    Destination Recall@5:    {result['destination_recall_5']:.3f}")
                self.stdout.write(f"    Destination NDCG@5:      {result['destination_ndcg_5']:.3f}")
                self.stdout.write(f"    Destination MRR:         {result['destination_mrr']:.3f}")
                self.stdout.write("")

        # Generate and print report
        self.stdout.write(
            self.style.SUCCESS("\nEvaluation Complete!\n")
        )
        evaluator.print_report()

        # Save report if requested
        if save_report:
            import json
            from datetime import datetime
            
            report = evaluator.generate_accuracy_report()
            filename = f"accuracy_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            self.stdout.write(
                self.style.SUCCESS(f"\nReport saved to: {filename}\n")
            )
