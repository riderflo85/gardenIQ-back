# GardenIQ back

Backend de GardenIQ : Django + Django REST Framework, Python 3.13.5, SQLite.

## Commandes

Tout passe par un environnement de dev pipenv: `pipenv shell`. Les commandes django passent par le script `manage.py`. La configuration vient du fichier `.env` (ignoré par git, à copier depuis `.env.example`, chargé automatiquement par pipenv).

| Besoin | Commande |
|---|---|
| Lint (écrit les corrections) | `black gardeniq` `isort .` `flake8 .` (`black` seul échoue : il faut un chemin) |
| Lint comme la CI (sans écrire) | `black --check gardeniq` `isort --check-only --diff .` `flake8 .` |
| Tous les hooks pre-commit | `pre-commit run --all-files` |
| Tests | `pytest [options pytest]` (544 tests, ~2 min) |
| Tests plus rapides | réutilise la base de test, `--reuse-db`, `-x` (stoppe au premier échec), parallélisation des tests avec `-n auto` (utilise pytest-xdist, ~35 s) |
| Un test précis | `pytest [options pytest] -- gardeniq/<app>/tests/<dossier>/<fichier>.py::<test>` |
| Couverture (comme la CI) | `pytest --cov=. --cov-report=term-missing` |
| Serveur, shell | `pipenv run server`, `pipenv run shell` (`shell_plus`) |
| Fixtures (seeders) | `./manage.py seed [--app <app>] [--update]` |
| Matériel USB | `./manage.py list_devices [--verbose]`, `check_connection <port> <baud>`, `cmd <port> <baud>` |
| Mettre à jour les dépendances | `pipenv run update_dep` (régénère `Pipfile.lock`, `requirements.txt` et `requirements_dev.txt`, utilisés par la CI) |
| Docker (dev, hot-reload) | `docker compose up web-dev` |

Tests : pytest, pytest-django, pytest-xdist, pytest-mock. Les settings viennent du `.env` (`gardeniq.settings.dev`) : il n'y a ni settings de test, ni `pytest.ini`, ni timeout, ni marker `slow`. Les fichiers sont dans `gardeniq/<app>/tests/` (`tests_models/`, `tests_serializers/`, `tests_views/`, ou `test_<sujet>.py`).

## Règles d'architecture

Les règles à ne jamais enfreindre :

- Sens des imports entre apps : `base` n'importe **aucune** autre app ; `hardware` et `users` n'importent que `base` ; `orderlg` importe `base` et `hardware`. Jamais de cycle (exception : les tests).
- Un module n'importe pas son module parent (`ban-relative-imports = parents`), seulement ses frères (`from .device import Device`) ; tout le reste en absolu `gardeniq.<app>...`. Un import par ligne (isort `force_single_line`).
- Les modules `utils` n'importent ni modèle, ni serializer, ni vue de `gardeniq` en tête de fichier (import dans le corps de la fonction).
- Chaque app expose ses routes dans `api_urls.py` (router DRF), inclus dans `gardeniq/urls.py` sous `api/`. `ToggleObjectRouter` (`base/routers.py`) ajoute `enable/` et `disable/`.
- Les vues héritent de `BaseAPIModelViewSet` (`base/views/base.py`) : `serializer_class` (écriture), `detail_serializer_class` (retrieve) et `list_serializer_class` (list, optionnel). `DisableAPIViewMixin` pour enable/disable.
- Les serializers héritent de `BaseSerializer` (`base/serializers/bases.py`) avec `Meta.model` et les `*MixinSerializer` de `base/serializers/mixins.py` ; pas de `ModelSerializer`. Lecture seule : `ReadOnlySerializer`.
- Les modèles réutilisent les mixins abstraits de `base/models/mixins.py` (`Slug`, `Name`, `Description`, `ProtectedDisabled`, `ProtectedDeleted`, `Seeder`…). Les suppressions/désactivations protégées lèvent les exceptions de `base/exceptions.py`.
- Les erreurs attendues sont gérées explicitement dans la vue ; `APIException` en dernier recours.
- Une `Meta` qui combine des parents hérite explicitement de leurs `Meta` quand ils y définissent des attributs (ex. `class Meta(BaseSerializer.Meta, AutocompleteSlugMixinSerializer.Meta)` dans `orderlg/serializers/order.py`). Les `Meta` des modèles Django n'héritent pas.
- Tests de vues : hériter de `ViewSetTestMixin` (`base/utils/tests.py`, `MODEL`, `BASE_PATTERN`, `DATA_TO_DEFAULT_OBJ`). Il n'y a pas de factories.

