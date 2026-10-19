---
paths:
  - "gardeniq/**/tests/**"
  - "gardeniq/base/utils/tests.py"
---

# Tests

- pytest, pytest-django, pytest-xdist, pytest-mock. Les settings viennent du `.env` (`gardeniq.settings.dev`) : il n'y a ni settings de test, ni timeout, ni marker `slow`. Fichiers dans `gardeniq/<app>/tests/` : `tests_models/`, `tests_serializers/`, `tests_views/`, `tests_protocols/`, ou `test_<sujet>.py` à la racine de `tests/`. Un fichier de test porte le nom de l'objet testé (`test_device.py`).
- Structure d'un test : une docstring d'une ligne, puis les commentaires `# GIVEN`, `# WHEN`, `# THEN`. Classes de test groupées par objet (`TestStatusAPIModelView`, `TestPinSerializer`), sur le modèle de `gardeniq/base/tests/tests_views/test_status.py`.
- Accès base de données : `@pytest.mark.django_db` sur la classe, ou la fixture `db` pour les fonctions et les fixtures de module (voir `hardware/tests/tests_models/test_pin.py`).
- Tests de vues : hériter de `ViewSetTestMixin` (`gardeniq/base/utils/tests.py`, importable aussi depuis `gardeniq.base.utils`) via une classe `<Objet>ViewSetTestConf` qui définit `MODEL`, `BASE_PATTERN` (nom de route, ex. `"status"`) et `DATA_TO_DEFAULT_OBJ` ; la classe `Test<Objet>APIModelView` hérite de cette conf. Utiliser ses `get_url_list`, `get_url_create` et `get_url_detail`, la fixture `obj` (objet créé depuis `DATA_TO_DEFAULT_OBJ`) et les clients ci-dessous. Ne pas utiliser `get_url_enable` / `get_url_disable` pour l'instant : `get_url_disable` est cassé et ces routes renvoient 405 (voir `docs/backlog.md`).
- Clients d'API fournis par `ViewSetTestMixin` (il n'y a pas de `conftest.py`) : `authenticated_client` (utilisateur standard), `admin_client` (staff et superuser), `unauthenticated_client` et `client_anonymous` (sans authentification), `api_client` (client brut). Les réutiliser avant d'en créer. Fixtures d'utilisateurs, groupes et permissions : `regular_user`, `admin_user`, `regular_user_with_groups`, `test_group`, `test_permission`.
- Les données de test viennent de `DATA_TO_DEFAULT_OBJ`, de fixtures `@pytest.fixture` définies dans le fichier de test et de `Model.objects.create(...)`. Il n'y a pas de factories : ne pas en introduire sans décision.
- Les mocks passent par `pytest-mock` (`mocker.patch(...)`) et `monkeypatch` pour l'environnement : aucun test du dépôt n'importe `unittest.mock`. Jamais de réseau ni de port série réels.
- Dans les tests, importer une autre app est autorisé (seule exception au sens des imports entre apps), par exemple `orderlg` qui importe les modèles de `hardware`.
- Lancer un fichier ou un test : `pytest -- gardeniq/<app>/tests/<dossier>/<fichier>.py::<Classe>::<test>`. Pour aller vite : `-n auto --reuse-db`.
