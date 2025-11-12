"""
Management command to index courses to Qdrant vector database
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from src.services.ai_recommendations.recommendation_engine import QdrantRecommendationEngine
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Index all published courses to Qdrant vector database for AI recommendations'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-index all courses (clears existing data)',
        )
        
        parser.add_argument(
            '--course-id',
            type=int,
            help='Index a specific course by ID',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Starting course indexing to Qdrant...'))
        
        try:
            # Get a dummy admin user for the engine
            admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                self.stdout.write(self.style.ERROR('❌ No admin user found. Please create a superuser first.'))
                return
            
            # Initialize the engine
            engine = QdrantRecommendationEngine(admin_user)
            
            # Handle specific course indexing
            if options['course_id']:
                self.index_single_course(engine, options['course_id'])
                return
            
            # Handle force re-indexing
            if options['force']:
                self.stdout.write(self.style.WARNING('⚠️  Force mode enabled. Clearing existing collection...'))
                try:
                    engine.qdrant_client.delete_collection(engine.collection_name)
                    self.stdout.write(self.style.SUCCESS('✅ Collection cleared'))
                    engine._ensure_collection_exists()
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'Collection not found or already cleared: {e}'))
            
            # Bulk index all courses
            self.stdout.write(self.style.MIGRATE_HEADING('📊 Indexing all published courses...'))
            result = engine.bulk_index_courses()
            
            if result['status'] == 'success':
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Successfully indexed {result["indexed"]} courses to Qdrant')
                )
                self.stdout.write(
                    self.style.SUCCESS('🎉 Course recommendations are now powered by AI!')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ Indexing failed: {result["message"]}')
                )
        
        except Exception as e:
            logger.error(f'Error in index_courses_to_qdrant command: {str(e)}', exc_info=True)
            self.stdout.write(
                self.style.ERROR(f'❌ Unexpected error: {str(e)}')
            )
    
    def index_single_course(self, engine, course_id):
        """Index a single course by ID"""
        try:
            from src.services.courses_service.models import Course
            
            self.stdout.write(self.style.MIGRATE_HEADING(f'📌 Indexing course ID: {course_id}'))
            
            course = Course.objects.get(id=course_id, status='published')
            success = engine.index_course_to_qdrant(course)
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Successfully indexed: "{course.title}"')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ Failed to index course {course_id}')
                )
        
        except Course.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'❌ Course with ID {course_id} not found or not published')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error indexing course: {str(e)}')
            )
