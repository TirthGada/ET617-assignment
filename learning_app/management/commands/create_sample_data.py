from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from learning_app.models import Course, Content, Quiz


class Command(BaseCommand):
    help = 'Create sample data for the learning platform'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating sample data...'))

        # Create only one sample course
        course1, created = Course.objects.get_or_create(
            title="Web Development Fundamentals",
            defaults={
                'description': "Learn the basics of web development including HTML, CSS, and JavaScript. This course covers fundamental concepts needed to build modern web applications."
            }
        )

        # Create sample content for Web Development course - 1 text, 1 video, 1 quiz
        content1 = Content.objects.get_or_create(
            course=course1,
            title="Introduction to HTML",
            defaults={
                'content_type': 'text',
                'text_content': '''HTML (HyperText Markup Language) is the standard markup language for creating web pages. It describes the structure of a web page using markup elements.

Key HTML concepts:
- Elements and tags
- Attributes 
- Document structure
- Semantic HTML

HTML forms the backbone of all web pages. Understanding HTML is essential for web development.

Practice exercises:
1. Create a basic HTML page
2. Use different heading levels
3. Add paragraphs and links
4. Create lists and tables

Remember: HTML provides structure, CSS provides styling, and JavaScript provides interactivity.''',
                'order': 1
            }
        )[0]

        content2 = Content.objects.get_or_create(
            course=course1,
            title="CSS Styling Basics Video",
            defaults={
                'content_type': 'video',
                'video_url': 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
                'video_duration': 120,
                'order': 2
            }
        )[0]

        content3 = Content.objects.get_or_create(
            course=course1,
            title="HTML Knowledge Check",
            defaults={
                'content_type': 'quiz',
                'order': 3
            }
        )[0]

        # Create quiz for HTML content
        Quiz.objects.get_or_create(
            content=content3,
            defaults={
                'question': 'What does HTML stand for?',
                'option_a': 'HyperText Markup Language',
                'option_b': 'High Tech Modern Language',
                'option_c': 'Home Tool Markup Language', 
                'option_d': 'Hyperlink and Text Markup Language',
                'correct_answer': 'A'
            }
        )

        # Create a test user
        if not User.objects.filter(username='testuser').exists():
            User.objects.create_user(
                username='testuser',
                email='test@example.com',
                password='testpass123'
            )
            self.stdout.write(self.style.SUCCESS('Created test user: testuser / testpass123'))

        # Create admin user if not exists
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123'
            )
            self.stdout.write(self.style.SUCCESS('Created admin user: admin / admin123'))

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created sample data:\n'
                f'- {Course.objects.count()} course\n'
                f'- {Content.objects.count()} content items\n'
                f'- {Quiz.objects.count()} quiz\n'
                f'- {User.objects.count()} users'
            )
        ) 