import uuid
from django.db import models
from django.conf import settings


# Backend-enforced allowlist for permitted ChatMessage metadata fields.
# Strictly prohibits storing authentication tokens, guest secrets, JWTs, API keys, or credentials.
PERMITTED_METADATA_KEYS = frozenset({
    'detected_language',
    'confidence',
    'remedies',
    'terminology',
    'engine',
    'statutory_preserved',
    'response_time_ms',
    'tokens_used',
    'model_version',
})


def sanitize_chat_metadata(data: dict) -> dict:
    """
    Sanitizes message metadata against the strict backend allowlist.
    Strips any unapproved keys, secrets, or credentials before database persistence.
    """
    if not isinstance(data, dict):
        return {}
    return {k: v for k, v in data.items() if k in PERMITTED_METADATA_KEYS}


class ChatSession(models.Model):
    """
    Represents an isolated legal case or conversational thread in Law Mithra.
    Belongs to an authenticated User or remains a partitioned guest session (via guest_secret_hash).
    """
    class Role(models.TextChoices):
        NEUTRAL = 'neutral', 'Neutral Legal Inquiry'
        COMPLAINANT = 'complainant', 'Complainant / Victim'
        ACCUSED = 'accused', 'Accused / Respondent'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_sessions',
        null=True,
        blank=True,
        help_text="Owning user (null for guest/anonymous sessions)"
    )
    guest_secret_hash = models.CharField(
        max_length=64,
        blank=True,
        default='',
        db_index=True,
        help_text="SHA-256 digest of high-entropy guest access token"
    )
    title = models.CharField(
        max_length=255,
        default="New Legal Inquiry",
        help_text="Conversation summary or case title derived from initial query"
    )
    case_role = models.CharField(
        max_length=30,
        default=Role.NEUTRAL,
        choices=Role.choices,
        help_text="Role perspective for legal reasoning"
    )
    preferred_language = models.CharField(
        max_length=10,
        default='en',
        help_text="Active language code (e.g., en, kn, hi, te, ta, ml, mr, bn, gu, pa)"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Chat Session'
        verbose_name_plural = 'Chat Sessions'

    def __str__(self):
        owner = getattr(self.user, 'email', None) or "Guest"
        return f"{self.title[:30]} ({owner}) - {self.id}"


class ChatMessage(models.Model):
    """
    Represents an individual turn within a legal chat session.
    Chronologically sequenced with client idempotency protection and sanitized metadata.
    """
    class Sender(models.TextChoices):
        USER = 'user', 'User'
        ASSISTANT = 'assistant', 'Assistant'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='messages',
        help_text="Parent chat session"
    )
    sequence_number = models.PositiveIntegerField(
        db_index=True,
        help_text="Monotonically increasing sequence number per session"
    )
    client_request_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Client-generated UUID for idempotency per session (nullable for backward compatibility)"
    )
    sender = models.CharField(
        max_length=15,
        choices=Sender.choices,
        help_text="Role of turn sender (user or assistant)"
    )
    content = models.TextField(help_text="Message text content")
    statutory_citations = models.JSONField(
        default=list,
        blank=True,
        help_text="Structured acts and sections referenced in this response"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Sanitized metadata: language, confidence, remedies, and operational metrics only"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['sequence_number', 'created_at']
        unique_together = ('session', 'sequence_number')
        constraints = [
            models.UniqueConstraint(
                fields=['session', 'client_request_id'],
                name='unique_session_client_request_id',
                condition=models.Q(client_request_id__isnull=False)
            )
        ]
        verbose_name = 'Chat Message'
        verbose_name_plural = 'Chat Messages'

    def __str__(self):
        return f"[{self.sequence_number}] {self.sender}: {self.session.title[:20]}"

    def save(self, *args, **kwargs):
        """
        Enforce backend-level metadata sanitization before persisting.
        Guarantees that credentials, tokens, or arbitrary keys cannot be saved to DB.
        """
        if self.metadata:
            self.metadata = sanitize_chat_metadata(self.metadata)
        super().save(*args, **kwargs)
