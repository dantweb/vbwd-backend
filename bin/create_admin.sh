#!/bin/bash
# Create admin user for admin panel access
# Usage: ./bin/create_admin.sh [email] [password]

EMAIL="${1:-admin@vbwd.local}"
PASSWORD="${2:-admin123}"

echo "Creating admin user: $EMAIL with password: $PASSWORD"

docker-compose exec -T api python << EOF
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
        print(f'User already exists: {user.email} (id={user.id}, role={user.role.value}, status={user.status.value})')
        # Ensure user is active and has admin role
        updated = False
        if user.status != UserStatus.ACTIVE:
            user.status = UserStatus.ACTIVE
            updated = True
            print(f'User status updated to ACTIVE')
        if user.role != UserRole.ADMIN:
            user.role = UserRole.ADMIN
            updated = True
            print(f'User role updated to ADMIN')
        if updated:
            session.commit()
    else:
        print('Admin user not found, creating...')
        password_hash = bcrypt.hashpw('${PASSWORD}'.encode(), bcrypt.gensalt()).decode()
        user = User()
        user.email = '${EMAIL}'
        user.password_hash = password_hash
        user.status = UserStatus.ACTIVE
        user.role = UserRole.ADMIN
        session.add(user)
        session.commit()
        print(f'Created admin user: {user.email} (id={user.id}, role={user.role.value})')
finally:
    session.close()
EOF
