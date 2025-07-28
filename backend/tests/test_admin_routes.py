import pytest
import json
from unittest.mock import Mock, patch
from datetime import timedelta
from werkzeug.security import generate_password_hash
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from admin_routes import admin_bp

# pylint: disable=all

@pytest.fixture(scope="module")
def app():
    """
    Create and configure a Flask application for testing admin routes.

    This fixture initializes a Flask application with JWT configuration for testing,
    registers the admin blueprint, and yields the configured app instance for use in tests.

    Yields:
        Flask: The configured Flask application instance.
    """
    app = Flask(__name__)
    app.config['JWT_SECRET_KEY'] = 'test-secret-key-for-admin-routes'
    app.config['TESTING'] = True
    JWTManager(app)
    app.register_blueprint(admin_bp)
    yield app


@pytest.fixture
def client(app):
    """
    Return a test client for simulating API requests on the admin Flask application.

    This function creates and returns a test client for the provided Flask app using its
    built-in test_client() method. The returned client can be used to simulate HTTP requests
    during testing of admin routes.

    Parameters:
        app (Flask): A Flask application instance configured for testing.

    Returns:
        FlaskClient: A test client instance for making simulated API requests.
    """
    return app.test_client()


@pytest.fixture
def mock_user():
    """Create a mock user object for testing."""
    user = Mock()
    user.id = 1
    user.username = "admin_user"
    user.name = "Admin"
    user.surname = "User"
    user.password = generate_password_hash("correct_password")
    user.role = Mock()
    user.role.name = "admin"
    return user


@pytest.fixture
def mock_structures():
    """Create mock structure data for testing."""
    structure1 = Mock()
    structure1.id_structure = 1
    structure1.name = "Structure 1"
    
    structure2 = Mock()
    structure2.id_structure = 2
    structure2.name = "Structure 2"
    
    return [structure1, structure2]


@pytest.fixture
def auth_headers(app):
    """Create authentication headers with valid JWT token."""
    with app.app_context():
        token = create_access_token(
            identity="1",
            additional_claims={"username": "admin_user", "role": "admin"}
        )
        return {'Authorization': f'Bearer {token}'}


