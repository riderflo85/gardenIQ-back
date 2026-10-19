---
name: write-test
description: Écrit des tests pytest / DRF pour GardenIQ en respectant les conventions du dépôt (GIVEN/WHEN/THEN, classes par objet, ViewSetTestMixin et ses clients d'API, fixtures de fichier, mocker), les exécute et rend compte de ce qui est couvert ou non. Utiliser quand l'utilisateur demande "écris les tests de X", "ajoute des tests", "teste ce modèle / cette vue / ce serializer / cette commande", "write-test", "couvre ce changement par des tests" ou "reproduis ce bug par un test".
---

# write-test

Écrit des tests qui ressemblent à ceux du dépôt : même structure, mêmes fixtures, mêmes clients d'API. Les conventions de base sont dans `.claude/rules/tests.md` (et `api.md`, `migrations.md`) : les **lire** avant d'écrire, ne pas les recopier ici ni les contourner.

Ce skill écrit des tests ; il **ne modifie pas le code testé**. Si un test révèle un bug, le rapporter (voir « Restituer »).

## Procédé

### 0. Cibler ce qu'on teste

Dans l'ordre :
- l'objet ou le comportement nommé par l'utilisateur (« la vue des devices », « la comparaison de versions ») ;
- sinon le changement de la branche : `git diff $(git merge-base origin/main HEAD)...HEAD`, en ne gardant que le code qui porte du comportement (pas les migrations ni la config).

Lire le code testé **en entier**, pas seulement les hunks : branches, cas d'erreur, permissions, effets de bord (écriture en base, appel externe, log).

### 1. Lire l'existant avant d'écrire

- Les tests voisins de l'objet : `gardeniq/<app>/tests/` (`tests_models/`, `tests_serializers/`, `tests_views/`, `tests_protocols/`, `test_<sujet>.py`). **Ne pas dupliquer** un test qui existe déjà : l'étendre ou le compléter.
- Pour une vue : `ViewSetTestMixin` (`gardeniq/base/utils/tests.py`) et un exemple complet, `gardeniq/base/tests/tests_views/test_status.py` (`StatusViewSetTestConf` puis `TestStatusAPIModelView`).
- Autres modèles à suivre : un modèle avec fixtures de module (`hardware/tests/tests_models/test_pin.py`), un serializer (`hardware/tests/tests_serializers/test_pin.py`), des permissions 401 et 403 (`users/tests/tests_views/test_users.py`), un seeder (`orderlg/tests/test_seeders.py`), du code qui appelle l'extérieur (`base/tests/test_versions.py`, avec `mocker`).
- Les clients et fixtures déjà fournis par `ViewSetTestMixin` : `authenticated_client`, `admin_client`, `unauthenticated_client`, `client_anonymous`, `api_client`, `regular_user`, `admin_user`, `obj`… les réutiliser avant d'en créer. Il n'y a ni `conftest.py` ni factories.

### 2. Choisir quoi couvrir

Un test par comportement observable, pas par ligne de code. Selon la cible :

- **Modèle** : `save`, `delete`, contraintes, méthodes métier, valeurs par défaut. Erreurs attendues avec `pytest.raises` (par exemple `ProtectedError` de Django pour une clé étrangère protégée, `IntegrityError` pour une contrainte). Ne pas écrire de test qui suppose que `ProtectedDeletedMixinModel` ou `ProtectedDisabledMixinModel` protège réellement : `get_protected_relations()` n'est pas implémentée (voir `docs/backlog.md`).
- **Serializer** : validation (champs requis, valeurs refusées), effet de `save()`. Un serializer de lecture hérite de `ReadOnlySerializer` : ses champs sont en lecture seule et `save`, `create` et `update` lèvent `NotImplementedError`.
- **Vue** (`ViewSetTestMixin`) : liste (la réponse est paginée : `response.data["results"]` et `response.data["count"]`), création (201), détail, mise à jour (PUT), suppression, actions personnalisées. Codes attendus : `unauthenticated_client` → **401** ; un utilisateur non administrateur sur une action réservée aux administrateurs → **403** ; PATCH → **405** (la vue n'expose que GET, POST, PUT, DELETE) ; données invalides → **400** ; objet inexistant → **404**. Ne pas utiliser `get_url_enable` / `get_url_disable` : `get_url_disable` est cassé et les routes `enable/` et `disable/` renvoient 405 (voir `docs/backlog.md`).
- **Requêtes** : les vues optimisent leurs requêtes par action (`select_related`). Sur une liste ou un détail, un test avec la fixture `django_assert_max_num_queries` (pytest-django, pas encore utilisée dans le dépôt) protège contre un N+1.
- **Seeders et commandes de management** : un seeder se teste comme `orderlg/tests/test_seeders.py`. Pour une commande, `call_command("<nom>", stdout=out)` ; les tests de commandes existants sont désactivés (voir `docs/backlog.md`).
- **Protocole USB et matériel** : trames et parseur dans `hardware/tests/tests_protocols/`. Jamais de port série réel : simuler avec `mocker`.
- **Appels externes** (HTTP, GitHub, port série) : jamais réels, `mocker.patch("<module>.<fonction>")`, comme `config_value_mock` et `request_version_mock` dans `base/tests/test_versions.py`. `monkeypatch` pour les variables d'environnement. Ni `requests_mock` ni `freezegun` ne sont installés.

Cas limites à chercher dans le code lu à l'étape 0 : liste vide, valeur absente ou `None`, doublon, objet désactivé (`is_enabled`), relation manquante, accès d'un autre utilisateur.

### 3. Écrire

Conventions (détail dans `tests.md`) :
- fichier à l'emplacement de l'étape 1, dans un fichier existant s'il y en a un pour l'objet ;
- une docstring d'une ligne, puis **`# GIVEN` / `# WHEN` / `# THEN`** dans chaque test ;
- classes groupées par objet (`Test<Objet>APIModelView`, `Test<Objet>Serializer`), `@pytest.mark.django_db` sur la classe, ou la fixture `db` pour des fonctions et des fixtures de module ;
- vues : une classe `<Objet>ViewSetTestConf(ViewSetTestMixin)` avec `MODEL`, `BASE_PATTERN` et `DATA_TO_DEFAULT_OBJ`, puis la classe `Test<Objet>APIModelView(<Objet>ViewSetTestConf)` qui utilise `authenticated_client`, `obj`, `get_url_list()` et `get_url_detail(obj)` ;
- données par `DATA_TO_DEFAULT_OBJ`, par des fixtures `@pytest.fixture` du fichier et par `Model.objects.create(...)` ; ne pas écrire de `pk` en dur, ne pas dépendre de l'ordre d'exécution (les tests peuvent tourner en parallèle avec `pytest-xdist`) ;
- `assert response.status_code == status.HTTP_201_CREATED, response.content` donne le message utile en cas d'échec ;
- imports en une ligne par nom (`from x import A` / `from x import B`), comme dans tout le dépôt : isort et flake8 tranchent ;
- il n'y a ni timeout par test ni marker `slow` : un test lent est un problème à signaler, pas à masquer.

Ne pas modifier `ViewSetTestMixin` sans demander : l'impact dépasse le test en cours. Les tests sont dispensés de typage (voir « Typage » dans `CLAUDE.md`).

### 4. Exécuter

```bash
pytest -- gardeniq/<app>/tests/<dossier>/<fichier>.py::<Classe>::<test>
```

La base est du SQLite local : aucune infrastructure à démarrer. Pour tout un fichier ou une app, `pytest -n auto --reuse-db -- gardeniq/<app>/tests`. Si une migration a été ajoutée ou modifiée, `--create-db` à la place de `--reuse-db`.

- **Nouvelle fonctionnalité** : les tests doivent passer.
- **Reproduction d'un bug** : le test doit **échouer avant le correctif**, pour la bonne raison (l'assertion qui décrit le bug, pas une erreur d'import ou de fixture). Le montrer, puis laisser l'utilisateur valider la cause et le correctif : on ne corrige pas dans ce skill (règle de `CLAUDE.md` : cause racine proposée avant de modifier le code).
- Un test qui passe du premier coup sans avoir vu échouer ce qu'il protège ne prouve rien : pour un comportement critique, vérifier qu'il échoue quand on casse volontairement le code (sur une copie ou en annulant ensuite, jamais en laissant la casse).

Ensuite, le lint comme la CI :

```bash
black --check gardeniq
isort --check-only --diff .
flake8 .
```

flake8 signale les imports inutilisés ; `black gardeniq` et `isort .` corrigent le reste, sur les fichiers de test écrits seulement.

### 5. Restituer

Dans le chat, en français :
- fichiers de tests créés ou modifiés ;
- **ce qui est couvert** (liste de comportements, pas de pourcentage) et **ce qui ne l'est pas** (et pourquoi : dépend du matériel ou d'un service externe, hors périmètre, bug connu du backlog) ;
- résultat réel de l'exécution : commande lancée, nombre de tests passés ou échoués. **Ne jamais affirmer qu'un test passe sans l'avoir lancé.**
- bugs ou comportements surprenants découverts en écrivant les tests : les noter dans `docs/backlog.md` plutôt que de les corriger, après avoir cherché un doublon.

Ne pas commiter : les tests se commitent avec le skill `commit`, dans le même changement que le code qu'ils couvrent ou dans un commit distinct (`test` si la branche est de type `test`).

## À éviter

- Modifier le code testé pour faire passer un test.
- Des tests qui répètent l'implémentation (mêmes calculs que le code) au lieu de vérifier le résultat.
- Assertions sur des détails internes (ordre des appels, noms de variables) plutôt que sur le comportement observable.
- Introduire une bibliothèque de factories ou un `conftest.py` sans décision de l'équipe.
- Appels réseau ou port série réels, dépendance à l'heure courante sans la contrôler.
- Tests dépendants les uns des autres ou de l'ordre d'exécution.
- Valeurs réelles (adresses, jetons, identifiants d'appareil) dans les fixtures ou les attendus.
- Annoncer « tests OK » sans les avoir exécutés.
