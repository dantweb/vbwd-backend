#!/bin/bash
# Create test user for e2e tests
# Usage: ./bin/create_user.sh [email] [password]

EMAIL="${1:-user@example.com}"
PASSWORD="${2:-Password123!}"

echo "Creating user: $EMAIL"

docker compose exec -T api python /app/bin/create_user.py --email "$EMAIL" --password "$PASSWORD"
exit 0

# Legacy inline script kept below for reference only:
: << EOF
import sys
sys.path.insert(0, '/app')

from src.extensions import Session
from src.models.user import User
from src.models.enums import UserStatus, UserRole
import bcrypt

session = Session()
try:
    # Check if user exists
    user = session.query(User).filter_by(email='${EMAIL}').first()
    if user:
        print(f'User already exists: {user.email} (id={user.id}, status={user.status.value})')
        # Ensure user is active
        if user.status != UserStatus.ACTIVE:
            user.status = UserStatus.ACTIVE
            session.commit()
            print(f'User status updated to ACTIVE')
    else:
        print('User not found, creating...')
        password_hash = bcrypt.hashpw('${PASSWORD}'.encode(), bcrypt.gensalt()).decode()
        user = User()
        user.email = '${EMAIL}'
        user.password_hash = password_hash
        user.status = UserStatus.ACTIVE
        user.role = UserRole.USER
        session.add(user)
        session.commit()
        print(f'Created user: {user.email} (id={user.id})')
finally:
    session.close()
EOF
