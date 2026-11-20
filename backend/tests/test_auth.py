import pytest
import os
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from documents.models import Document, DocumentPage
from accounts.models import UserProfile


@pytest.fixture(autouse=True)
def clear_throttle_cache():
    """Clear Django cache between tests to avoid throttle bleed-over."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_register_login_refresh_logout(api_client):
    """
    Test registration, login, refresh token rotation, and logout.
    """
    # 1. Register
    register_url = reverse('auth-register')
    reg_payload = {
        'email': 'citizen@example.com',
        'password': 'StrongPassword!2026',
        'preferred_language': 'kn',
        'text_size': 'large',
    }
    reg_res = api_client.post(register_url, reg_payload, format='json')
    assert reg_res.status_code == status.HTTP_201_CREATED
    data = reg_res.json()
    assert 'access' in data
    assert 'refresh' in data
    assert data['user']['email'] == 'citizen@example.com'
    assert data['user']['preferred_language'] == 'kn'
    assert data['user']['text_size'] == 'large'
    assert 'refresh_token' in reg_res.cookies

    # 2. Login
    login_url = reverse('auth-login')
    login_payload = {
        'email': 'CITIZEN@EXAMPLE.COM',  # Case-insensitive test
        'password': 'StrongPassword!2026',
    }
    login_res = api_client.post(login_url, login_payload, format='json')
    assert login_res.status_code == status.HTTP_200_OK
    login_data = login_res.json()
    access_token = login_data['access']
    refresh_token = login_data['refresh']
    assert access_token is not None

    # 3. Refresh token
    refresh_url = reverse('auth-refresh')
    # Use cookie or payload
    ref_res = api_client.post(refresh_url, {'refresh': refresh_token}, format='json')
    assert ref_res.status_code == status.HTTP_200_OK
    new_access = ref_res.json().get('access')
    assert new_access is not None

    # 4. Profile endpoint /api/auth/me/
    me_url = reverse('auth-me')
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {new_access}')
    me_res = api_client.get(me_url)
    assert me_res.status_code == status.HTTP_200_OK
    assert me_res.json()['email'] == 'citizen@example.com'

    # 5. Patch Profile
    patch_res = api_client.patch(me_url, {'preferred_language': 'hi'}, format='json')
    assert patch_res.status_code == status.HTTP_200_OK
    assert patch_res.json()['preferred_language'] == 'hi'

    # 6. Logout
    logout_url = reverse('auth-logout')
    logout_res = api_client.post(logout_url, {'refresh': ref_res.json().get('refresh')}, format='json')
    assert logout_res.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_duplicate_email_rejected(api_client):
    """
    Test duplicate email (case-insensitive) is rejected with 400.
    """
    User.objects.create_user(username='test@lawmithra.in', email='test@lawmithra.in', password='StrongPassword!123')
    register_url = reverse('auth-register')
    res = api_client.post(register_url, {
        'email': 'TEST@LAWMITHRA.IN',
        'password': 'StrongPassword!123',
    }, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert 'email' in res.json()


@pytest.mark.django_db
def test_weak_password_rejected(api_client):
    """
    Test weak/short password is rejected by Django's password validators.
    """
    register_url = reverse('auth-register')
    res = api_client.post(register_url, {
        'email': 'weakpass@lawmithra.in',
        'password': '123',
    }, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert 'password' in res.json()


@pytest.mark.django_db
def test_unauthenticated_request_to_documents_returns_401(api_client):
    """
    Test unauthenticated access to /api/documents/ returns 401.
    """
    res = api_client.get(reverse('document-list-create'))
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

    upload_res = api_client.post(reverse('document-upload'), {}, format='multipart')
    assert upload_res.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_user_isolation_user_b_cannot_access_user_a_documents(api_client, tmp_path):
    """
    Test User A uploads a document; User B gets 404 on detail, delete, and reprocess,
    and does not see User A's document in the list.
    """
    user_a = User.objects.create_user(username='user_a@test.com', email='user_a@test.com', password='Password123!')
    user_b = User.objects.create_user(username='user_b@test.com', email='user_b@test.com', password='Password123!')

    # User A uploads a document
    doc_a = Document.objects.create(
        owner=user_a,
        title="User A Private Notice",
        file="documents/sample_a.pdf",
        status=Document.Status.COMPLETED
    )

    # Authenticate as User B
    refresh_b = RefreshToken.for_user(user_b)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh_b.access_token}')

    # 1. User B lists documents -> empty list
    list_res = api_client.get(reverse('document-list-create'))
    assert list_res.status_code == status.HTTP_200_OK
    assert len(list_res.json()) == 0

    # 2. User B requests User A's document detail -> 404 (not 403)
    detail_url = reverse('document-detail', kwargs={'pk': doc_a.id})
    detail_res = api_client.get(detail_url)
    assert detail_res.status_code == status.HTTP_404_NOT_FOUND

    # 3. User B requests User A's document delete -> 404 (not 403)
    delete_res = api_client.delete(detail_url)
    assert delete_res.status_code == status.HTTP_404_NOT_FOUND

    # 4. User B requests User A's document reprocess -> 404 (not 403)
    reprocess_url = reverse('document-reprocess', kwargs={'pk': doc_a.id})
    reprocess_res = api_client.post(reprocess_url)
    assert reprocess_res.status_code == status.HTTP_404_NOT_FOUND

    # 5. User B requests User A's document download -> 404 (not 403)
    download_url = reverse('document-download', kwargs={'pk': doc_a.id})
    download_res = api_client.get(download_url)
    assert download_res.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_delete_account_removes_user_documents_pages_and_files(api_client, settings, tmp_path):
    """
    Test deleting user account permanently purges user, all owned documents,
    pages, and physical files from disk.
    """
    settings.MEDIA_ROOT = tmp_path
    user = User.objects.create_user(username='delete_me@test.com', email='delete_me@test.com', password='ValidPassword123!')
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    # Upload document
    uploaded = SimpleUploadedFile("petition_to_delete.txt", b"Confidential client data", content_type="text/plain")
    upload_url = reverse('document-upload') + "?sync=true"
    up_res = api_client.post(upload_url, {'file': uploaded}, format='multipart')
    assert up_res.status_code == status.HTTP_201_CREATED
    doc_id = up_res.json()['id']

    doc = Document.objects.get(id=doc_id)
    file_path = doc.file.path
    assert os.path.exists(file_path)
    assert doc.pages.count() > 0

    # 1. Reject account deletion if password is wrong
    delete_url = reverse('auth-me')
    bad_res = api_client.delete(delete_url, {'password': 'WrongPassword'}, format='json')
    assert bad_res.status_code == status.HTTP_400_BAD_REQUEST
    assert User.objects.filter(id=user.id).exists()
    assert os.path.exists(file_path)

    # 2. Confirm account deletion with correct password
    good_res = api_client.delete(delete_url, {'password': 'ValidPassword123!'}, format='json')
    assert good_res.status_code == status.HTTP_204_NO_CONTENT

    # Assert user is deleted
    assert not User.objects.filter(id=user.id).exists()

    # Assert document & pages deleted
    assert not Document.objects.filter(id=doc_id).exists()
    assert not DocumentPage.objects.filter(document_id=doc_id).exists()

    # Assert physical file deleted from storage
    assert not os.path.exists(file_path)


@pytest.mark.django_db
def test_login_throttling_returns_429(api_client):
    """
    Test login endpoint returns 429 Too Many Requests after 5 attempts per minute.
    """
    login_url = reverse('auth-login')
    payload = {'email': 'nobody@test.com', 'password': 'WrongPassword123'}

    # 5 allowed attempts
    for _ in range(5):
        res = api_client.post(login_url, payload, format='json')
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    # 6th attempt throttled
    throttled_res = api_client.post(login_url, payload, format='json')
    assert throttled_res.status_code == status.HTTP_429_TOO_MANY_REQUESTS


@pytest.mark.django_db
def test_registration_normalization_and_login_case_insensitivity(api_client):
    """
    Test registration normalizes email with leading/trailing whitespace and mixed case,
    and subsequent logins succeed regardless of casing or whitespace.
    """
    reg_url = reverse('auth-register')
    reg_payload = {
        'full_name': 'Asha Devi',
        'email': '  Asha.Devi@LawMithra.IN  ',
        'password': 'SecurePassword!2026',
        'confirm_password': 'SecurePassword!2026',
        'preferred_language': 'kn',
    }
    reg_res = api_client.post(reg_url, reg_payload, format='json')
    assert reg_res.status_code == status.HTTP_201_CREATED
    data = reg_res.json()
    assert data['user']['email'] == 'asha.devi@lawmithra.in'

    # Verify User record in DB has normalized email and username
    user = User.objects.get(email='asha.devi@lawmithra.in')
    assert user.username == 'asha.devi@lawmithra.in'
    assert hasattr(user, 'profile')
    assert user.profile.preferred_language == 'kn'

    login_url = reverse('auth-login')

    # 1. Login with exact lowercase
    res_lower = api_client.post(login_url, {
        'email': 'asha.devi@lawmithra.in',
        'password': 'SecurePassword!2026',
    }, format='json')
    assert res_lower.status_code == status.HTTP_200_OK

    # 2. Login with uppercase and trailing spaces
    res_upper = api_client.post(login_url, {
        'email': '  ASHA.DEVI@LAWMITHRA.IN  ',
        'password': 'SecurePassword!2026',
    }, format='json')
    assert res_upper.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_registration_rejects_conflicting_username(api_client):
    """
    Test registration returns 400 Bad Request (not 500) if username already exists in auth_user.
    """
    User.objects.create(username='legacy.user@lawmithra.in', email='')

    reg_url = reverse('auth-register')
    res = api_client.post(reg_url, {
        'full_name': 'Legacy User',
        'email': 'LEGACY.USER@LAWMITHRA.IN',
        'password': 'StrongPassword!2026',
        'confirm_password': 'StrongPassword!2026',
    }, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert 'email' in res.json()
    assert 'already exists' in res.json()['email'][0].lower()


@pytest.mark.django_db
def test_login_handles_duplicate_email_candidates_safely(api_client):
    """
    Test login checks password across candidate users and does not crash with MultipleObjectsReturned.
    """
    u1 = User.objects.create(username='dupe_acc_1', email='shared@lawmithra.in')
    u1.set_password('PasswordOne!123')
    u1.save()

    u2 = User.objects.create(username='dupe_acc_2', email='shared@lawmithra.in')
    u2.set_password('PasswordTwo!456')
    u2.save()

    login_url = reverse('auth-login')

    # Login matching user 1
    res1 = api_client.post(login_url, {'email': 'shared@lawmithra.in', 'password': 'PasswordOne!123'}, format='json')
    assert res1.status_code == status.HTTP_200_OK
    assert res1.json()['user']['id'] == u1.id

    # Login matching user 2
    res2 = api_client.post(login_url, {'email': 'shared@lawmithra.in', 'password': 'PasswordTwo!456'}, format='json')
    assert res2.status_code == status.HTTP_200_OK
    assert res2.json()['user']['id'] == u2.id

    # Wrong password for both
    res_bad = api_client.post(login_url, {'email': 'shared@lawmithra.in', 'password': 'WrongPassword!'}, format='json')
    assert res_bad.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_login_supports_username(api_client):
    """
    Test login supports username even when username is not in standard email address format.
    """
    admin_user = User.objects.create_user(username='court_registrar', email='registrar@karnataka.gov.in', password='RegistrarPassword!2026')

    login_url = reverse('auth-login')

    # Log in using username
    res = api_client.post(login_url, {'email': 'court_registrar', 'password': 'RegistrarPassword!2026'}, format='json')
    assert res.status_code == status.HTTP_200_OK
    assert res.json()['user']['id'] == admin_user.id


@pytest.mark.django_db
def test_login_disabled_account_rejected(api_client):
    """
    Test disabled accounts receive a clear, safe 400 rejection message.
    """
    user = User.objects.create_user(username='suspended@lawmithra.in', email='suspended@lawmithra.in', password='ValidPassword!2026', is_active=False)

    login_url = reverse('auth-login')
    res = api_client.post(login_url, {'email': 'suspended@lawmithra.in', 'password': 'ValidPassword!2026'}, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert 'Account is disabled' in str(res.json())


@pytest.mark.django_db
def test_refresh_token_rejects_inactive_user(api_client):
    """
    Test refreshing an access token for a deactivated user returns 401 and clears cookie.
    """
    user = User.objects.create_user(username='temp_active@lawmithra.in', email='temp_active@lawmithra.in', password='ValidPassword!2026')
    refresh = RefreshToken.for_user(user)

    # Deactivate user
    user.is_active = False
    user.save()

    refresh_url = reverse('auth-refresh')
    res = api_client.post(refresh_url, {'refresh': str(refresh)}, format='json')
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert 'disabled' in str(res.json()).lower()


@pytest.mark.django_db
def test_change_password_cycle_and_relogin(api_client):
    """
    Test password change validation:
    - Rejects same password
    - Rejects invalid current password
    - Successfully changes password
    - Disallows login with old password
    - Allows login with new password
    - Returns fresh valid JWT tokens
    """
    user = User.objects.create_user(username='pwd_test@lawmithra.in', email='pwd_test@lawmithra.in', password='OldPassword!2026')
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    change_url = reverse('auth-change-password')

    # 1. Rejects new_password identical to current_password
    res_same = api_client.post(change_url, {
        'current_password': 'OldPassword!2026',
        'new_password': 'OldPassword!2026',
    }, format='json')
    assert res_same.status_code == status.HTTP_400_BAD_REQUEST
    assert 'new_password' in res_same.json()

    # 2. Rejects incorrect current password
    res_wrong = api_client.post(change_url, {
        'current_password': 'WrongCurrentPassword',
        'new_password': 'NewBrandPassword!2026',
    }, format='json')
    assert res_wrong.status_code == status.HTTP_400_BAD_REQUEST

    # 3. Valid password change
    res_good = api_client.post(change_url, {
        'current_password': 'OldPassword!2026',
        'new_password': 'NewBrandPassword!2026',
    }, format='json')
    assert res_good.status_code == status.HTTP_200_OK
    assert 'access' in res_good.json()
    assert 'refresh' in res_good.json()

    # 4. Old password rejected at login
    api_client.credentials()  # clear credentials
    login_url = reverse('auth-login')
    old_res = api_client.post(login_url, {
        'email': 'pwd_test@lawmithra.in',
        'password': 'OldPassword!2026',
    }, format='json')
    assert old_res.status_code == status.HTTP_400_BAD_REQUEST

    # 5. New password accepted at login
    new_res = api_client.post(login_url, {
        'email': 'pwd_test@lawmithra.in',
        'password': 'NewBrandPassword!2026',
    }, format='json')
    assert new_res.status_code == status.HTTP_200_OK
    assert 'access' in new_res.json()