## Typage

Typer au maximum, pour la lisibilité et l'aide de l'éditeur :

- Toute fonction ou méthode écrite ou modifiée a ses paramètres et son retour typés, y compris `-> None`. Typer aussi les attributs de classe et les variables dont le type n'est pas évident.
- Syntaxe moderne (Python 3.13) : `list[str]`, `dict[str, int]`, `X | None`, `type[Model]`. Ne pas ajouter de `typing.Dict`, `List`, `Optional`, `Union` ; ceux déjà présents ne sont pas migrés sans demande (diff minimal).
- `Any` en dernier recours. Pour une exception au vérificateur, `# pyright: ignore[<règle>]` avec la règle précise, jamais un `ignore` nu.
- Pas de vérificateur de types en CI ni dans les hooks : seul Pylance (VS Code, mode `basic`) signale les erreurs. Ne pas annoncer « typage vérifié » sans l'avoir contrôlé.
- Migrations et tests exclus. Pas de campagne de typage sur du code non touché, sauf demande.

## Git et GitHub

Détail dans `docs/git_version.md` (lu par les skills `commit`, `pre-push`, `pr-create`).

- Flux : GitHub Flow, branches courtes depuis `main`, une PR par branche (dépôt `riderflo85/gardenIQ-back`).
- Branche : `(TK-<id>)(<type>)-<slug>` (ex. `(TK-61)(feat)-Optimise-remove-and-add-models`). `TK` = « Ticket » : `<id>` est le numéro de la carte du kanban Notion.
- Commit : `(TK-<id>)(<type>) - <module>: <Description>`, **en anglais**, un commit par changement logique.
  - Exemple : `(TK-41)(feat) - hardware: Add frame protocol unit tests`.
  - Le hook local `.git/hooks/prepare-commit-msg` (non versionné) ajoute tout seul le préfixe `(TK-<id>)(<type>) - ` à partir du nom de la branche : n'écrire que `<module>: <Description>`. Pour un commit d'un autre type que la branche, écrire `(<type>) - <module>: <Description>` : le hook garde ce type et met le ticket de la branche.
  - Types : `feat`, `fix`, `enh`, `refactor`, `test`, `docs`, `chore`. Le type `docs` sert aux commits de documentation (`docs/`, `README.md`, `CLAUDE.md`, règles et skills) dans une branche `feat`, `fix` ou `enh` : `(docs) - hardware: Document the USB frame protocol`. Une branche entièrement dédiée à la documentation est de type `docs`.
  - Modules : l'app concernée (`base`, `hardware`, `orderlg`, `telemetry`, `users`) ou `settings`, `ci`, `docker`, `deps`, `hooks`, `claude` hors apps. Si un nouveau module est ajouté dans `gardeniq/`, l'ajouter à cette liste.
- Squash au merge de la PR : le titre de la PR devient le message sur `main`, avec le suffixe ` (#<n>)` ajouté par GitHub (ex. `(TK-61)(feat) optimise remove and add models (#12)`). Rebaser sur `main` avant de pousser.
- Si un fichier de migration est généré, il fait partie du même changement.

Hooks : `.git/hooks/pre-commit` est le framework `pre-commit` (`pre-commit install`) : il lance black, flake8, isort, check-json, end-of-file-fixer et trailing-whitespace sur les fichiers indexés. Ne jamais contourner avec `--no-verify`.

## Garde-fous

- Confirmation avant **chaque** commit (une approbation = un seul commit) et avant tout merge de PR.
- Lire un fichier avant de le modifier ; diff minimal, sans refactor non demandé.
- Pour un bug : proposer la cause racine et le correctif **avant** de modifier le code.

## Documentation

La documentation de référence vit dans `docs/features/` et `docs/runbooks/` (Markdown, diagrammes Mermaid).

## Notion (kanban des tickets)

Les tickets vivent dans le kanban Notion, accessible par le serveur MCP `notion` (espace « GardenerIQ », compte « Garden » : toute écriture apparaît sous ce compte). Les outils `mcp__notion__*` sont chargés à la demande : `ToolSearch` avec `select:<nom>` avant le premier appel. Skills : `ticket` (lire et traiter un ticket, tenir son statut à jour) et `ticket-create` (créer des tickets à partir de `docs/backlog.md`).

