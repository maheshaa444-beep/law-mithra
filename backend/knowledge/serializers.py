from rest_framework import serializers
from .models import ChatSession, ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    """
    Serializer for individual conversation turns.
    """
    class Meta:
        model = ChatMessage
        fields = (
            'id',
            'sequence_number',
            'client_request_id',
            'sender',
            'content',
            'statutory_citations',
            'metadata',
            'created_at',
        )
        read_only_fields = fields


class ChatSessionListSerializer(serializers.ModelSerializer):
    """
    Lightweight metadata-only serializer for session listing.
    Never exposes message texts, internal hashes, or guest secrets.
    """
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatSession
        fields = (
            'id',
            'title',
            'case_role',
            'preferred_language',
            'message_count',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields

    def get_message_count(self, obj) -> int:
        return obj.messages.count()


class ChatSessionDetailSerializer(serializers.ModelSerializer):
    """
    Full session detail serializer with chronologically ordered message thread.
    Never exposes guest_secret_hash.
    """
    messages = ChatMessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatSession
        fields = (
            'id',
            'title',
            'case_role',
            'preferred_language',
            'message_count',
            'created_at',
            'updated_at',
            'messages',
        )
        read_only_fields = fields

    def get_message_count(self, obj) -> int:
        return obj.messages.count()


class ChatTurnInputSerializer(serializers.Serializer):
    """
    Input validation serializer for legal chat queries.
    Strictly requires client_request_id for idempotency on all chat submissions.
    """
    query = serializers.CharField(required=True, allow_blank=False, max_length=10000)
    client_request_id = serializers.UUIDField(
        required=True,
        allow_null=False,
        help_text="Mandatory client-generated UUID for exactly-once idempotency protection"
    )
    session_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    preferred_language = serializers.CharField(required=False, default='en', max_length=10)
    auto_detect_language = serializers.BooleanField(required=False, default=True)
    case_role = serializers.ChoiceField(
        choices=ChatSession.Role.choices,
        required=False,
        default=ChatSession.Role.NEUTRAL
    )
