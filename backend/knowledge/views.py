"""
Views for Multilingual Legal AI and Localization Engine.
Endpoints:
- POST /api/knowledge/chat/       (Legal AI Multilingual Assistant)
- GET  /api/knowledge/glossary/   (Legal Terminology Glossary)
- GET  /api/knowledge/languages/  (Supported Indian Languages)
- POST /api/knowledge/translate/  (Statutory-guarded translation)
"""

import hashlib
import secrets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from .models import ChatSession, ChatMessage
from .serializers import (
    ChatSessionListSerializer,
    ChatSessionDetailSerializer,
    ChatMessageSerializer,
)
from .services.language_detector import SUPPORTED_LANGUAGES, detect_language
from .services.statutory_guard import StatutoryGuard
from .services.terminology import get_all_terms_for_language
from .services.legal_ai_service import LegalAIService
from .services.gemini_client import GeminiClient

legal_ai_service = LegalAIService()


def get_session_queryset(request):
    """
    Returns queryset of ChatSessions belonging to the current authenticated user or guest.
    Validates ownership on every access to enforce privacy and isolation.
    """
    if request.user and request.user.is_authenticated:
        return ChatSession.objects.filter(user=request.user)

    guest_secret = request.headers.get('X-Guest-Secret') or request.query_params.get('guest_secret')
    if guest_secret:
        secret_hash = hashlib.sha256(guest_secret.strip().encode('utf-8')).hexdigest()
        return ChatSession.objects.filter(user__isnull=True, guest_secret_hash=secret_hash)

    return ChatSession.objects.none()


class ChatSessionListView(APIView):
    """
    List and create legal chat sessions.
    Authenticated users see their private history; guests can track via high-entropy secret.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary="List Chat Sessions",
        description="Returns list of conversation sessions belonging to the authenticated user.",
        responses={200: ChatSessionListSerializer(many=True)}
    )
    def get(self, request):
        qs = get_session_queryset(request).order_by('-updated_at')
        serializer = ChatSessionListSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Create Chat Session",
        description="Creates a new conversation thread with distinct identity.",
        responses={201: ChatSessionDetailSerializer}
    )
    def post(self, request):
        title = str(request.data.get('title', 'New Legal Inquiry')).strip() or 'New Legal Inquiry'
        case_role = request.data.get('case_role', ChatSession.Role.NEUTRAL)
        preferred_language = request.data.get('preferred_language', 'en')

        if request.user and request.user.is_authenticated:
            session = ChatSession.objects.create(
                user=request.user,
                title=title[:255],
                case_role=case_role,
                preferred_language=preferred_language
            )
            serializer = ChatSessionDetailSerializer(session)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            raw_secret = secrets.token_urlsafe(32)
            secret_hash = hashlib.sha256(raw_secret.encode('utf-8')).hexdigest()
            session = ChatSession.objects.create(
                user=None,
                guest_secret_hash=secret_hash,
                title=title[:255],
                case_role=case_role,
                preferred_language=preferred_language
            )
            data = ChatSessionDetailSerializer(session).data
            data['guest_secret'] = raw_secret
            return Response(data, status=status.HTTP_201_CREATED)


class ChatSessionDetailView(APIView):
    """
    Retrieve or delete an individual chat session.
    Strictly verifies ownership so users can never access or delete another user's session.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Get Chat Session Detail",
        description="Retrieves session with chronologically ordered message thread.",
        responses={200: ChatSessionDetailSerializer}
    )
    def get(self, request, session_id):
        session = get_session_queryset(request).filter(id=session_id).first()
        if not session:
            return Response(
                {"error": "Chat session not found or access denied."},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = ChatSessionDetailSerializer(session)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Delete Chat Session",
        description="Deletes a specific chat session without affecting others.",
        responses={200: OpenApiTypes.OBJECT}
    )
    def delete(self, request, session_id):
        session = get_session_queryset(request).filter(id=session_id).first()
        if not session:
            return Response(
                {"error": "Chat session not found or access denied."},
                status=status.HTTP_404_NOT_FOUND
            )
        session.delete()
        return Response(
            {"detail": "Chat session deleted successfully."},
            status=status.HTTP_200_OK
        )