- **Base** : « Tableau kanban », `collection://28f54287-aae0-81ff-b3d7-000b26a0535c`. Propriétés : `Nom`, `Id carte` (`TK-<n>`, automatique, lecture seule), `Statut`, `Priorité`, `Tags`, `Équipe`, `Assigné à`, `Nom de la branche GitHub`, `Pull Requests GitHub`.
- **Statuts** et lien avec Git : `À faire` → `En développement` (branche créée) → `Code review & test` (PR ouverte) → `À merge` (PR relue) → `Fait` (PR fusionnée sur `main`). L'intégration GitHub de Notion relie la PR au ticket et le passe à `Code review & test` toute seule après l'ouverture de la PR (observé sur TK-75) : relire le ticket avant d'écrire un statut, n'écrire que si l'intégration ne l'a pas fait.
- **Tags** : type `feature`, `bug`, `enhancement` (soit `feat`, `fix`, `enh` pour la branche) et périmètre `back`, `front`, `software`. Ce dépôt est `back`. Pas de tag pour `refactor`, `test`, `docs`, `chore` : demander.
- **Contenu d'un ticket** : le modèle « Template User Story » (carte `TK-39`) : user story, critères d'acceptation en cases à cocher, conditions techniques, dépendances, tâches, tests.
- **Lecture** : `notion-query-data-sources` en mode `rows` (le SQL a un quota sur ce plan), `notion-search` pour chercher par mots-clés (la recherche IA n'est pas disponible). La base des pull requests liées est synchronisée depuis GitHub et le MCP ne peut pas la lire directement.
- **Écriture** : le kanban est partagé avec l'équipe, donc **confirmation avant toute création ou modification** (une demande explicite de l'utilisateur dans le message vaut confirmation). Jamais d'écriture dans `Id carte` ni dans la relation `Pull Requests GitHub`. Pas de suppression de page ni de changement de schéma (refusés dans `.claude/settings.json`) : ajouter un tag ou un statut se fait dans Notion.
- **Ticket de la branche** : le `<id>` de `(TK-<id>)…` est l'`Id carte` du ticket. Pour lire un ticket par son numéro, voir le skill `ticket`.

## Backlog

Tout bug, problème d'architecture ou remarque repéré en passant et **hors du périmètre demandé** se note dans `docs/backlog.md` au lieu d'être corrigé. Ce fichier sert à créer les tickets dans le kanban Notion (skill `ticket-create`). Il est local : ignoré par git (`.gitignore`), donc absent d'un clone neuf.

- Une entrée par sujet, au format du fichier : titre, type (`bug`, `architecture`, `remarque`), user story (« En tant que … je veux … afin de … »), description, critères d'acceptation, fichiers.
- Vérifier le constat avant de l'écrire (lire le code, lancer un test) et dire ce qui n'a pas été reproduit.
- Chercher d'abord si le sujet existe déjà ; ne pas créer de doublon.
- Ne pas corriger sans demande : l'ajout au backlog ne remplace pas la décision de l'utilisateur.
- **Relire régulièrement** `docs/backlog.md` (au moins avant de créer une PR, au début d'un travail sur un sujet proche, et quand l'utilisateur le demande) et vérifier chaque entrée dont le statut n'est pas `Traité` : relire les fichiers cités, rejouer la vérification décrite, regarder si une PR ou un commit récent l'a réglée. Si le problème est résolu, passer le statut à `Traité` avec la date et la PR ou le commit ; si le constat a changé, mettre l'entrée à jour ; si elle est devenue sans objet, le dire à l'utilisateur. Ne jamais supprimer une entrée. Pour une entrée qui a un ticket, le statut se lit dans Notion (skill `ticket-create sync`) : un ticket `Fait` ne suffit pas à clore l'entrée, la vérification dans le code reste obligatoire. Le numéro `TK-<id>` s'écrit dans l'entrée à la création du ticket (statut `Ticket créé`) ; ne jamais le deviner.

## Faire évoluer ce fichier

Chaque piège rencontré devient une ligne ici, courte et précise. Préférences personnelles : `CLAUDE.local.md` (non versionné).
