#pylint: disable=C0301,E0401,R0914,W0718,W0612,E0611,R0912,R0915,R1702,R0903
"""
PII Redaction Filter for Logging System.

This module provides a centralized PII redaction filter that automatically
sanitizes Personally Identifiable Information from log records before emission.
"""

import re
import logging
import hashlib
from typing import Any, Dict, Optional


class PIIRedactionFilter(logging.Filter):
    """
    Logging filter that automatically redacts PII from log records.

    This filter provides comprehensive PII protection by:
    1. Redacting email addresses from log messages
    2. Masking sensitive fields in extra data
    3. Providing configurable redaction patterns
    4. Supporting hash-based anonymization for debugging
    """

    # Email pattern for detection and redaction
    EMAIL_PATTERN = re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    )

    # User ID patterns (common formats)
    USER_ID_PATTERNS = [
        re.compile(r'\buser_id[:\s=]+(\w+)\b', re.IGNORECASE),
        re.compile(r'\buserid[:\s=]+(\w+)\b', re.IGNORECASE),
        re.compile(r'\bcustomer_id[:\s=]+(\w+)\b', re.IGNORECASE),
        re.compile(r'\bclient_id[:\s=]+(\w+)\b', re.IGNORECASE),
    ]

    # Phone number patterns
    PHONE_PATTERNS = [
        re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),  # US format
        re.compile(r'\b\+?\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b'),  # International
    ]

    # Sensitive field names that should be redacted
    SENSITIVE_FIELD_NAMES = {
        'email', 'recipient_email', 'guest_email', 'user_email', 'client_email',
        'user_id', 'customer_id', 'client_id', 'guest_id',
        'telephone', 'phone', 'mobile', 'contact_number',
        'name', 'surname', 'first_name', 'last_name', 'full_name',
        'name_reference', 'guest_name', 'reservation_number', 'reservationnumber', 'id_reference',
        'document_number', 'document_type', 'tax_code', 'cf',
        'street', 'address', 'city', 'province', 'cap',
        'birth_city', 'birth_country', 'residence_city', 'residence_country',
        'password', 'passwd', 'secret', 'token', 'key', 'authorization',
        'x-api-key', 'x-auth-token', 'cookie', 'session',
        'portale_password', 'portale_username', 'wskey', 'web_service_key'
    }

    def __init__(self,
                 use_hash_anonymization: bool = True,
                 hash_salt: Optional[str] = None,
                 redaction_string: str = "***REDACTED***"):
        """
        Initialize PII redaction filter.

        Args:
            use_hash_anonymization: Whether to use hash-based anonymization for emails
            hash_salt: Salt for hash-based anonymization (uses default if None)
            redaction_string: String to replace redacted content with
        """
        super().__init__()
        self.use_hash_anonymization = use_hash_anonymization
        self.hash_salt = hash_salt or "pii_redaction_salt_2024"
        self.redaction_string = redaction_string

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter and redact PII from log record.

        Args:
            record: Log record to process

        Returns:
            True (record should be logged)
        """
        # Redact PII from the main log message
        if hasattr(record, 'getMessage'):
            original_msg = record.getMessage()
            redacted_msg = self._redact_message(original_msg)

            # Update the message if redaction occurred
            if redacted_msg != original_msg:
                record.msg = redacted_msg
                record.args = ()

        # Redact PII from extra fields
        if hasattr(record, '__dict__'):
            self._redact_extra_fields(record)

        return True

    def _redact_message(self, message: str) -> str:
        """
        Redact PII from log message string.

        Args:
            message: Original log message

        Returns:
            Redacted log message
        """
        if not isinstance(message, str):
            return message

        # Redact email addresses
        message = self._redact_emails(message)

        # Redact user IDs
        message = self._redact_user_ids(message)

        # Redact phone numbers
        message = self._redact_phone_numbers(message)

        return message

    def _redact_emails(self, text: str) -> str:
        """Redact email addresses from text."""
        def replace_email(match):
            email = match.group(0)
            if self.use_hash_anonymization:
                return self._anonymize_email(email)
            return self.redaction_string

        return self.EMAIL_PATTERN.sub(replace_email, text)

    def _redact_user_ids(self, text: str) -> str:
        """Redact user IDs from text."""
        def replace_user_id(match):
            if self.use_hash_anonymization:
                user_id = match.group(1)
                return match.group(0).replace(user_id, self._hash_value(user_id))
            return match.group(0).replace(match.group(1), self.redaction_string)

        for pattern in self.USER_ID_PATTERNS:
            text = pattern.sub(replace_user_id, text)

        return text

    def _redact_phone_numbers(self, text: str) -> str:
        """Redact phone numbers from text."""
        def replace_phone(match):
            if self.use_hash_anonymization:
                phone = match.group(0)
                return self._hash_value(phone)
            return self.redaction_string

        for pattern in self.PHONE_PATTERNS:
            text = pattern.sub(replace_phone, text)

        return text

    def _redact_extra_fields(self, record: logging.LogRecord) -> None:
        """Redact PII from extra fields in log record."""
        for key, value in record.__dict__.items():
            # Skip standard logging fields
            if key in {'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                      'filename', 'module', 'lineno', 'funcName', 'created',
                      'msecs', 'relativeCreated', 'thread', 'threadName',
                      'processName', 'process', 'exc_info', 'exc_text',
                      'stack_info', 'getMessage', 'taskName', 'asctime', 'message'}:
                continue

            # Check if field name indicates sensitive data
            if self._is_sensitive_field_name(key):
                if self.use_hash_anonymization and isinstance(value, str):
                    record.__dict__[key] = self._hash_value(value)
                else:
                    record.__dict__[key] = self.redaction_string

            # Recursively process nested dictionaries
            elif isinstance(value, dict):
                record.__dict__[key] = self._redact_dict(value)

            # Process list values
            elif isinstance(value, list):
                record.__dict__[key] = [self._redact_value(item) for item in value]

            # Process string values for embedded PII
            elif isinstance(value, str):
                redacted_value = self._redact_message(value)
                if redacted_value != value:
                    record.__dict__[key] = redacted_value

    def _redact_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively redact PII from dictionary."""
        redacted = {}
        for key, value in data.items():
            if self._is_sensitive_field_name(key):
                if self.use_hash_anonymization and isinstance(value, str):
                    redacted[key] = self._hash_value(value)
                else:
                    redacted[key] = self.redaction_string
            elif isinstance(value, dict):
                redacted[key] = self._redact_dict(value)
            elif isinstance(value, list):
                redacted[key] = [self._redact_value(item) for item in value]
            elif isinstance(value, str):
                redacted_value = self._redact_message(value)
                redacted[key] = redacted_value if redacted_value != value else value
            else:
                redacted[key] = value
        return redacted

    def _redact_value(self, value: Any) -> Any:
        """Redact PII from a single value."""
        if isinstance(value, dict):
            return self._redact_dict(value)
        if isinstance(value, str):
            return self._redact_message(value)
        return value

    def _is_sensitive_field_name(self, field_name: str) -> bool:
        """Check if field name indicates sensitive data."""
        field_lower = field_name.lower()
        return any(sensitive in field_lower for sensitive in self.SENSITIVE_FIELD_NAMES)

    def _anonymize_email(self, email: str) -> str:
        """
        Anonymize email address while preserving domain for debugging.

        Args:
            email: Email address to anonymize

        Returns:
            Anonymized email (e.g., "jo***@example.com")
        """
        if '@' not in email:
            return self.redaction_string

        local, domain = email.split('@', 1)
        if len(local) <= 2:
            return f"{local[0]}***@{domain}"
        return f"{local[:2]}***@{domain}"

    def _hash_value(self, value: str) -> str:
        """
        Create a short hash of a value for anonymization.

        Args:
            value: Value to hash

        Returns:
            Short hash prefixed with identifier
        """
        if not value:
            return self.redaction_string

        # Create a short, consistent hash
        hash_obj = hashlib.md5()
        hash_obj.update(f"{self.hash_salt}{value}".encode('utf-8'))
        short_hash = hash_obj.hexdigest()[:8]

        return f"HASH_{short_hash}"


def setup_pii_filter(logger: logging.Logger,
                    use_hash_anonymization: bool = True,
                    hash_salt: Optional[str] = None) -> PIIRedactionFilter:
    """
    Setup PII redaction filter on a logger.

    Args:
        logger: Logger to add filter to
        use_hash_anonymization: Whether to use hash-based anonymization
        hash_salt: Salt for hash-based anonymization

    Returns:
        The configured PIIRedactionFilter instance
    """
    pii_filter = PIIRedactionFilter(
        use_hash_anonymization=use_hash_anonymization,
        hash_salt=hash_salt
    )

    logger.addFilter(pii_filter)
    return pii_filter
