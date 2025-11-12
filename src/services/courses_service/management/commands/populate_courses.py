"""
Management command to populate the database with comprehensive course data
Usage: python src/manage.py populate_courses
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.text import slugify
from decimal import Decimal
import random

from src.services.courses_service.models import (
    CourseCategory, Course, Module, Lesson, Quiz, Question, Answer,
    Enrollment, CourseRating, Bookmark
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate database with comprehensive course data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing course data before populating',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing course data...')
            CourseRating.objects.all().delete()
            Bookmark.objects.all().delete()
            Enrollment.objects.all().delete()
            Answer.objects.all().delete()
            Question.objects.all().delete()
            Quiz.objects.all().delete()
            Lesson.objects.all().delete()
            Module.objects.all().delete()
            Course.objects.all().delete()
            CourseCategory.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✓ Cleared existing data'))

        # Create or get instructor users
        instructor1, _ = User.objects.get_or_create(
            email='instructor1@lms.com',
            defaults={
                'username': 'instructor1',
                'first_name': 'Sarah',
                'last_name': 'Johnson',
                'is_verified': True,
                'bio': 'Blockchain expert with 10+ years of experience',
                'token_balance': Decimal('1000.00')
            }
        )
        if _:
            instructor1.set_password('password123')
            instructor1.save()

        instructor2, _ = User.objects.get_or_create(
            email='instructor2@lms.com',
            defaults={
                'username': 'instructor2',
                'first_name': 'Michael',
                'last_name': 'Chen',
                'is_verified': True,
                'bio': 'AI/ML researcher and educator',
                'token_balance': Decimal('1500.00')
            }
        )
        if _:
            instructor2.set_password('password123')
            instructor2.save()

        instructor3, _ = User.objects.get_or_create(
            email='instructor3@lms.com',
            defaults={
                'username': 'instructor3',
                'first_name': 'Emily',
                'last_name': 'Rodriguez',
                'is_verified': True,
                'bio': 'Full-stack developer and Web3 enthusiast',
                'token_balance': Decimal('800.00')
            }
        )
        if _:
            instructor3.set_password('password123')
            instructor3.save()

        self.stdout.write(self.style.SUCCESS(f'✓ Created {3} instructors'))

        # Create categories
        categories_data = [
            {
                'name': 'Blockchain Development',
                'slug': 'blockchain-development',
                'description': 'Learn blockchain technology, smart contracts, and decentralized applications',
                'icon_url': 'https://cdn-icons-png.flaticon.com/512/2092/2092663.png'
            },
            {
                'name': 'Artificial Intelligence',
                'slug': 'artificial-intelligence',
                'description': 'Master AI, machine learning, and deep learning concepts',
                'icon_url': 'https://cdn-icons-png.flaticon.com/512/2103/2103633.png'
            },
            {
                'name': 'Web Development',
                'slug': 'web-development',
                'description': 'Full-stack web development with modern frameworks',
                'icon_url': 'https://cdn-icons-png.flaticon.com/512/1055/1055645.png'
            },
            {
                'name': 'Data Science',
                'slug': 'data-science',
                'description': 'Analytics, visualization, and data-driven decision making',
                'icon_url': 'https://cdn-icons-png.flaticon.com/512/2920/2920277.png'
            },
            {
                'name': 'Cybersecurity',
                'slug': 'cybersecurity',
                'description': 'Security best practices and ethical hacking',
                'icon_url': 'https://cdn-icons-png.flaticon.com/512/1104/1104961.png'
            },
        ]

        categories = {}
        for cat_data in categories_data:
            cat, created = CourseCategory.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            categories[cat_data['slug']] = cat

        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(categories)} categories'))

        # Create comprehensive courses
        courses_data = [
            {
                'title': 'Complete Blockchain Development Bootcamp',
                'category': categories['blockchain-development'],
                'instructor': instructor1,
                'description': '''Master blockchain development from scratch! Learn Ethereum, Solidity, smart contracts, 
                and build real-world decentralized applications. This comprehensive bootcamp covers everything from blockchain 
                fundamentals to advanced DApp development, including Web3.js integration, NFT creation, and DeFi protocols.''',
                'access_type': 'token',
                'token_cost': 50,
                'price_usd': Decimal('99.99'),
                'difficulty_level': 'intermediate',
                'duration_hours': 40,
                'status': 'published',
                'is_featured': True,
                'tags': ['blockchain', 'ethereum', 'solidity', 'web3', 'smart-contracts'],
                'learning_objectives': [
                    'Understand blockchain architecture and consensus mechanisms',
                    'Write and deploy Solidity smart contracts',
                    'Build full-stack decentralized applications',
                    'Implement Web3.js for blockchain interaction',
                    'Create and trade NFTs on Ethereum',
                    'Develop DeFi protocols and understand tokenomics'
                ],
                'modules': [
                    {
                        'title': 'Blockchain Fundamentals',
                        'description': 'Core concepts of blockchain technology',
                        'lessons': [
                            {'title': 'What is Blockchain?', 'type': 'video', 'duration': 15, 'free': True},
                            {'title': 'Cryptographic Foundations', 'type': 'video', 'duration': 20},
                            {'title': 'Consensus Mechanisms', 'type': 'article', 'duration': 25},
                            {'title': 'Bitcoin vs Ethereum', 'type': 'video', 'duration': 18},
                        ]
                    },
                    {
                        'title': 'Solidity Programming',
                        'description': 'Learn the Solidity programming language',
                        'lessons': [
                            {'title': 'Introduction to Solidity', 'type': 'video', 'duration': 22},
                            {'title': 'Data Types and Variables', 'type': 'interactive', 'duration': 30},
                            {'title': 'Functions and Modifiers', 'type': 'video', 'duration': 28},
                            {'title': 'Smart Contract Security', 'type': 'article', 'duration': 35},
                        ]
                    },
                    {
                        'title': 'Building DApps',
                        'description': 'Create decentralized applications',
                        'lessons': [
                            {'title': 'Web3.js Integration', 'type': 'video', 'duration': 40},
                            {'title': 'Frontend Development', 'type': 'interactive', 'duration': 45},
                            {'title': 'Testing Smart Contracts', 'type': 'video', 'duration': 30},
                            {'title': 'Deployment Strategies', 'type': 'article', 'duration': 25},
                        ]
                    },
                ]
            },
            {
                'title': 'AI & Machine Learning Masterclass',
                'category': categories['artificial-intelligence'],
                'instructor': instructor2,
                'description': '''Become an AI expert! This comprehensive course covers machine learning fundamentals, 
                neural networks, deep learning, natural language processing, and computer vision. Build real-world AI 
                applications using Python, TensorFlow, and PyTorch.''',
                'access_type': 'token',
                'token_cost': 75,
                'price_usd': Decimal('149.99'),
                'difficulty_level': 'advanced',
                'duration_hours': 60,
                'status': 'published',
                'is_featured': True,
                'tags': ['ai', 'machine-learning', 'deep-learning', 'python', 'tensorflow', 'nlp'],
                'learning_objectives': [
                    'Master supervised and unsupervised learning algorithms',
                    'Build neural networks from scratch',
                    'Implement computer vision applications',
                    'Develop NLP models for text analysis',
                    'Deploy AI models to production',
                    'Understand ethical AI and bias mitigation'
                ],
                'modules': [
                    {
                        'title': 'Machine Learning Basics',
                        'description': 'Introduction to ML concepts',
                        'lessons': [
                            {'title': 'Introduction to ML', 'type': 'video', 'duration': 20, 'free': True},
                            {'title': 'Python for ML', 'type': 'interactive', 'duration': 30},
                            {'title': 'Linear Regression', 'type': 'video', 'duration': 35},
                            {'title': 'Classification Algorithms', 'type': 'video', 'duration': 40},
                        ]
                    },
                    {
                        'title': 'Deep Learning',
                        'description': 'Neural networks and deep learning',
                        'lessons': [
                            {'title': 'Neural Network Architecture', 'type': 'video', 'duration': 45},
                            {'title': 'Backpropagation', 'type': 'article', 'duration': 35},
                            {'title': 'Convolutional Networks', 'type': 'video', 'duration': 50},
                            {'title': 'Recurrent Networks', 'type': 'interactive', 'duration': 45},
                        ]
                    },
                    {
                        'title': 'Advanced Applications',
                        'description': 'Real-world AI projects',
                        'lessons': [
                            {'title': 'Computer Vision Projects', 'type': 'video', 'duration': 60},
                            {'title': 'NLP and Transformers', 'type': 'video', 'duration': 55},
                            {'title': 'Generative AI', 'type': 'interactive', 'duration': 50},
                            {'title': 'Model Deployment', 'type': 'article', 'duration': 40},
                        ]
                    },
                ]
            },
            {
                'title': 'Full-Stack Web Development with React & Node.js',
                'category': categories['web-development'],
                'instructor': instructor3,
                'description': '''Become a full-stack developer! Master modern web development with React, Node.js, 
                Express, MongoDB, and deployment. Build production-ready applications with authentication, databases, 
                APIs, and responsive design.''',
                'access_type': 'free',
                'token_cost': 0,
                'price_usd': Decimal('0.00'),
                'difficulty_level': 'beginner',
                'duration_hours': 35,
                'status': 'published',
                'is_featured': True,
                'tags': ['react', 'nodejs', 'javascript', 'mongodb', 'fullstack'],
                'learning_objectives': [
                    'Build modern React applications',
                    'Create RESTful APIs with Node.js',
                    'Work with MongoDB and databases',
                    'Implement authentication and authorization',
                    'Deploy applications to production',
                    'Follow industry best practices'
                ],
                'modules': [
                    {
                        'title': 'Frontend with React',
                        'description': 'Modern React development',
                        'lessons': [
                            {'title': 'React Fundamentals', 'type': 'video', 'duration': 25, 'free': True},
                            {'title': 'Components and Props', 'type': 'interactive', 'duration': 30, 'free': True},
                            {'title': 'State Management', 'type': 'video', 'duration': 35},
                            {'title': 'React Hooks', 'type': 'video', 'duration': 40},
                        ]
                    },
                    {
                        'title': 'Backend with Node.js',
                        'description': 'Server-side development',
                        'lessons': [
                            {'title': 'Node.js Basics', 'type': 'video', 'duration': 20},
                            {'title': 'Express Framework', 'type': 'interactive', 'duration': 30},
                            {'title': 'RESTful APIs', 'type': 'video', 'duration': 35},
                            {'title': 'Database Integration', 'type': 'article', 'duration': 25},
                        ]
                    },
                ]
            },
            {
                'title': 'Introduction to Python Programming',
                'category': categories['web-development'],
                'instructor': instructor2,
                'description': '''Learn Python from scratch! Perfect for beginners, this course covers Python fundamentals, 
                data structures, OOP, file handling, and popular libraries. Start your programming journey today!''',
                'access_type': 'free',
                'token_cost': 0,
                'price_usd': Decimal('0.00'),
                'difficulty_level': 'beginner',
                'duration_hours': 20,
                'status': 'published',
                'is_featured': False,
                'tags': ['python', 'programming', 'beginner'],
                'learning_objectives': [
                    'Understand Python syntax and fundamentals',
                    'Work with data structures',
                    'Write object-oriented code',
                    'Handle files and exceptions',
                    'Use popular Python libraries'
                ],
                'modules': [
                    {
                        'title': 'Python Basics',
                        'description': 'Getting started with Python',
                        'lessons': [
                            {'title': 'Installing Python', 'type': 'video', 'duration': 10, 'free': True},
                            {'title': 'Variables and Data Types', 'type': 'interactive', 'duration': 15, 'free': True},
                            {'title': 'Control Flow', 'type': 'video', 'duration': 20, 'free': True},
                        ]
                    },
                ]
            },
            {
                'title': 'Data Science with Python',
                'category': categories['data-science'],
                'instructor': instructor2,
                'description': '''Master data science! Learn data analysis, visualization, statistical modeling, 
                and machine learning with Python. Work with pandas, numpy, matplotlib, and scikit-learn.''',
                'access_type': 'token',
                'token_cost': 30,
                'price_usd': Decimal('79.99'),
                'difficulty_level': 'intermediate',
                'duration_hours': 30,
                'status': 'published',
                'is_featured': False,
                'tags': ['data-science', 'python', 'pandas', 'visualization'],
                'learning_objectives': [
                    'Perform data analysis with pandas',
                    'Create visualizations with matplotlib',
                    'Apply statistical techniques',
                    'Build predictive models',
                    'Work with real-world datasets'
                ],
                'modules': [
                    {
                        'title': 'Data Analysis',
                        'description': 'Working with data in Python',
                        'lessons': [
                            {'title': 'Pandas Fundamentals', 'type': 'video', 'duration': 30, 'free': True},
                            {'title': 'Data Cleaning', 'type': 'interactive', 'duration': 35},
                            {'title': 'Data Visualization', 'type': 'video', 'duration': 40},
                        ]
                    },
                ]
            },
            {
                'title': 'Ethical Hacking & Penetration Testing',
                'category': categories['cybersecurity'],
                'instructor': instructor1,
                'description': '''Learn ethical hacking! Master penetration testing, network security, web application 
                security, and security tools. Become a certified ethical hacker.''',
                'access_type': 'paid',
                'token_cost': 0,
                'price_usd': Decimal('199.99'),
                'difficulty_level': 'advanced',
                'duration_hours': 50,
                'status': 'published',
                'is_featured': False,
                'tags': ['cybersecurity', 'ethical-hacking', 'penetration-testing'],
                'learning_objectives': [
                    'Understand security fundamentals',
                    'Perform penetration testing',
                    'Identify vulnerabilities',
                    'Use security tools effectively',
                    'Follow ethical hacking guidelines'
                ],
                'modules': [
                    {
                        'title': 'Security Basics',
                        'description': 'Introduction to cybersecurity',
                        'lessons': [
                            {'title': 'Introduction to Ethical Hacking', 'type': 'video', 'duration': 25, 'free': True},
                            {'title': 'Security Frameworks', 'type': 'article', 'duration': 30},
                        ]
                    },
                ]
            },
        ]

        created_courses = []
        for course_data in courses_data:
            modules_data = course_data.pop('modules')
            
            course, created = Course.objects.get_or_create(
                slug=slugify(course_data['title']),
                defaults={
                    **course_data,
                    'created_by': course_data['instructor'],
                    'published_at': timezone.now() if course_data['status'] == 'published' else None,
                }
            )
            created_courses.append(course)
            
            if not created:
                continue

            # Create modules and lessons
            for module_order, module_data in enumerate(modules_data, 1):
                lessons_data = module_data.pop('lessons')
                
                module = Module.objects.create(
                    course=course,
                    title=module_data['title'],
                    description=module_data['description'],
                    order=module_order
                )

                for lesson_order, lesson_data in enumerate(lessons_data, 1):
                    Lesson.objects.create(
                        module=module,
                        title=lesson_data['title'],
                        content_type=lesson_data['type'],
                        content_url=f'https://example.com/videos/{slugify(lesson_data["title"])}',
                        duration_minutes=lesson_data['duration'],
                        order=lesson_order,
                        is_free_preview=lesson_data.get('free', False),
                        transcript=f'Transcript for {lesson_data["title"]}...',
                        resources=[
                            {'name': 'Slides', 'url': 'https://example.com/slides.pdf'},
                            {'name': 'Code Examples', 'url': 'https://github.com/example/code'}
                        ]
                    )

        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(created_courses)} courses with modules and lessons'))

        # Create sample enrollments and ratings
        demo_user, _ = User.objects.get_or_create(
            email='demo@student.com',
            defaults={
                'username': 'demostudent',
                'first_name': 'Demo',
                'last_name': 'Student',
                'is_verified': True,
                'token_balance': Decimal('200.00')
            }
        )
        if _:
            demo_user.set_password('demo123')
            demo_user.save()

        # Enroll demo user in some courses
        free_courses = [c for c in created_courses if c.access_type == 'free']
        for course in free_courses[:2]:
            enrollment, created = Enrollment.objects.get_or_create(
                user=demo_user,
                course=course,
                defaults={
                    'status': 'enrolled',
                    'progress_percentage': Decimal(random.randint(20, 80)),
                    'lessons_completed': random.randint(2, 8)
                }
            )

            # Add ratings for enrolled courses
            if created and random.choice([True, False]):
                CourseRating.objects.get_or_create(
                    user=demo_user,
                    course=course,
                    defaults={
                        'rating': random.randint(4, 5),
                        'review': 'Great course! Very informative and well-structured.'
                    }
                )

        # Generate random ratings for courses
        for course in created_courses:
            num_ratings = random.randint(10, 50)
            total_rating = 0
            
            for i in range(num_ratings):
                rating_value = random.randint(3, 5)
                total_rating += rating_value
            
            # Update course statistics
            course.total_ratings = num_ratings
            course.average_rating = Decimal(total_rating / num_ratings)
            course.total_enrollments = random.randint(50, 500)
            course.save()

        self.stdout.write(self.style.SUCCESS(f'✓ Created enrollments and ratings'))

        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('Database Population Complete!'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(f'Categories: {CourseCategory.objects.count()}')
        self.stdout.write(f'Courses: {Course.objects.count()}')
        self.stdout.write(f'Modules: {Module.objects.count()}')
        self.stdout.write(f'Lessons: {Lesson.objects.count()}')
        self.stdout.write(f'Enrollments: {Enrollment.objects.count()}')
        self.stdout.write(f'Ratings: {CourseRating.objects.count()}')
        self.stdout.write('\n' + self.style.SUCCESS('Test Accounts Created:'))
        self.stdout.write(f'Instructors: instructor1@lms.com, instructor2@lms.com, instructor3@lms.com (password: password123)')
        self.stdout.write(f'Student: demo@student.com (password: demo123)')
