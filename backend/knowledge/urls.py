from django.urls import path
from .views import (
    LegalChatView,
    CaseAnalysisView,
    LegalGlossaryView,
    SupportedLanguagesView,
    StatutoryTranslateView,
    ChatSessionListView,
    ChatSessionDetailView,
)

urlpatterns = [
    path('chat/', LegalChatView.as_view(), name='knowledge-chat'),
    path('sessions/', ChatSessionListView.as_view(), name='knowledge-session-list'),
    path('sessions/<uuid:session_id>/', ChatSessionDetailView.as_view(), name='knowledge-session-detail'),
    path('case-analysis/', CaseAnalysisView.as_view(), name='knowledge-case-analysis'),
    path('glossary/', LegalGlossaryView.as_view(), name='knowledge-glossary'),
    path('languages/', SupportedLanguagesView.as_view(), name='knowledge-languages'),
    path('translate/', StatutoryTranslateView.as_view(), name='knowledge-translate'),
]