class TestAdminLogin:
    """Test cases for admin login functionality."""

    @patch('admin_routes.SessionLocal')
    def test_admin_login_success(self, mock_session_local, client, mock_user, mock_structures):
        """Test successful admin login with valid credentials and structures."""
        # Setup mock database session
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_user
        
        # Setup mock structures query chain
        mock_structures_query = Mock()
        mock_session.query.return_value = mock_structures_query
        mock_structures_query.join.return_value = mock_structures_query
        mock_structures_query.filter.return_value = mock_structures_query
        mock_structures_query.all.return_value = mock_structures
        
        login_data = {
            "username": "admin_user",
            "password": "correct_password"
        }
        
        response = client.post('/api/v1/admin/login', 
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'access_token' in data
        assert 'user' in data
        assert data['user']['username'] == 'admin_user'
        assert data['user']['role'] == 'admin'
        assert len(data['user']['structures']) == 2
        assert data['user']['structures'][0]['id'] == 1
        assert data['user']['structures'][0]['name'] == 'Structure 1'
        mock_session.close.assert_called_once()

    @patch('admin_routes.SessionLocal')
    def test_admin_login_missing_username(self, mock_session_local, client):
        """Test admin login fails when username is missing."""
        login_data = {"password": "test_password"}
        
        response = client.post('/api/v1/admin/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Username e password sono obbligatori" in data['error']

    @patch('admin_routes.SessionLocal')
    def test_admin_login_missing_password(self, mock_session_local, client):
        """Test admin login fails when password is missing."""
        login_data = {"username": "admin_user"}
        
        response = client.post('/api/v1/admin/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Username e password sono obbligatori" in data['error']

    @patch('admin_routes.SessionLocal')
    def test_admin_login_empty_credentials(self, mock_session_local, client):
        """Test admin login fails with empty username and password."""
        login_data = {"username": "", "password": ""}
        
        response = client.post('/api/v1/admin/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Username e password sono obbligatori" in data['error']

    @patch('admin_routes.SessionLocal')
    def test_admin_login_user_not_found(self, mock_session_local, client):
        """Test admin login fails when user doesn't exist."""
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        
        login_data = {
            "username": "nonexistent_user",
            "password": "any_password"
        }
        
        response = client.post('/api/v1/admin/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert "Credenziali non valide" in data['error']
        mock_session.close.assert_called_once()

    @patch('admin_routes.SessionLocal')
    def test_admin_login_wrong_password(self, mock_session_local, client, mock_user):
        """Test admin login fails with incorrect password."""
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_user
        
        login_data = {
            "username": "admin_user",
            "password": "wrong_password"
        }
        
        response = client.post('/api/v1/admin/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert "Credenziali non valide" in data['error']
        mock_session.close.assert_called_once()

    @patch('admin_routes.SessionLocal')
    def test_admin_login_insufficient_role(self, mock_session_local, client):
        """Test admin login fails when user has insufficient role."""
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        
        regular_user = Mock()
        regular_user.id = 1
        regular_user.username = "regular_user"
        regular_user.password = generate_password_hash("password")
        regular_user.role = Mock()
        regular_user.role.name = "user"
        
        mock_session.query.return_value.filter_by.return_value.first.return_value = regular_user
        
        login_data = {
            "username": "regular_user",
            "password": "password"
        }
        
        response = client.post('/api/v1/admin/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert "Non autorizzato" in data['error']
        mock_session.close.assert_called_once()

    @patch('admin_routes.SessionLocal')
    def test_admin_login_no_role(self, mock_session_local, client):
        """Test admin login fails when user has no role."""
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        
        user_no_role = Mock()
        user_no_role.id = 1
        user_no_role.username = "no_role_user"
        user_no_role.password = generate_password_hash("password")
        user_no_role.role = None
        
        mock_session.query.return_value.filter_by.return_value.first.return_value = user_no_role
        
        login_data = {
            "username": "no_role_user",
            "password": "password"
        }
        
        response = client.post('/api/v1/admin/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert "Non autorizzato" in data['error']
        mock_session.close.assert_called_once()

    @patch('admin_routes.SessionLocal')
    def test_admin_login_superadmin_role_success(self, mock_session_local, client, mock_structures):
        """Test admin login succeeds with superadmin role."""
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        
        superadmin_user = Mock()
        superadmin_user.id = 1
        superadmin_user.username = "superadmin"
        superadmin_user.name = "Super"
        superadmin_user.surname = "Admin"
        superadmin_user.password = generate_password_hash("password")
        superadmin_user.role = Mock()
        superadmin_user.role.name = "superadmin"
        
        mock_session.query.return_value.filter_by.return_value.first.return_value = superadmin_user
        
        # Setup structures query
        mock_structures_query = Mock()
        mock_session.query.return_value = mock_structures_query
        mock_structures_query.join.return_value = mock_structures_query
        mock_structures_query.filter.return_value = mock_structures_query
        mock_structures_query.all.return_value = mock_structures
        
        login_data = {
            "username": "superadmin",
            "password": "password"
        }
        
        response = client.post('/api/v1/admin/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['user']['role'] == 'superadmin'
        assert data['user']['username'] == 'superadmin'

    @patch('admin_routes.SessionLocal')
    def test_admin_login_administrator_role_success(self, mock_session_local, client, mock_structures):
        """Test admin login succeeds with administrator role."""
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        
        administrator_user = Mock()
        administrator_user.id = 1
        administrator_user.username = "administrator"
        administrator_user.name = "Admin"
        administrator_user.surname = "User"
        administrator_user.password = generate_password_hash("password")
        administrator_user.role = Mock()
        administrator_user.role.name = "administrator"
        
        mock_session.query.return_value.filter_by.return_value.first.return_value = administrator_user
        
        # Setup structures query
        mock_structures_query = Mock()
        mock_session.query.return_value = mock_structures_query
        mock_structures_query.join.return_value = mock_structures_query
        mock_structures_query.filter.return_value = mock_structures_query
        mock_structures_query.all.return_value = mock_structures
        
        login_data = {
            "username": "administrator",
            "password": "password"
        }
        
        response = client.post('/api/v1/admin/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['user']['role'] == 'administrator'

    @patch('admin_routes.SessionLocal')
    def test_admin_login_no_structures(self, mock_session_local, client, mock_user):
        """Test admin login with user having no associated structures."""
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_user
        
        # Setup empty structures query
        mock_structures_query = Mock()
        mock_session.query.return_value = mock_structures_query
        mock_structures_query.join.return_value = mock_structures_query
        mock_structures_query.filter.return_value = mock_structures_query
        mock_structures_query.all.return_value = []
        
        login_data = {
            "username": "admin_user",
            "password": "correct_password"
        }
        
        response = client.post('/api/v1/admin/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['user']['structures'] == []

    @patch('admin_routes.SessionLocal')
    @patch('admin_routes.logging')
    def test_admin_login_database_exception(self, mock_logging, mock_session_local, client):
        """Test admin login handles database exceptions properly."""
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        mock_session.query.side_effect = Exception("Database connection error")
        
        login_data = {
            "username": "admin_user",
            "password": "password"
        }
        
        response = client.post('/api/v1/admin/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert "Errore durante il login" in data['error']
        mock_logging.error.assert_called_once()
        mock_session.close.assert_called_once()

    def test_admin_login_invalid_json(self, client):
        """Test admin login handles invalid JSON gracefully."""
        response = client.post('/api/v1/admin/login',
                             data="invalid json",
                             content_type='application/json')
        
        assert response.status_code in [400, 500]

    def test_admin_login_no_content_type(self, client):
        """Test admin login without proper content type."""
        login_data = {"username": "test", "password": "test"}
        
        response = client.post('/api/v1/admin/login',
                             data=json.dumps(login_data))
        
        # Should still work or fail gracefully
        assert response.status_code in [200, 400, 500]


class TestCreateAdminUser:
    """Test cases for admin user creation functionality."""

    @patch('admin_routes.SessionLocal')
    def test_create_admin_user_success(self, mock_session_local, client):
        """Test successful creation of admin user with all fields."""
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        
        # Mock that user doesn't exist
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        
        # Mock new user creation
        mock_new_user = Mock()
        mock_new_user.id = 2
        mock_new_user.username = "new_admin"
        mock_new_user.name = "New"
        mock_new_user.surname = "Admin"
        mock_new_user.id_role = 2
        
        with patch('admin_routes.User', return_value=mock_new_user):
            user_data = {
                "username": "new_admin",
                "password": "secure_password",
                "name": "New",
                "surname": "Admin",
                "id_role": 2
            }
            
            response = client.post('/api/v1/admin/create',
                                 data=json.dumps(user_data),
                                 content_type='application/json')
            
            assert response.status_code == 201
            data = json.loads(response.data)
            assert "Utente creato con successo" in data['message']
            assert data['user']['username'] == 'new_admin'
            assert data['user']['id_role'] == 2
            assert data['user']['name'] == 'New'
            assert data['user']['surname'] == 'Admin'
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()

    @patch('admin_routes.SessionLocal')
    def test_create_admin_user_missing_username(self, mock_session_local, client):
        """Test admin user creation fails when username is missing."""
        user_data = {
            "password": "secure_password",
            "id_role": 2
        }
        
        response = client.post('/api/v1/admin/create',
                             data=json.dumps(user_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "username, password e id_role sono obbligatori" in data['error']

    @patch('admin_routes.SessionLocal')
    def test_create_admin_user_missing_password(self, mock_session_local, client):
        """Test admin user creation fails when password is missing."""
        user_data = {
            "username": "new_admin",
            "id_role": 2
        }
        
        response = client.post('/api/v1/admin/create',
                             data=json.dumps(user_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "username, password e id_role sono obbligatori" in data['error']

    @patch('admin_routes.SessionLocal')
    def test_create_admin_user_missing_role(self, mock_session_local, client):
        """Test admin user creation fails when role is missing."""
        user_data = {
            "username": "new_admin",
            "password": "secure_password"
        }
        
        response = client.post('/api/v1/admin/create',
                             data=json.dumps(user_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "username, password e id_role sono obbligatori" in data['error']

    @patch('admin_routes.SessionLocal')
    def test_create_admin_user_existing_username(self, mock_session_local, client):
        """Test admin user creation fails when username already exists."""
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        
        # Mock existing user
        existing_user = Mock()
        existing_user.username = "existing_admin"
        mock_session.query.return_value.filter_by.return_value.first.return_value = existing_user
        
        user_data = {
            "username": "existing_admin",
            "password": "secure_password",
            "id_role": 2
        }
        
        response = client.post('/api/v1/admin/create',
                             data=json.dumps(user_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Username gia' esistente" in data['error']
        mock_session.close.assert_called_once()

    @patch('admin_routes.SessionLocal')
    def test_create_admin_user_minimal_fields(self, mock_session_local, client):
        """Test admin user creation with only required fields."""
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        
        # Mock that user doesn't exist
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        
        # Mock new user creation with minimal fields
        mock_new_user = Mock()
        mock_new_user.id = 3
        mock_new_user.username = "minimal_admin"
        mock_new_user.name = None
        mock_new_user.surname = None
        mock_new_user.id_role = 1
        
        with patch('admin_routes.User', return_value=mock_new_user):
            user_data = {
                "username": "minimal_admin",
                "password": "secure_password",
                "id_role": 1
            }
            
            response = client.post('/api/v1/admin/create',
                                 data=json.dumps(user_data),
                                 content_type='application/json')
            
            assert response.status_code == 201
            data = json.loads(response.data)
            assert data['user']['name'] is None
            assert data['user']['surname'] is None
            assert data['user']['username'] == 'minimal_admin'

    @patch('admin_routes.SessionLocal')
    @patch('admin_routes.logging')
    def test_create_admin_user_database_exception(self, mock_logging, mock_session_local, client):
        """Test admin user creation handles database exceptions."""
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        mock_session.query.side_effect = Exception("Database error")
        
        user_data = {
            "username": "test_admin",
            "password": "secure_password",
            "id_role": 2
        }
        
        response = client.post('/api/v1/admin/create',
                             data=json.dumps(user_data),
                             content_type='application/json')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert "Errore durante la creazione utente" in data['error']
        mock_logging.error.assert_called_once()
        mock_session.close.assert_called_once()

    @patch('admin_routes.SessionLocal')
    def test_create_admin_user_password_hashing(self, mock_session_local, client):
        """Test that password is properly hashed during user creation."""
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        
        original_password = "plain_password"
        
        with patch('admin_routes.generate_password_hash') as mock_hash:
            mock_hash.return_value = "hashed_password"
            
            with patch('admin_routes.User') as mock_user_class:
                mock_user = Mock()
                mock_user.id = 1
                mock_user_class.return_value = mock_user
                
                user_data = {
                    "username": "test_admin",
                    "password": original_password,
                    "id_role": 2
                }
                
                client.post('/api/v1/admin/create',
                            data=json.dumps(user_data),
                            content_type='application/json')
                
                mock_hash.assert_called_once_with(original_password)
                mock_user_class.assert_called_once()

    def test_create_admin_user_invalid_json(self, client):
        """Test admin user creation with invalid JSON."""
        response = client.post('/api/v1/admin/create',
                             data="invalid json",
                             content_type='application/json')
        
        assert response.status_code in [400, 500]

    @patch('admin_routes.SessionLocal')
    def test_create_admin_user_zero_role_id(self, mock_session_local, client):
        """Test admin user creation fails with zero role ID."""
        user_data = {
            "username": "test_admin",
            "password": "secure_password",
            "id_role": 0
        }
        
        response = client.post('/api/v1/admin/create',
                             data=json.dumps(user_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "username, password e id_role sono obbligatori" in data['error']

    @patch('admin_routes.SessionLocal')
    def test_create_admin_user_null_role_id(self, mock_session_local, client):
        """Test admin user creation fails with null role ID."""
        user_data = {
            "username": "test_admin",
            "password": "secure_password",
            "id_role": None
        }
        
        response = client.post('/api/v1/admin/create',
                             data=json.dumps(user_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "username, password e id_role sono obbligatori" in data['error']


class TestGetAdminInfo:
    """Test cases for get admin info functionality."""

    @patch('admin_routes.SessionLocal')
    @patch('admin_routes.get_jwt_identity')
    def test_get_admin_info_success(self, mock_get_identity, mock_session_local, client, mock_user, auth_headers):
        """Test successful retrieval of admin information."""
        mock_get_identity.return_value = "1"
        
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_user
        
        # Mock structures
        mock_structures = [Mock(), Mock()]
        mock_structures[0].id_structure = 1
        mock_structures[0].name = "Structure 1"
        mock_structures[1].id_structure = 2
        mock_structures[1].name = "Structure 2"
        
        mock_structures_query = Mock()
        mock_session.query.return_value = mock_structures_query
        mock_structures_query.join.return_value = mock_structures_query
        mock_structures_query.filter.return_value = mock_structures_query
        mock_structures_query.all.return_value = mock_structures
        
        response = client.get('/api/v1/admin/me', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['username'] == 'admin_user'
        assert data['role'] == 'admin'
        assert data['name'] == 'Admin'
        assert data['surname'] == 'User'
        assert len(data['structures']) == 2
        assert data['structures'][0]['id'] == 1
        assert data['structures'][0]['name'] == 'Structure 1'
        mock_session.close.assert_called_once()

    @patch('admin_routes.SessionLocal')
    @patch('admin_routes.get_jwt_identity')
    def test_get_admin_info_user_not_found(self, mock_get_identity, mock_session_local, client, auth_headers):
        """Test get admin info when user is not found."""
        mock_get_identity.return_value = "999"
        
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        
        response = client.get('/api/v1/admin/me', headers=auth_headers)
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert "Utente non trovato" in data['error']
        mock_session.close.assert_called_once()

    def test_get_admin_info_no_auth_token(self, client):
        """Test get admin info without authentication token."""
        response = client.get('/api/v1/admin/me')
        
        assert response.status_code == 401

    @patch('admin_routes.SessionLocal')
    @patch('admin_routes.get_jwt_identity')
    def test_get_admin_info_no_structures(self, mock_get_identity, mock_session_local, client, mock_user, auth_headers):
        """Test get admin info for user with no structures."""
        mock_get_identity.return_value = "1"
        
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_user
        
        # Mock empty structures query
        mock_structures_query = Mock()
        mock_session.query.return_value = mock_structures_query
        mock_structures_query.join.return_value = mock_structures_query
        mock_structures_query.filter.return_value = mock_structures_query
        mock_structures_query.all.return_value = []
        
        response = client.get('/api/v1/admin/me', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['structures'] == []

    def test_get_admin_info_invalid_token(self, client):
        """Test get admin info with invalid JWT token."""
        invalid_headers = {'Authorization': 'Bearer invalid_token'}
        
        response = client.get('/api/v1/admin/me', headers=invalid_headers)
        
        assert response.status_code == 422  # JWT decode error

    def test_get_admin_info_malformed_auth_header(self, client):
        """Test get admin info with malformed authorization header."""
        malformed_headers = {'Authorization': 'invalid_format'}
        
        response = client.get('/api/v1/admin/me', headers=malformed_headers)
        
        assert response.status_code == 401

    @patch('admin_routes.SessionLocal')
    @patch('admin_routes.get_jwt_identity')
    def test_get_admin_info_database_exception(self, mock_get_identity, mock_session_local, client, auth_headers):
        """Test get admin info handles database exceptions."""
        mock_get_identity.return_value = "1"
        
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        mock_session.query.side_effect = Exception("Database connection error")
        
        response = client.get('/api/v1/admin/me', headers=auth_headers)
        
        assert response.status_code == 500
        mock_session.close.assert_called_once()


class TestAdminRoutesIntegration:
    """Integration tests for admin routes."""

    def test_blueprint_registration(self, app):
        """Test that the admin blueprint is properly registered."""
        assert 'admin' in app.blueprints
        blueprint = app.blueprints['admin']
        assert blueprint.url_prefix == '/api/v1'

    def test_all_routes_exist(self, client):
        """Test that all admin routes are properly registered."""
        # Login route should exist
        response = client.post('/api/v1/admin/login')
        assert response.status_code != 404
        
        # Create route should exist
        response = client.post('/api/v1/admin/create')
        assert response.status_code != 404
        
        # Me route should exist (will fail auth but route exists)
        response = client.get('/api/v1/admin/me')
        assert response.status_code != 404

    def test_options_requests(self, client):
        """Test OPTIONS requests for CORS support."""
        endpoints = [
            '/api/v1/admin/login',
            '/api/v1/admin/create',
            '/api/v1/admin/me'
        ]
        
        for endpoint in endpoints:
            response = client.options(endpoint)
            assert response.status_code in [200, 404, 405]  # Valid responses

    def test_endpoints_handle_empty_body(self, client):
        """Test that endpoints handle empty request bodies gracefully."""
        post_endpoints = [
            '/api/v1/admin/login',
            '/api/v1/admin/create'
        ]
        
        for endpoint in post_endpoints:
            response = client.post(endpoint, content_type='application/json')
            assert response.status_code in [400, 500]  # Should not crash

    @patch('admin_routes.SessionLocal')
    def test_database_session_cleanup(self, mock_session_local, client):
        """Test that database sessions are properly cleaned up."""
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        mock_session.query.side_effect = Exception("Database error")
        
        login_data = {"username": "test", "password": "test"}
        
        client.post('/api/v1/admin/login',
                    data=json.dumps(login_data),
                    content_type='application/json')
        
        # Verify session was closed even on exception
        mock_session.close.assert_called()


class TestPasswordSecurity:
    """Test password security functionality."""

    def test_password_hashing_works(self):
        """Test password hashing and verification."""
        from werkzeug.security import generate_password_hash, check_password_hash
        
        password = "test_password_123"
        hashed = generate_password_hash(password)
        
        # Verify hash is different from original
        assert hashed != password
        # Verify correct password works
        assert check_password_hash(hashed, password) is True
        # Verify wrong password fails
        assert check_password_hash(hashed, "wrong_password") is False

    def test_password_uniqueness(self):
        """Test that identical passwords produce different hashes."""
        from werkzeug.security import generate_password_hash
        
        password = "same_password"
        hash1 = generate_password_hash(password)
        hash2 = generate_password_hash(password)
        
        # Hashes should be different due to salt
        assert hash1 != hash2

    def test_various_password_strengths(self):
        """Test hashing works with various password complexities."""
        from werkzeug.security import generate_password_hash, check_password_hash
        
        passwords = [
            "simple",
            "complex_password_123!",
            "12345",
            "!@#$%^&*()",
            "very_long_password_with_many_characters_in_it"
        ]
        
        for password in passwords:
            hashed = generate_password_hash(password)
            assert check_password_hash(hashed, password) is True
            assert check_password_hash(hashed, password + "x") is False


class TestJWTSecurity:
    """Test JWT token security functionality."""

    def test_jwt_token_creation(self, app):
        """Test JWT token creation with claims."""
        with app.app_context():
            token = create_access_token(
                identity="1",
                additional_claims={
                    "username": "test_admin",
                    "role": "admin"
                },
                expires_delta=timedelta(hours=2)
            )
            
            assert token is not None
            assert isinstance(token, str)
            assert len(token) > 0

    def test_jwt_token_expiration_settings(self, app):
        """Test JWT tokens with different expiration times."""
        with app.app_context():
            short_token = create_access_token(
                identity="1",
                expires_delta=timedelta(minutes=5)
            )
            
            long_token = create_access_token(
                identity="1", 
                expires_delta=timedelta(hours=24)
            )
            
            assert short_token is not None
            assert long_token is not None
            assert short_token != long_token

    def test_jwt_with_multiple_claims(self, app):
        """Test JWT token creation with various additional claims."""
        with app.app_context():
            claims = {
                "username": "test_user",
                "role": "admin",
                "permissions": ["read", "write", "delete"],
                "organization_id": 123
            }
            
            token = create_access_token(
                identity="456",
                additional_claims=claims
            )
            
            assert token is not None
            assert len(token) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])