class CaseAnalysisView(APIView):
    """
    AI Legal Case Analysis API Endpoint.
    Takes a legal scenario or complaint text and returns a full 7-section structured JSON analysis.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary="AI Legal Case Analysis",
        description="Comprehensive case analysis adhering to Indian statutory law, civil/criminal court procedure, timelines, and strategy.",
        responses={200: OpenApiTypes.OBJECT}
    )
    def post(self, request):
        case_text = request.data.get('case_text') or request.data.get('query') or request.data.get('text', '')
        case_text = str(case_text).strip()
        if not case_text:
            return Response(
                {"error": "Legal case text is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        lang = request.data.get('language') or request.data.get('preferred_language', 'en')
        gemini = GeminiClient()
        analysis = gemini.analyze_legal_case(case_text=case_text, language=lang)
        return Response(analysis, status=status.HTTP_200_OK)


class LegalChatView(APIView):
    """
    Multilingual Legal AI Conversation Endpoint.
    Accepts natural language legal questions in 10 Indian languages.
    Performs issue extraction, section retrieval, and returns dual-statute guidance.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Ask Multilingual Legal AI",
        description="Processes a legal question in any supported Indian language and returns remedies and verified sections.",
        responses={200: OpenApiTypes.OBJECT}
    )
    def post(self, request):
        query_text = request.data.get('query', '').strip()
        if not query_text:
            return Response(
                {"error": "Legal question query is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # User's language preference
        user_lang = 'en'
        if request.user and request.user.is_authenticated and hasattr(request.user, 'profile'):
            user_lang = request.user.profile.preferred_language or 'en'
        elif 'preferred_language' in request.data:
            user_lang = request.data.get('preferred_language', 'en')

        auto_detect = request.data.get('auto_detect_language', True)
        session_id = request.data.get('session_id')
        client_request_id = request.data.get('client_request_id')

        # Resolve or create the ChatSession
        session = None
        if session_id:
            session = get_session_queryset(request).filter(id=session_id).first()
            if not session:
                return Response(
                    {"error": "Chat session not found or access denied."},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            title = query_text[:35] + ('...' if len(query_text) > 35 else '')
            if request.user and request.user.is_authenticated:
                session = ChatSession.objects.create(
                    user=request.user,
                    title=title,
                    preferred_language=user_lang
                )
            else:
                raw_secret = secrets.token_urlsafe(32)
                secret_hash = hashlib.sha256(raw_secret.encode('utf-8')).hexdigest()
                session = ChatSession.objects.create(
                    user=None,
                    guest_secret_hash=secret_hash,
                    title=title,
                    preferred_language=user_lang
                )

        # Idempotency check: if client_request_id already saved, return replayed response
        if client_request_id:
            existing_user_msg = ChatMessage.objects.filter(session=session, client_request_id=client_request_id).first()
            if existing_user_msg:
                asst_msg = ChatMessage.objects.filter(session=session, sequence_number=existing_user_msg.sequence_number + 1).first()
                if asst_msg:
                    return Response({
                        'legal_issue': asst_msg.content,
                        'explanation': asst_msg.content,
                        'applicable_sections': asst_msg.statutory_citations,
                        'remedies': asst_msg.metadata.get('remedies', []),
                        'detected_language': asst_msg.metadata.get('detected_language', user_lang),
                        'session_id': str(session.id),
                        'session_title': session.title,
                        'idempotent_replay': True,
                    }, status=status.HTTP_200_OK)

        # Determine sequence number for user message
        last_msg = session.messages.order_by('-sequence_number').first()
        next_seq = (last_msg.sequence_number + 1) if last_msg else 1

        # Save user turn
        user_msg = ChatMessage.objects.create(
            session=session,
            sequence_number=next_seq,
            client_request_id=client_request_id if client_request_id else None,
            sender=ChatMessage.Sender.USER,
            content=query_text,
            metadata={'preferred_language': user_lang}
        )

        try:
            result = legal_ai_service.process_query(
                query_text=query_text,
                preferred_lang=user_lang,
                auto_detect_lang=auto_detect
            )

            # Save assistant turn
            asst_content = result.get('legal_issue') or result.get('explanation') or 'Statutory remedies retrieved.'
            asst_msg = ChatMessage.objects.create(
                session=session,
                sequence_number=next_seq + 1,
                sender=ChatMessage.Sender.ASSISTANT,
                content=asst_content,
                statutory_citations=result.get('applicable_sections', []),
                metadata={
                    'detected_language': result.get('detected_language', user_lang),
                    'confidence': result.get('confidence', 0.95),
                    'remedies': result.get('remedies', []),
                }
            )

            # Update session timestamp and title if it was initial
            if session.title == "New Legal Inquiry" or session.messages.count() <= 2:
                session.title = query_text[:35] + ('...' if len(query_text) > 35 else '')
            session.save()

            # Include session metadata in response
            result['session_id'] = str(session.id)
            result['session_title'] = session.title
            result['user_message_id'] = str(user_msg.id)
            result['assistant_message_id'] = str(asst_msg.id)

            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Failed to process legal query: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LegalGlossaryView(APIView):
    """
    Returns legal terminology glossary across Indian languages.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Get Legal Glossary",
        parameters=[
            OpenApiParameter('lang', OpenApiTypes.STR, description="Language code (e.g. kn, hi, ta)")
        ]
    )
    def get(self, request):
        lang = request.query_params.get('lang', 'en')
        terms = get_all_terms_for_language(lang)
        return Response({"language": lang, "terms": terms})


class SupportedLanguagesView(APIView):
    """
    Lists the 10 supported Indian languages with their native scripts.
    """
    permission_classes = [AllowAny]

    @extend_schema(summary="List Supported Indian Languages")
    def get(self, request):
        languages_list = [
            {'code': code, **meta}
            for code, meta in SUPPORTED_LANGUAGES.items()
        ]
        return Response({"languages": languages_list})


class StatutoryTranslateView(APIView):
    """
    Statutory-Guarded Machine Translation Endpoint.
    Never alters section numbers, penalties, fines, or statutory conditions.
    """
    permission_classes = [AllowAny]

    @extend_schema(summary="Translate Legal Text with Statutory Guard")
    def post(self, request):
        text = request.data.get('text', '')
        source_lang = request.data.get('source_language', 'en')
        target_lang = request.data.get('target_language', 'en')

        if not text:
            return Response({"error": "Text is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Mask statutory numbers
        masked, token_map = StatutoryGuard.mask_statutory_entities(text)

        # Attempt translation
        translated = None
        if legal_ai_service.bhashini.is_configured:
            translated = legal_ai_service.bhashini.translate(masked, source_lang, target_lang)
        elif legal_ai_service.indictrans.is_configured:
            translated = legal_ai_service.indictrans.translate(masked, source_lang, target_lang)

        final_translated = StatutoryGuard.unmask_statutory_entities(translated or text, token_map)
        is_preserved, missing = StatutoryGuard.validate_preservation(text, final_translated)

        return Response({
            "original": text,
            "translated": final_translated,
            "source_language": source_lang,
            "target_language": target_lang,
            "statutory_preserved": is_preserved,
            "engine": "bhashini" if legal_ai_service.bhashini.is_configured else "statutory_guard_local"
        })
