"""
Security Module - Password Hashing, Rate Limiting, Session Management
"""

import time
import bcrypt
from collections import defaultdict
from threading import Lock
from datetime import datetime, timedelta


# ============================================================
# PASSWORD HASHING (bcrypt)
# ============================================================

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    Returns the hashed password as a string (safe to store in DB).
    """
    if not password:
        return None
    salt = bcrypt.gensalt(rounds=12)  # 12 rounds is secure and reasonably fast
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against a bcrypt hash.
    Also supports legacy plaintext comparison for migration period.
    """
    if not password or not hashed:
        return False
    
    try:
        # Try bcrypt verification first
        if hashed.startswith('$2b$') or hashed.startswith('$2a$'):
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        else:
            # Legacy: plaintext comparison (for existing users before migration)
            # This allows old users to login and their password will be updated
            return password == hashed
    except Exception as e:
        print(f"Password verification error: {e}")
        return False


def is_password_hashed(password: str) -> bool:
    """Check if a password is already hashed (bcrypt format)"""
    if not password:
        return False
    return password.startswith('$2b$') or password.startswith('$2a$')


# ============================================================
# RATE LIMITING (Brute Force Protection)
# ============================================================

class RateLimiter:
    """
    Rate limiter to prevent brute force attacks.
    Locks account after max_attempts failed attempts for lockout_duration seconds.
    """
    
    def __init__(self, max_attempts: int = 5, lockout_duration: int = 300):
        self.max_attempts = max_attempts  # Default: 5 attempts
        self.lockout_duration = lockout_duration  # Default: 5 minutes (300 seconds)
        self.failed_attempts = defaultdict(list)  # username -> list of timestamps
        self.lock = Lock()
    
    def record_failed_attempt(self, username: str) -> tuple:
        """
        Record a failed login attempt.
        Returns: (is_locked, remaining_attempts, lockout_seconds_remaining)
        """
        with self.lock:
            now = time.time()
            username_lower = username.lower()
            
            # Clean old attempts (older than lockout_duration)
            self.failed_attempts[username_lower] = [
                t for t in self.failed_attempts[username_lower]
                if now - t < self.lockout_duration
            ]
            
            # Add new failed attempt
            self.failed_attempts[username_lower].append(now)
            
            attempts = len(self.failed_attempts[username_lower])
            remaining = self.max_attempts - attempts
            
            if attempts >= self.max_attempts:
                # Calculate lockout time remaining
                oldest_attempt = min(self.failed_attempts[username_lower])
                lockout_remaining = int(self.lockout_duration - (now - oldest_attempt))
                return True, 0, max(lockout_remaining, 0)
            
            return False, remaining, 0
    
    def is_locked(self, username: str) -> tuple:
        """
        Check if an account is locked.
        Returns: (is_locked, lockout_seconds_remaining)
        """
        with self.lock:
            now = time.time()
            username_lower = username.lower()
            
            # Clean old attempts
            self.failed_attempts[username_lower] = [
                t for t in self.failed_attempts[username_lower]
                if now - t < self.lockout_duration
            ]
            
            attempts = len(self.failed_attempts[username_lower])
            
            if attempts >= self.max_attempts:
                oldest_attempt = min(self.failed_attempts[username_lower])
                lockout_remaining = int(self.lockout_duration - (now - oldest_attempt))
                return True, max(lockout_remaining, 0)
            
            return False, 0
    
    def reset(self, username: str):
        """Reset failed attempts for a user (call after successful login)"""
        with self.lock:
            username_lower = username.lower()
            self.failed_attempts[username_lower] = []


# Global rate limiter instance
login_rate_limiter = RateLimiter(max_attempts=5, lockout_duration=300)


# ============================================================
# SESSION MANAGEMENT
# ============================================================

class SessionManager:
    """
    Manages user session timeout.
    Auto-logout after inactivity_timeout seconds of inactivity.
    """
    
    def __init__(self, inactivity_timeout: int = 1800):
        self.inactivity_timeout = inactivity_timeout  # Default: 30 minutes
        self.last_activity = time.time()
        self.is_active = True
    
    def update_activity(self):
        """Call this on any user activity to reset the timeout"""
        self.last_activity = time.time()
    
    def check_timeout(self) -> bool:
        """
        Check if session has timed out.
        Returns True if timed out, False if still active.
        """
        if not self.is_active:
            return True
        
        elapsed = time.time() - self.last_activity
        if elapsed >= self.inactivity_timeout:
            self.is_active = False
            return True
        return False
    
    def get_remaining_time(self) -> int:
        """Get seconds remaining before timeout"""
        elapsed = time.time() - self.last_activity
        remaining = self.inactivity_timeout - elapsed
        return max(0, int(remaining))
    
    def logout(self):
        """Mark session as logged out"""
        self.is_active = False


# ============================================================
# PASSWORD STRENGTH VALIDATION
# ============================================================

def validate_password_strength(password: str) -> tuple:
    """
    Validate password meets minimum security requirements.
    Returns: (is_valid, error_message)
    """
    if not password:
        return False, "Password is required"
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    if not has_upper:
        return False, "Password must contain at least one uppercase letter"
    
    if not has_lower:
        return False, "Password must contain at least one lowercase letter"
    
    if not has_digit:
        return False, "Password must contain at least one number"
    
    return True, "Password is strong"


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def format_lockout_time(seconds: int) -> str:
    """Format lockout time for user display"""
    if seconds < 60:
        return f"{seconds} seconds"
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    if remaining_seconds > 0:
        return f"{minutes} min {remaining_seconds} sec"
    return f"{minutes} minutes"
