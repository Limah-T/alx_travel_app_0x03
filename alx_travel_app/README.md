# DataBase Seeding

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
