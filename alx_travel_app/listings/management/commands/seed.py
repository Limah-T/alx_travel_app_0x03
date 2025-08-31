'''CREATE TABLE IF NOT EXISTS 'user'(
    'user_id' UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    'first_name' VARCHAR(255) NOT NULL,
    'last_name' VARCHAR(255) NOT NULL,
    'email' VARCHAR(255) NOT NULL UNIQUE,
    'phone_number' VARCHAR(255) NOT NULL,
    'role' VARCHAR(10) NOT NULL CHECK (role IN ('guest', 'host', 'admin')),
    'created_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    'updated_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)'''

'''CREATE TABLE IF NOT EXISTS 'property'(
    'property_id' UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    'user_id' UUID NOT NULL REFERENCES "user"("user_id") ON DELETE CASCADE,
    'name' VARCHAR(255) NOT NULL,
    'description' TEXT NOT NULL,
    'location' VARCHAR(255) NOT NULL,
    'pricepernight' DECIMAL(10, 2) NOT NULL,
    'created_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    'updated_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
'''

'''CREATE TABLE IF NOT EXISTS 'booking'(
    'booking_id' UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    'property_id' UUID NOT NULL REFERENCES "property"("property_id") ON DELETE CASCADE,
    'user_id' UUID NOT NULL REFERENCES "user"("user_id") ON DELETE CASCADE,
    'start_date' DATE NOT NULL,
    'end_date' DATE NOT NULL,
    'created_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    'updated_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)'''

'''CREATE TABLE IF NOT EXISTS 'booking'(
    'booking_id' UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    'property_id' UUID NOT NULL REFERENCES "property"("property_id") ON DELETE CASCADE,
    'user_id' UUID NOT NULL REFERENCES "user"("user_id") ON DELETE CASCADE,
    'start_date' DATE NOT NULL,
    'end_date' DATE NOT NULL,
    'created_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    'updated_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)'''

'''CREATE TABLE IF NOT EXISTS 'review'(
    'review_id' UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    'property_id' UUID NOT NULL REFERENCES "property"("property_id") ON DELETE CASCADE,
    'user_id' UUID NOT NULL REFERENCES "user"("user_id") ON DELETE CASCADE,
    'rating' INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    'comment' TEXT
)'''

from django.core.management.base import BaseCommand
from listings.models import User, Property, Booking, Review

class Command(BaseCommand):
    help = 'Seed the database with initial data'

    def handle(self, *args, **options):
        # Create users
        user1 = User.objects.create(
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            phone_number='1234567890',
            role='guest'
        )
        user2 = User.objects.create(
            first_name='Jane',
            last_name='Smith',
            email='jane.smith@example.com',
            phone_number='0987654321',
            role='host'
        )

        # Create properties
        property1 = Property.objects.create(
            user=user2,
            name='Cozy Cottage',
            description='A cozy cottage in the woods.',
            location='Forest',
            pricepernight=100.00
        )
        property2 = Property.objects.create(
            user=user2,
            name='Beach House',
            description='A beautiful beach house.',
            location='Beach',
            pricepernight=200.00
        )

        # Create bookings
        Booking.objects.create(
            property=property1,
            user=user1,
            start_date='2023-10-01',
            end_date='2023-10-05'
        )
        Booking.objects.create(
            property=property2,
            user=user1,
            start_date='2023-10-10',
            end_date='2023-10-15'
        )

        Review.objects.create(
            property=property1,
            user=user1,
            rating=5,
            comment='Amazing stay!'
        )

        Review.objects.create(
            property=property2,
            user=user1,
            rating=4,
            comment='Great location, but a bit noisy.'
        )

        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))