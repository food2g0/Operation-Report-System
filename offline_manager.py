"""
Offline Manager Module
Handles offline mode functionality including:
- Credential caching for offline login
- Pending entries queue for later posting
- Connectivity detection and sync
"""

import os
import sys
import json
import hashlib
import datetime
from typing import Optional, Dict, List, Tuple


def _get_data_dir() -> str:
    """Get the offline data directory path"""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        if hasattr(sys, '_MEIPASS'):
            base = os.path.dirname(sys.executable)
        else:
            base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    
    offline_dir = os.path.join(base, "offline_data")
    os.makedirs(offline_dir, exist_ok=True)
    return offline_dir


def _get_credentials_path() -> str:
    """Get path to cached credentials file"""
    return os.path.join(_get_data_dir(), "cached_credentials.json")


def _get_pending_path() -> str:
    """Get path to pending entries directory"""
    pending_dir = os.path.join(_get_data_dir(), "pending_entries")
    os.makedirs(pending_dir, exist_ok=True)
    return pending_dir


def _hash_password(password: str, salt: str) -> str:
    """Hash password with salt for local storage"""
    combined = f"{salt}{password}{salt}".encode('utf-8')
    return hashlib.sha256(combined).hexdigest()


class OfflineManager:
    """Manages offline mode functionality"""
    
    # Salt for local password hashing (different from server-side bcrypt)
    LOCAL_SALT = "ORS_OFFLINE_2024"
    
    def __init__(self):
        self._is_offline = False
        self._cached_user_data = None
        
    @property
    def is_offline(self) -> bool:
        """Check if currently in offline mode"""
        return self._is_offline
    
    @is_offline.setter
    def is_offline(self, value: bool):
        self._is_offline = value
        
    def cache_credentials(self, username: str, password: str, user_data: Dict) -> bool:
        # Ensure all user_data values are serializable primitives (str, int, float, None)
        def _safe_primitive(val):
            if isinstance(val, (str, int, float)) or val is None:
                return val
            return str(val)
        safe_user_data = {k: _safe_primitive(v) for k, v in user_data.items()}
        """
        Cache user credentials for offline login after successful online login.
        
        Args:
            username: The user's username
            password: Plain password to hash for offline verification
            user_data: User data dict including branch, corporation, role
        
        Returns:
            True if successful, False otherwise
        """
        try:
            credentials_path = _get_credentials_path()
            
            # Load existing cached credentials
            cached = {}
            if os.path.exists(credentials_path):
                with open(credentials_path, 'r', encoding='utf-8') as f:
                    cached = json.load(f)
            
            # Hash password for local storage
            password_hash = _hash_password(password, self.LOCAL_SALT)
            
            # Store user's cached data
            cached[username.lower()] = {
                "password_hash": password_hash,
                "username": username,
                "branch": safe_user_data.get("branch", "Unknown"),
                "corporation": safe_user_data.get("corporation", "Unknown"),
                "role": safe_user_data.get("role", "user"),
                "last_cached": datetime.datetime.now().isoformat(),
                "account_type": safe_user_data.get("account_type")
            }
            
            with open(credentials_path, 'w', encoding='utf-8') as f:
                json.dump(cached, f, indent=2)
            
            print(f"✅ Credentials cached for offline use: {username}")
            return True
            
        except Exception as e:
            print(f"Failed to cache credentials: {e}")
            return False
    
    def verify_offline_credentials(self, username: str, password: str) -> Tuple[bool, Optional[Dict]]:
        """
        Verify credentials against cached data for offline login.
        
        Args:
            username: The user's username
            password: Plain password to verify
            
        Returns:
            Tuple of (success, user_data) where user_data is None if failed
        """
        try:
            credentials_path = _get_credentials_path()
            
            if not os.path.exists(credentials_path):
                return False, None
            
            with open(credentials_path, 'r', encoding='utf-8') as f:
                cached = json.load(f)
            
            user_key = username.lower()
            if user_key not in cached:
                return False, None
            
            user_data = cached[user_key]
            password_hash = _hash_password(password, self.LOCAL_SALT)
            
            if password_hash == user_data.get("password_hash"):
                self._cached_user_data = user_data
                return True, user_data
            
            return False, None
            
        except Exception as e:
            print(f"Offline credential verification failed: {e}")
            return False, None
    
    def has_cached_credentials(self, username: str = None) -> bool:
        """Check if there are any cached credentials (or for specific user)"""
        try:
            credentials_path = _get_credentials_path()
            
            if not os.path.exists(credentials_path):
                return False
            
            with open(credentials_path, 'r', encoding='utf-8') as f:
                cached = json.load(f)
            
            if username:
                return username.lower() in cached
            
            return len(cached) > 0
            
        except Exception:
            return False
    
    def save_pending_entry(self, username: str, branch: str, corporation: str, 
                           entry_data: Dict) -> str:
        """
        Save an entry to the pending queue for later posting.
        
        Args:
            username: User who created the entry
            branch: User's branch
            corporation: User's corporation
            entry_data: The full entry data to post later
            
        Returns:
            The pending entry ID
        """
        try:
            pending_dir = _get_pending_path()
            
            # Generate unique ID
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            entry_id = f"{username}_{timestamp}"
            
            pending_entry = {
                "id": entry_id,
                "created_at": datetime.datetime.now().isoformat(),
                "username": username,
                "branch": branch,
                "corporation": corporation,
                "status": "pending",
                "retries": 0,
                "last_error": None,
                "entry_data": entry_data
            }
            
            entry_path = os.path.join(pending_dir, f"{entry_id}.json")
            with open(entry_path, 'w', encoding='utf-8') as f:
                json.dump(pending_entry, f, indent=2, ensure_ascii=False)
            
            print(f"📝 Entry saved to pending queue: {entry_id}")
            return entry_id
            
        except Exception as e:
            print(f"Failed to save pending entry: {e}")
            raise
    
    def get_pending_entries(self, username: str = None) -> List[Dict]:
        """
        Get all pending entries, optionally filtered by username.
        
        Args:
            username: Optional filter by username
            
        Returns:
            List of pending entry dictionaries
        """
        pending = []
        try:
            pending_dir = _get_pending_path()
            
            for filename in os.listdir(pending_dir):
                if not filename.endswith('.json'):
                    continue
                    
                filepath = os.path.join(pending_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    entry = json.load(f)
                
                if username and entry.get("username") != username:
                    continue
                
                if entry.get("status") == "pending":
                    pending.append(entry)
            
            # Sort by creation time
            pending.sort(key=lambda x: x.get("created_at", ""))
            
        except Exception as e:
            print(f"Failed to get pending entries: {e}")
        
        return pending
    
    def get_pending_count(self, username: str = None) -> int:
        """Get count of pending entries"""
        return len(self.get_pending_entries(username))
    
    def mark_entry_synced(self, entry_id: str) -> bool:
        """Mark a pending entry as successfully synced"""
        try:
            pending_dir = _get_pending_path()
            entry_path = os.path.join(pending_dir, f"{entry_id}.json")
            
            if os.path.exists(entry_path):
                # Remove the file after successful sync
                os.remove(entry_path)
                print(f"✅ Entry synced and removed: {entry_id}")
                return True
            
            return False
            
        except Exception as e:
            print(f"Failed to mark entry synced: {e}")
            return False
    
    def mark_entry_failed(self, entry_id: str, error: str) -> bool:
        """Mark a pending entry as failed (for retry later)"""
        try:
            pending_dir = _get_pending_path()
            entry_path = os.path.join(pending_dir, f"{entry_id}.json")
            
            if not os.path.exists(entry_path):
                return False
            
            with open(entry_path, 'r', encoding='utf-8') as f:
                entry = json.load(f)
            
            entry["retries"] = entry.get("retries", 0) + 1
            entry["last_error"] = error
            entry["last_attempt"] = datetime.datetime.now().isoformat()
            
            with open(entry_path, 'w', encoding='utf-8') as f:
                json.dump(entry, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Failed to mark entry failed: {e}")
            return False
    
    def delete_pending_entry(self, entry_id: str) -> bool:
        """Delete a pending entry (user manually cancelled)"""
        try:
            pending_dir = _get_pending_path()
            entry_path = os.path.join(pending_dir, f"{entry_id}.json")
            
            if os.path.exists(entry_path):
                os.remove(entry_path)
                return True
            
            return False
            
        except Exception as e:
            print(f"Failed to delete pending entry: {e}")
            return False
    
    # ───────────────────────────────────────────────────────
    #  BALANCE CACHING FOR OFFLINE MODE
    # ───────────────────────────────────────────────────────
    
    def _get_balance_cache_path(self) -> str:
        """Get path to cached balances file"""
        return os.path.join(_get_data_dir(), "cached_balances.json")
    
    def cache_ending_balance(self, username: str, branch: str, corporation: str,
                             brand: str, date: str, ending_balance: float) -> bool:
        """
        Cache the ending balance after a successful post (online or offline).
        Used to auto-fill beginning balance when offline.
        """
        try:
            cache_path = self._get_balance_cache_path()
            
            # Load existing cache
            cached = {}
            if os.path.exists(cache_path):
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cached = json.load(f)
            
            # Create unique key for this user/branch/corporation/brand combination
            key = f"{username}_{branch}_{corporation}_{brand}".lower()
            key = "".join(c if c.isalnum() or c == "_" else "_" for c in key)
            
            cached[key] = {
                "username": username,
                "branch": branch,
                "corporation": corporation,
                "brand": brand,
                "date": date,
                "ending_balance": ending_balance,
                "cached_at": datetime.datetime.now().isoformat()
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cached, f, indent=2)
            
            print(f"💾 Cached ending balance for {brand}: {ending_balance} ({date})")
            return True
            
        except Exception as e:
            print(f"Failed to cache ending balance: {e}")
            return False
    
    def get_cached_balance(self, username: str, branch: str, corporation: str,
                           brand: str) -> Tuple[Optional[float], Optional[str]]:
        """
        Get the cached ending balance for offline beginning balance auto-fill.
        Returns (balance, date) or (None, None) if not cached.
        """
        try:
            cache_path = self._get_balance_cache_path()
            
            if not os.path.exists(cache_path):
                return None, None
            
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached = json.load(f)
            
            key = f"{username}_{branch}_{corporation}_{brand}".lower()
            key = "".join(c if c.isalnum() or c == "_" else "_" for c in key)
            
            if key in cached:
                data = cached[key]
                return data.get("ending_balance"), data.get("date")
            
            return None, None
            
        except Exception as e:
            print(f"Failed to get cached balance: {e}")
            return None, None
    
    def get_latest_pending_balance(self, username: str, branch: str, corporation: str,
                                   brand: str, before_date: str) -> Tuple[Optional[float], Optional[str]]:
        """
        Get ending balance from pending entries for offline use.
        This checks pending entries that haven't been synced yet.
        Returns the most recent entry's ending balance before the given date.
        """
        try:
            pending_dir = _get_pending_path()
            latest_date = None
            latest_balance = None
            
            for filename in os.listdir(pending_dir):
                if not filename.endswith('.json'):
                    continue
                
                filepath = os.path.join(pending_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    entry = json.load(f)
                
                entry_data = entry.get('entry_data', {})
                if (entry_data.get('username') != username or
                    entry_data.get('branch') != branch or
                    entry_data.get('corporation') != corporation):
                    continue
                
                entry_date = entry_data.get('date')
                if not entry_date or entry_date >= before_date:
                    continue
                
                brand_data = entry_data.get('brand_data', {}).get(brand)
                if brand_data:
                    ending = brand_data.get('ending_balance')
                    if ending is not None:
                        if latest_date is None or entry_date > latest_date:
                            latest_date = entry_date
                            latest_balance = ending
            
            return latest_balance, latest_date
            
        except Exception as e:
            print(f"Failed to get pending balance: {e}")
            return None, None


# Global singleton instance
offline_manager = OfflineManager()
