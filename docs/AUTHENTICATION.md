# Documentation Technique : Authentification avec Knox

## Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture](#architecture)
3. [Configuration](#configuration)
4. [Endpoints API](#endpoints-api)
5. [Utilisation](#utilisation)
6. [Sécurité](#sécurité)
7. [Gestion des tokens](#gestion-des-tokens)
8. [Dépannage](#dépannage)

---

## Vue d'ensemble

Le projet GardenIQ utilise **django-rest-knox** pour l'authentification basée sur des tokens. Knox fournit une approche sécurisée pour l'authentification des API REST en générant des tokens uniques et cryptographiquement sécurisés.

### Pourquoi Knox ?

- **Sécurité renforcée** : Les tokens sont hashés avec SHA-512 avant d'être stockés en base de données
- **Gestion avancée** : Support de plusieurs tokens par utilisateur
- **Expiration flexible** : Configuration des durées de vie des tokens
- **Contrôle** : Révocation individuelle ou collective des tokens

---

## Architecture

### Composants principaux

```
┌─────────────────┐
│   Client Web    │
│   ou Mobile     │
└────────┬────────┘
         │ 1. POST /api/auth/login/
         │    {username, password}
         ▼
┌─────────────────────────────┐
│   LoginView (Knox)          │
│   - Validation credentials  │
│   - Génération token        │
└────────┬────────────────────┘
         │ 2. Token + User data
         ▼
┌─────────────────┐
│     Client      │
│  (Stocke token) │
└────────┬────────┘
         │ 3. GET /api/auth/me/
         │    Authorization: Token <token>
         ▼
┌─────────────────────────────┐
│  TokenAuthentication        │
│  - Vérifie token            │
│  - Charge utilisateur       │
└────────┬────────────────────┘
         │ 4. User data
         ▼
┌─────────────────┐
│     Client      │
└─────────────────┘
```

### Classes principales

1. **LoginView** (`gardeniq/users/views/auth.py`)
   - Hérite de `KnoxLoginView`
   - Gère l'authentification et la génération de tokens
   - Applique le throttling (5 requêtes/minute)

2. **UserAuthViewSet** (`gardeniq/users/views/auth.py`)
   - Endpoint `/me/` pour récupérer les informations de l'utilisateur authentifié
   - Utilise `UserDetailReadOnlySerializer`

3. **TokenAuthentication** (Knox)
   - Middleware d'authentification automatique
   - Validé sur chaque requête protégée

---

## Configuration

### Configuration Knox (`gardeniq/settings/third_party/knox.py`)

```python
REST_KNOX = {
    # Algorithme de hachage pour les tokens
    "SECURE_HASH_ALGORITHM": "hashlib.sha512",
    
    # Longueur du token (64 caractères)
    "AUTH_TOKEN_CHARACTER_LENGTH": 64,
    
    # Durée de vie du token (7 jours)
    "TOKEN_TTL": timedelta(days=7),
    
    # Serializer pour retourner les données utilisateur
    "USER_SERIALIZER": "gardeniq.users.serializers.UserDetailReadOnlySerializer",
    
    # Limite de tokens par utilisateur (5 maximum)
    "TOKEN_LIMIT_PER_USER": 5,
    
    # Désactive le rafraîchissement automatique
    "AUTO_REFRESH": False,
    
    # Intervalle minimum avant rafraîchissement (60 secondes)
    "MIN_REFRESH_INTERVAL": 60,
    
    # Format de date d'expiration
    "EXPIRY_DATETIME_FORMAT": "%Y-%m-%dT%H:%M:%S.%fZ",
}
```

### Configuration Django REST Framework (`gardeniq/settings/third_party/rest_framework.py`)

```python
REST_FRAMEWORK = {
    # Knox comme authentification par défaut
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "knox.auth.TokenAuthentication",
    ],
    
    # Toutes les vues nécessitent l'authentification par défaut
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    
    # Throttling
    "DEFAULT_THROTTLE_RATES": {
        "anon": "20/hour",      # Utilisateurs anonymes
        "user": "200/hour",     # Utilisateurs authentifiés
        "login": "10/hour",     # Login spécifique
    },
}
```

### Throttling personnalisé

```python
class LoginThrottle(AnonRateThrottle):
    rate = "5/min"  # Maximum 5 tentatives de connexion par minute
```

---

## Endpoints API

### 1. Login - POST `/api/auth/login/`

Authentifie un utilisateur et génère un token.

**Requête :**
```http
POST /api/auth/login/
Content-Type: application/json

{
    "username": "john_doe",
    "password": "SecurePassword123!"
}
```

**Réponse (200 OK) :**
```json
{
    "expiry": "2026-01-22T12:34:56.789123Z",
    "token": "a1b2c3d4e5f6...64caractères",
    "user": {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "is_active": true,
        "is_staff": false,
        "last_login": "2026-01-15T10:00:00.000000Z",
        "date_joined": "2025-12-01T08:00:00.000000Z",
        "groups": [
            {
                "id": 1,
                "name": "gardeners",
                "permissions": [...]
            }
        ],
        "user_permissions": []
    }
}
```

**Erreurs possibles :**
- `400 Bad Request` : Identifiants incorrects
- `429 Too Many Requests` : Throttling dépassé (5 tentatives/minute)

---

### 2. Logout - POST `/api/auth/logout/`

Révoque le token actuel de l'utilisateur.

**Requête :**
```http
POST /api/auth/logout/
Authorization: Token a1b2c3d4e5f6...64caractères
```

**Réponse (204 No Content) :**
```
(Pas de contenu)
```

---

### 3. Logout All - POST `/api/auth/logoutall/`

Révoque tous les tokens de l'utilisateur.

**Requête :**
```http
POST /api/auth/logoutall/
Authorization: Token a1b2c3d4e5f6...64caractères
```

**Réponse (204 No Content) :**
```
(Pas de contenu)
```

---

### 4. User Info (Me) - GET `/api/auth/me/`

Récupère les informations de l'utilisateur authentifié.

**Requête :**
```http
GET /api/auth/me/
Authorization: Token a1b2c3d4e5f6...64caractères
```

**Réponse (200 OK) :**
```json
{
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_active": true,
    "is_staff": false,
    "last_login": "2026-01-15T10:00:00.000000Z",
    "date_joined": "2025-12-01T08:00:00.000000Z",
    "groups": [...],
    "user_permissions": [...]
}
```

**Erreurs possibles :**
- `401 Unauthorized` : Token invalide ou expiré

---

## Utilisation

### Frontend : JavaScript / Fetch

#### 1. Connexion

```javascript
async function login(username, password) {
    try {
        const response = await fetch('/api/auth/login/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
        });

        if (!response.ok) {
            throw new Error('Échec de connexion');
        }

        const data = await response.json();
        
        // Stocker le token (localStorage, sessionStorage, ou cookie sécurisé)
        localStorage.setItem('authToken', data.token);
        localStorage.setItem('tokenExpiry', data.expiry);
        
        return data;
    } catch (error) {
        console.error('Erreur de connexion:', error);
        throw error;
    }
}
```

#### 2. Requête authentifiée

```javascript
async function fetchUserInfo() {
    const token = localStorage.getItem('authToken');
    
    if (!token) {
        throw new Error('Non authentifié');
    }

    try {
        const response = await fetch('/api/auth/me/', {
            method: 'GET',
            headers: {
                'Authorization': `Token ${token}`,
                'Content-Type': 'application/json',
            },
        });

        if (!response.ok) {
            if (response.status === 401) {
                // Token invalide, rediriger vers login
                localStorage.removeItem('authToken');
                window.location.href = '/login';
            }
            throw new Error('Erreur lors de la récupération');
        }

        return await response.json();
    } catch (error) {
        console.error('Erreur:', error);
        throw error;
    }
}
```

#### 3. Déconnexion

```javascript
async function logout() {
    const token = localStorage.getItem('authToken');
    
    try {
        await fetch('/api/auth/logout/', {
            method: 'POST',
            headers: {
                'Authorization': `Token ${token}`,
            },
        });
    } finally {
        // Nettoyer le stockage local
        localStorage.removeItem('authToken');
        localStorage.removeItem('tokenExpiry');
        window.location.href = '/login';
    }
}
```

### Backend : Python / Requests

```python
import requests

BASE_URL = "http://localhost:8000"

class APIClient:
    def __init__(self):
        self.token = None
        self.session = requests.Session()
    
    def login(self, username, password):
        """Connexion et récupération du token."""
        response = self.session.post(
            f"{BASE_URL}/api/auth/login/",
            json={"username": username, "password": password}
        )
        response.raise_for_status()
        
        data = response.json()
        self.token = data["token"]
        
        # Configurer le header pour les prochaines requêtes
        self.session.headers.update({
            "Authorization": f"Token {self.token}"
        })
        
        return data
    
    def get_user_info(self):
        """Récupérer les informations utilisateur."""
        response = self.session.get(f"{BASE_URL}/api/auth/me/")
        response.raise_for_status()
        return response.json()
    
    def logout(self):
        """Déconnexion."""
        if self.token:
            self.session.post(f"{BASE_URL}/api/auth/logout/")
            self.token = None
            self.session.headers.pop("Authorization", None)

# Utilisation
client = APIClient()
client.login("john_doe", "SecurePassword123!")
user_info = client.get_user_info()
print(f"Connecté en tant que : {user_info['username']}")
client.logout()
```

---

## Sécurité

### Bonnes pratiques implémentées

1. **Hachage sécurisé (SHA-512)**
   - Les tokens ne sont jamais stockés en clair dans la base de données
   - Impossible de récupérer un token original à partir du hash

2. **Throttling**
   - Login : 5 tentatives/minute (protection contre le brute force)
   - Utilisateurs anonymes : 20 requêtes/heure
   - Utilisateurs authentifiés : 200 requêtes/heure

3. **Limite de tokens**
   - Maximum 5 tokens actifs par utilisateur
   - Empêche l'accumulation excessive de tokens

4. **Expiration des tokens**
   - Durée de vie : 7 jours
   - Force la ré-authentification régulière

5. **HTTPS recommandé**
   - Les tokens doivent toujours être transmis via HTTPS en production
   - Évite l'interception par man-in-the-middle

### Recommandations supplémentaires

1. **Stockage côté client**
   ```javascript
   // ✅ BON : Cookie HttpOnly (le plus sécurisé)
   // Nécessite configuration backend spécifique
   
   // ⚠️ ACCEPTABLE : sessionStorage
   sessionStorage.setItem('authToken', token);
   
   // ❌ ÉVITER : localStorage (XSS vulnerable)
   // Utiliser uniquement si pas d'alternative
   ```

2. **Vérification d'expiration côté client**
   ```javascript
   function isTokenExpired() {
       const expiry = localStorage.getItem('tokenExpiry');
       if (!expiry) return true;
       
       return new Date(expiry) < new Date();
   }
   ```

3. **Rotation des tokens**
   - Déconnecter et reconnecter périodiquement
   - Utiliser `logoutall` en cas de compromission suspectée

4. **Monitoring**
   - Surveiller les tentatives de connexion échouées
   - Alertes sur les dépassements de throttling

---

## Gestion des tokens

### Cycle de vie d'un token

```
┌──────────────┐
│  Création    │  POST /api/auth/login/
│  Token       │  → Token généré (64 chars)
└──────┬───────┘  → Hash SHA-512 stocké en DB
       │          → Expiration : +7 jours
       ▼
┌──────────────┐
│  Utilisation │  Headers: Authorization: Token <token>
│  Active      │  → Validation à chaque requête
└──────┬───────┘  → Vérification expiration
       │          → Charge utilisateur
       ▼
┌──────────────┐
│  Révocation  │  POST /api/auth/logout/
│  ou          │  → Suppression immédiate
│  Expiration  │  ou après 7 jours
└──────────────┘
```

### Gestion multi-appareils

Knox permet à un utilisateur d'avoir plusieurs tokens actifs simultanément (limite : 5).

**Scénario typique :**
- Token 1 : Application web (Chrome)
- Token 2 : Application web (Firefox)
- Token 3 : Application mobile (Android)
- Token 4 : Application mobile (iOS)
- Token 5 : API externe

**Déconnexion sélective :**
```javascript
// Déconnecter uniquement l'appareil actuel
await fetch('/api/auth/logout/', {
    method: 'POST',
    headers: { 'Authorization': `Token ${currentToken}` }
});
// Les autres appareils restent connectés
```

**Déconnexion globale :**
```javascript
// Déconnecter tous les appareils
await fetch('/api/auth/logoutall/', {
    method: 'POST',
    headers: { 'Authorization': `Token ${currentToken}` }
});
// Tous les tokens sont révoqués
```

### Modèle de base de données

Les tokens sont stockés dans la table `knox_authtoken` :

```sql
CREATE TABLE knox_authtoken (
    digest VARCHAR(128) PRIMARY KEY,      -- Hash SHA-512 du token
    salt VARCHAR(16),                     -- Salt pour le hachage
    user_id INTEGER,                      -- Référence à l'utilisateur
    created TIMESTAMP,                    -- Date de création
    expiry TIMESTAMP                      -- Date d'expiration
);
```

---

## Dépannage

### Problème : "Invalid token" (401)

**Causes possibles :**
1. Token expiré (> 7 jours)
2. Token révoqué (logout)
3. Format du header incorrect
4. Token corrompu

**Solutions :**
```javascript
// Vérifier le format du header
// ✅ CORRECT
headers: { 'Authorization': 'Token abc123...' }

// ❌ INCORRECT
headers: { 'Authorization': 'Bearer abc123...' }  // Pas Bearer !
headers: { 'Token': 'abc123...' }                // Pas Token: !
```

### Problème : "Too many requests" (429)

**Cause :** Dépassement du throttling

**Solution :**
```python
# Augmenter les limites si nécessaire (dev uniquement)
# gardeniq/settings/third_party/rest_framework.py
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",  # Augmenter temporairement
    },
}
```

### Problème : Token non révoqué après logout

**Cause :** Cache ou problème de synchronisation

**Solution :**
```python
# Forcer la déconnexion de tous les tokens
POST /api/auth/logoutall/
```

### Problème : "User inactive" lors du login

**Cause :** Compte utilisateur désactivé (`is_active=False`)

**Solution :**
```python
# Activer l'utilisateur (Django shell ou admin)
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.get(username='john_doe')
user.is_active = True
user.save()
```

### Debug mode

Pour déboguer l'authentification :

```python
# Dans settings/dev.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'knox': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

---

## Tests

### Tester l'authentification avec curl

```bash
# 1. Login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Réponse : {"token": "abc123...", "expiry": "...", "user": {...}}

# 2. Utiliser le token
TOKEN="abc123..."
curl -X GET http://localhost:8000/api/auth/me/ \
  -H "Authorization: Token $TOKEN"

# 3. Logout
curl -X POST http://localhost:8000/api/auth/logout/ \
  -H "Authorization: Token $TOKEN"
```

### Tests unitaires

Les tests se trouvent dans `gardeniq/users/tests/tests_views/test_auth.py`

```bash
# Exécuter les tests d'authentification
python manage.py test gardeniq.users.tests.tests_views.test_auth
```

---

## Références

- [Documentation django-rest-knox](https://james1345.github.io/django-rest-knox/)
- [Django REST Framework Authentication](https://www.django-rest-framework.org/api-guide/authentication/)
- [Knox GitHub Repository](https://github.com/James1345/django-rest-knox)

---

**Dernière mise à jour :** 15 janvier 2026  
**Version :** 1.0  
**Auteur :** Équipe GardenIQ
