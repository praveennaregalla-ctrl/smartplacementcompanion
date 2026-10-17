from django.core.management.base import BaseCommand
from interview.models import InterviewQuestion

class Command(BaseCommand):
    help = 'Seed the database with predefined interview questions'

    def handle(self, *args, **options):
        questions = [
            # Software Engineer - Technical
            ('SOFTWARE_ENGINEER', 'TECHNICAL', 'What is the difference between a Process and a Thread?', 'resource sharing, memory space, context switching, overhead'),
            ('SOFTWARE_ENGINEER', 'TECHNICAL', 'Explain the concept of Virtual Memory.', 'address space, paging, segmentation, swapping, hard disk'),
            ('SOFTWARE_ENGINEER', 'TECHNICAL', 'What is a Deadlock and how can it be prevented?', 'mutual exclusion, hold and wait, no preemption, circular wait, bank algorithm'),
            ('SOFTWARE_ENGINEER', 'TECHNICAL', 'What are the ACID properties in a database?', 'atomicity, consistency, isolation, durability'),
            ('SOFTWARE_ENGINEER', 'TECHNICAL', 'Explain the difference between TCP and UDP.', 'connection oriented, reliable, connectionless, fast, overhead'),
            ('SOFTWARE_ENGINEER', 'TECHNICAL', 'What is inheritance in OOP?', 'reuse, parent class, child class, extends'),
            ('SOFTWARE_ENGINEER', 'TECHNICAL', 'Explain the Time Complexity of Quick Sort.', 'divide and conquer, pivot, n log n, average case, worst case'),
            ('SOFTWARE_ENGINEER', 'TECHNICAL', 'What is a Linked List and how does it differ from an Array?', 'dynamic size, pointers, contiguous memory, insertion, deletion'),
            
            # Data Analyst - Technical
            ('DATA_ANALYST', 'TECHNICAL', 'What is the difference between supervised and unsupervised learning?', 'labeled data, target variable, grouping, patterns'),
            ('DATA_ANALYST', 'TECHNICAL', 'What is a p-value in statistics?', 'significance, null hypothesis, probability, evidence'),
            ('DATA_ANALYST', 'TECHNICAL', 'Explain the difference between SELECT and WHERE in SQL.', 'columns, filtering, rows, query'),
            ('DATA_ANALYST', 'TECHNICAL', 'What is Data Normalization?', 'redundancy, integrity, 1nf, 2nf, 3nf'),
            ('DATA_ANALYST', 'TECHNICAL', 'What is an outlier and how do you handle it?', 'extreme value, deviation, imputation, removal'),
            
            # Web Developer - Technical
            ('WEB_DEVELOPER', 'TECHNICAL', 'What is the DOM in web development?', 'document object model, tree structure, browser, javascript, manipulation'),
            ('WEB_DEVELOPER', 'TECHNICAL', 'Explain the difference between local storage and session storage.', 'persistence, browser tab, expiry, web storage'),
            ('WEB_DEVELOPER', 'TECHNICAL', 'What is CSS Flexbox?', 'layout, alignment, flexible, container, axis'),
            ('WEB_DEVELOPER', 'TECHNICAL', 'What is a REST API?', 'stateless, resources, methods, get, post, put, delete'),
            ('WEB_DEVELOPER', 'TECHNICAL', 'Explain the concept of Hoisting in JavaScript.', 'declaration, top, undefined, execution context'),
            
            # HR Questions (Common for all)
            ('SOFTWARE_ENGINEER', 'HR', 'Tell me about yourself.', 'background, education, skills, interests'),
            ('SOFTWARE_ENGINEER', 'HR', 'What are your strengths and weaknesses?', 'problem solving, team player, communication, adaptability'),
            ('SOFTWARE_ENGINEER', 'HR', 'Why do you want to work for this company?', 'vision, growth, culture, match'),
            ('SOFTWARE_ENGINEER', 'HR', 'Where do you see yourself in 5 years?', 'professional growth, leadership, learning, impact'),
            ('DATA_ANALYST', 'HR', 'Describe a challenging project you worked on.', 'problem, approach, result, learning'),
            ('WEB_DEVELOPER', 'HR', 'How do you handle conflict in a team?', 'communication, empathy, resolution, professional'),
        ]

        # Duplicate HR questions for other roles
        roles = ['DATA_ANALYST', 'WEB_DEVELOPER']
        hr_questions_base = [q for q in questions if q[1] == 'HR']
        for role in roles:
            for q in hr_questions_base:
                if q[0] == 'SOFTWARE_ENGINEER':
                    questions.append((role, 'HR', q[2], q[3]))

        created_count = 0
        for role, cat, text, keys in questions:
            obj, created = InterviewQuestion.objects.get_or_create(
                role=role,
                category=cat,
                question_text=text,
                defaults={'expected_keywords': keys}
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {created_count} questions.'))
