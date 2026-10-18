from django.db import migrations


QUESTIONS = [
    ('APTITUDE', 'Percentage of a value', 'What is 15% of 240?', ['24', '30', '36', '40'], '36', '0.15 × 240 = 36.', 'EASY'),
    ('APTITUDE', 'Fraction of a quantity', 'What is 3/5 of 250?', ['125', '140', '150', '175'], '150', '250 ÷ 5 × 3 = 150.', 'EASY'),
    ('APTITUDE', 'Mean of five numbers', 'The mean of five numbers is 18. What is their total?', ['72', '80', '90', '108'], '90', 'Total = mean × count = 18 × 5 = 90.', 'EASY'),
    ('APTITUDE', 'Average speed', 'A car travels 180 km in 3 hours at a constant speed. What is its speed?', ['50 km/h', '55 km/h', '60 km/h', '65 km/h'], '60 km/h', 'Speed = distance ÷ time = 180 ÷ 3 = 60 km/h.', 'EASY'),
    ('APTITUDE', 'Simple interest', 'What simple interest accrues on ₹2,000 at 5% per year for 2 years?', ['₹100', '₹150', '₹200', '₹250'], '₹200', 'Simple interest = principal × rate × time = 2,000 × 0.05 × 2 = ₹200.', 'EASY'),
    ('APTITUDE', 'Divide in a ratio', 'A total of 75 is divided in the ratio 2:3. What is the smaller share?', ['25', '30', '35', '45'], '30', 'There are 5 equal parts; the smaller share is 2 × (75 ÷ 5) = 30.', 'EASY'),
    ('APTITUDE', 'Train speed', 'A 120 m train passes a pole in 6 seconds. What is its speed in km/h?', ['60', '68', '72', '80'], '72', '120 ÷ 6 = 20 m/s; 20 × 3.6 = 72 km/h.', 'MEDIUM'),
    ('APTITUDE', 'Combined work rate', 'A can finish a job in 12 days and B in 6 days. How long do they take working together?', ['3 days', '4 days', '6 days', '9 days'], '4 days', 'Their daily rates add to 1/12 + 1/6 = 1/4 of the job per day.', 'MEDIUM'),
    ('APTITUDE', 'Number series', 'Find the next number: 5, 11, 23, 47, __.', ['83', '91', '95', '99'], '95', 'Each term is twice the previous term plus one: 47 × 2 + 1 = 95.', 'MEDIUM'),
    ('APTITUDE', 'Probability on a die', 'A fair six-sided die is rolled once. What is the probability of rolling a number greater than 4?', ['1/6', '1/3', '1/2', '2/3'], '1/3', 'The favourable outcomes are 5 and 6, so the probability is 2/6 = 1/3.', 'EASY'),
    ('APTITUDE', 'Permutations', 'In how many different ways can 5 distinct people stand in a line?', ['25', '60', '100', '120'], '120', 'The number of arrangements is 5! = 5 × 4 × 3 × 2 × 1 = 120.', 'MEDIUM'),
    ('APTITUDE', 'Discounted price', 'An item marked ₹1,500 is sold at a 20% discount. What is its selling price?', ['₹1,050', '₹1,100', '₹1,200', '₹1,250'], '₹1,200', 'The discount is ₹300, leaving a selling price of ₹1,200.', 'EASY'),
    ('APTITUDE', 'Profit calculation', 'An item costs ₹800. What is its selling price at a 25% profit?', ['₹900', '₹950', '₹1,000', '₹1,100'], '₹1,000', 'Selling price = 800 × 1.25 = ₹1,000.', 'EASY'),
    ('APTITUDE', 'Least common multiple', 'What is the least common multiple of 12 and 18?', ['24', '30', '36', '72'], '36', '36 is the smallest positive number divisible by both 12 and 18.', 'EASY'),
    ('APTITUDE', 'Highest common factor', 'What is the highest common factor of 48 and 60?', ['6', '8', '12', '24'], '12', 'The common factors include 1, 2, 3, 4, 6, and 12; the greatest is 12.', 'EASY'),
    ('APTITUDE', 'Solve a linear equation', 'Solve for x: 2x + 7 = 31.', ['10', '11', '12', '14'], '12', 'Subtract 7 to get 2x = 24, then divide by 2.', 'EASY'),
    ('APTITUDE', 'Percentage increase', 'A value of 200 is increased by 30%. What is the new value?', ['230', '250', '260', '280'], '260', '30% of 200 is 60, so the new value is 260.', 'EASY'),
    ('APTITUDE', 'Pythagorean theorem', 'A right triangle has shorter sides of 3 cm and 4 cm. What is the hypotenuse?', ['5 cm', '6 cm', '7 cm', '8 cm'], '5 cm', 'By the Pythagorean theorem, the hypotenuse is √(3² + 4²) = 5 cm.', 'EASY'),
    ('APTITUDE', 'Angle at three o’clock', 'What is the smaller angle between the hands of a clock at exactly 3:00?', ['60°', '90°', '120°', '180°'], '90°', 'At 3:00, the minute hand is at 12 and the hour hand is at 3: a right angle.', 'EASY'),
    ('APTITUDE', 'Mean of four values', 'What is the mean of 12, 15, 18, and 21?', ['15', '16', '16.5', '17'], '16.5', 'The sum is 66; 66 ÷ 4 = 16.5.', 'EASY'),
    ('APTITUDE', 'Workforce scaling', 'Eight workers finish a job in 15 days. At the same rate, how many days would 12 workers take?', ['8 days', '10 days', '12 days', '18 days'], '10 days', 'The work is 8 × 15 = 120 worker-days; 120 ÷ 12 = 10 days.', 'MEDIUM'),
    ('APTITUDE', 'Square number series', 'Find the next number: 1, 4, 9, 16, 25, __.', ['30', '32', '36', '49'], '36', 'These are consecutive squares: 1², 2², 3², 4², 5²; next is 6² = 36.', 'EASY'),
    ('APTITUDE', 'Simple interest rate', 'What simple interest is earned on ₹5,000 at 8% per year for 3 years?', ['₹800', '₹1,000', '₹1,200', '₹1,500'], '₹1,200', '5,000 × 0.08 × 3 = ₹1,200.', 'MEDIUM'),
    ('APTITUDE', 'Ratio in a mixture', 'A 35-litre mixture has concentrate and water in the ratio 1:4. How many litres are concentrate?', ['5', '7', '14', '28'], '7', 'There are 5 total parts; one part is 35 ÷ 5 = 7 litres.', 'MEDIUM'),
    ('APTITUDE', 'Rectangle perimeter', 'What is the perimeter of a rectangle with length 12 cm and width 7 cm?', ['19 cm', '28 cm', '38 cm', '84 cm'], '38 cm', 'Perimeter = 2 × (12 + 7) = 38 cm.', 'EASY'),
    ('APTITUDE', 'Fraction as a percentage', 'What is 25% of 3/5?', ['0.12', '0.15', '0.20', '0.25'], '0.15', '25% × 3/5 = 1/4 × 3/5 = 3/20 = 0.15.', 'MEDIUM'),
    ('APTITUDE', 'Three-digit arrangements', 'How many three-digit arrangements can be made using 1, 2, 3, and 4 without repeating a digit?', ['12', '18', '24', '64'], '24', 'There are 4 choices for the first digit, then 3 and 2: 4 × 3 × 2 = 24.', 'MEDIUM'),
    ('APTITUDE', 'Sum of even numbers', 'What is the sum of the even numbers from 2 through 20?', ['100', '110', '120', '200'], '110', 'There are 10 terms with mean (2 + 20) ÷ 2 = 11, so the sum is 10 × 11 = 110.', 'MEDIUM'),
    ('APTITUDE', 'Two coin tosses', 'Two fair coins are tossed. What is the probability that both show heads?', ['1/2', '1/3', '1/4', '3/4'], '1/4', 'The equally likely outcomes are HH, HT, TH, TT; one of four is HH.', 'EASY'),
    ('APTITUDE', 'Pass percentage', 'If 60% of a group passed and 240 people passed, how many people were in the group?', ['360', '380', '400', '420'], '400', 'Total = 240 ÷ 0.60 = 400.', 'EASY'),
    ('DSA', 'Binary search complexity', 'What is the worst-case time complexity of binary search on a sorted array of n elements?', ['O(1)', 'O(log n)', 'O(n)', 'O(n log n)'], 'O(log n)', 'Binary search halves the remaining search interval at each step.', 'EASY'),
    ('DSA', 'Stack behaviour', 'Which order does a standard stack follow?', ['FIFO', 'LIFO', 'Random order', 'Sorted order'], 'LIFO', 'A stack is last-in, first-out: the most recently pushed item is popped first.', 'EASY'),
    ('DSA', 'Queue behaviour', 'Which order does a standard queue follow?', ['FIFO', 'LIFO', 'Largest first', 'Smallest first'], 'FIFO', 'A queue is first-in, first-out: items leave in the order they arrived.', 'EASY'),
    ('DSA', 'Linked-list insertion', 'Given a pointer to a node, what is the time complexity of inserting a new node immediately after it in a singly linked list?', ['O(1)', 'O(log n)', 'O(n)', 'O(n log n)'], 'O(1)', 'Only a fixed number of pointer updates are needed when the insertion node is already known.', 'MEDIUM'),
    ('DSA', 'Hash-table lookup', 'What is the average-case lookup time in a well-sized hash table?', ['O(1)', 'O(log n)', 'O(n)', 'O(n²)'], 'O(1)', 'A hash function maps the key directly to a bucket on average; collisions can worsen the worst case.', 'EASY'),
    ('DSA', 'Depth-first search structure', 'Which structure is naturally used to implement iterative depth-first search?', ['Queue', 'Stack', 'Min-heap', 'Hash table only'], 'Stack', 'Depth-first search explores the most recently discovered node first, which a stack supports.', 'EASY'),
    ('DSA', 'Merge-sort complexity', 'What is the worst-case time complexity of merge sort?', ['O(log n)', 'O(n)', 'O(n log n)', 'O(n²)'], 'O(n log n)', 'Merge sort performs O(log n) levels of splitting and O(n) merging work per level.', 'MEDIUM'),
    ('DSA', 'Balanced search-tree lookup', 'What is the search time in a height-balanced binary search tree with n nodes?', ['O(1)', 'O(log n)', 'O(n)', 'O(n²)'], 'O(log n)', 'A balanced tree has height proportional to log n, and search follows one root-to-leaf path.', 'MEDIUM'),
    ('HR', 'Constructive disagreement', 'A teammate disagrees with your proposal in a meeting. What is the most constructive response?', ['Dismiss their concern', 'Ask them to explain their reasoning and compare evidence', 'End the discussion immediately', 'Escalate before hearing them out'], 'Ask them to explain their reasoning and compare evidence', 'Listening to the concern and evaluating evidence supports respectful, effective decisions.', 'EASY'),
    ('HR', 'Deadline communication', 'You realize your task may miss its deadline. What should you do first?', ['Wait until the deadline passes', 'Tell stakeholders early and propose a recovery plan', 'Hide the delay', 'Stop work without telling anyone'], 'Tell stakeholders early and propose a recovery plan', 'Early, transparent communication gives the team time to adjust scope and support recovery.', 'EASY'),
    ('HR', 'Receiving feedback', 'What is the best response to specific constructive feedback?', ['Defend every decision', 'Listen, clarify expectations, and identify an improvement step', 'Ignore it', 'Blame another teammate'], 'Listen, clarify expectations, and identify an improvement step', 'Understanding the feedback and acting on it turns it into a practical development plan.', 'EASY'),
    ('HR', 'Team contribution', 'A team task is blocked and a colleague is overloaded. What is a helpful action?', ['Wait for someone else to notice', 'Offer specific support and coordinate priorities with the team', 'Take over without asking', 'Criticize the colleague publicly'], 'Offer specific support and coordinate priorities with the team', 'Specific offers of help plus coordination respect ownership while moving shared work forward.', 'EASY'),
]


def add_questions(apps, schema_editor):
    Question = apps.get_model('aptitude', 'AptitudeQuestion')
    existing_titles = set(Question.objects.values_list('title', flat=True))
    Question.objects.bulk_create([
        Question(
            category=category,
            title=title,
            prompt=prompt,
            options=options,
            correct_answer=answer,
            explanation=explanation,
            difficulty=difficulty,
            is_active=True,
        )
        for category, title, prompt, options, answer, explanation, difficulty in QUESTIONS
        if title not in existing_titles
    ])


class Migration(migrations.Migration):

    dependencies = [
        ('aptitude', '0003_aptitudetestattempt'),
    ]

    operations = [
        # Seeded questions remain usable bank content if the migration is rolled back.
        migrations.RunPython(add_questions, migrations.RunPython.noop),
    ]
