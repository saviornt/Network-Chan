"""Password strength validation utilities – NIST SP 800-63B & modern NSA compliant.

Follows current NIST guidance:
- Minimum length (12+ chars recommended)
- No composition rules (no forced uppercase/symbols/digits)
- Blacklist common/breached passwords
- Allow long passwords and Unicode

Provides user-facing feedback for the setup/change-password flow.
"""

from typing import List, Optional, Tuple

import zxcvbn  # pip install zxcvbn (very good entropy estimation)

from shared.src.config.auth_settings import auth_settings


class PasswordValidationError(Exception):
    """Raised when password fails validation."""

    pass


class PasswordValidator:
    """
    Validates password strength according to modern NIST/NSA recommendations.

    Usage:
        validator = PasswordValidator()
        is_valid, feedback = validator.validate("my-very-long-password-2026")
    """

    def __init__(self):
        # Load common passwords (can be extended with HIBP-style list)
        self.common_passwords: set[str] = {
            "password",
            "123456",
            "admin",
            "letmein",
            "qwerty",
            "welcome",
            # Add ~10,000 most common ones in production (from rockyou.txt, etc.)
        }

    def validate(
        self,
        password: str,
        username: Optional[str] = None,
        user_data: Optional[List[str]] = None,
    ) -> Tuple[bool, List[str]]:
        """
        Validate password strength.

        Args:
            password: The password to check
            username: Optional username (to prevent password == username)
            user_data: Optional list of other data (email, phone, etc.) to check against

        Returns:
            Tuple[bool, List[str]]: (is_valid, list of failure reasons or success hints)
        """
        feedback: List[str] = []

        # 1. Minimum length
        if len(password) < 12:
            feedback.append("Password must be at least 12 characters long.")
        elif len(password) >= 16:
            feedback.append("Good length! Longer passwords are much stronger.")

        # 2. Not too common
        if password.lower() in self.common_passwords:
            feedback.append("This password is too common and has likely been breached.")

        # 3. Not based on username or personal data
        if username and password.lower() == username.lower():
            feedback.append("Password should not be the same as your username.")
        if user_data:
            for item in user_data:
                if item and password.lower() == item.lower():
                    feedback.append("Password should not match personal information.")

        # 4. Entropy estimation (zxcvbn)
        result = zxcvbn.zxcvbn(
            password,
            user_inputs=[username] + (user_data or []) if username else [],
        )

        if result["score"] < 3:
            feedback.append(
                f"Password strength is weak (score {result['score']}/4). "
                "Consider adding more unique words or length."
            )
        elif result["score"] >= 4:
            feedback.append("Strong password!")

        # Final decision (length + score + blacklist)
        is_valid = (
            len(password) >= 12
            and result["score"] >= 3
            and password.lower() not in self.common_passwords
        )

        return is_valid, feedback


# Singleton instance
password_validator = PasswordValidator()
