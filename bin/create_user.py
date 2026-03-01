#!/usr/bin/env python
"""Create a regular user.
Usage: python /app/bin/create_user.py --email user@example.com --password Secret123!
"""
import sys
import argparse
sys.path.insert(0, '/app')

from src.extensions import Session
from src.models.user import User
from src.models.enums import UserStatus, UserRole
import bcrypt

parser = argparse.ArgumentParser()
parser.add_argument('--email',    default='user@vbwd.local')
parser.add_argument('--password', default='ChangeMe123!')
args = parser.parse_args()

session = Session()
try:
    user = session.query(User).filter_by(email=args.email).first()
    if user:
        if user.status != UserStatus.ACTIVE:
            user.status = UserStatus.ACTIVE
            session.commit()
            print(f'Activated: {user.email}')
        else:
            print(f'Already exists: {user.email}')
    else:
        h = bcrypt.hashpw(args.password.encode(), bcrypt.gensalt()).decode()
        user = User(email=args.email, password_hash=h,
                    status=UserStatus.ACTIVE, role=UserRole.USER)
        session.add(user)
        session.commit()
        print(f'Created user: {user.email} (id={user.id})')
except Exception as e:
    session.rollback()
    print(f'Error: {e}')
    sys.exit(1)
finally:
    session.close()
