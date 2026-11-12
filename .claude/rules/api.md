---
paths:
  - "gardeniq/**/views.py"
  - "gardeniq/**/views/**"
  - "gardeniq/**/serializers.py"
  - "gardeniq/**/serializers/**"
---

# API (vues et serializers)

- Les vues héritent de `BaseAPIModelViewSet` (`gardeniq/base/views/base.py`) et déclarent `serializer_class` (écriture : create, update et actions personnalisées), `detail_serializer_class` (retrieve) et, si la liste doit être plus légère, `list_serializer_class` (sinon `list` utilise `detail_serializer_class`). Méthodes HTTP autorisées : GET, POST, PUT, DELETE ; PATCH renvoie 405.
- Serializers de lecture (`list_serializer_class`, `detail_serializer_class`) : hériter de `ReadOnlySerializer` (`gardeniq/base/serializers/bases.py`), qui met tous les champs en lecture seule et interdit `save`. Inutile de répéter `read_only=True` champ par champ. `MinimalReadOnlySerializer` (`id` + `name`) pour les relations imbriquées.
- Limiter le coût des requêtes dans `get_queryset` selon l'action (`select_related` / `prefetch_related` sur `list` et `retrieve`), comme `OrderAPIModelView` et `DeviceAPIModelView`. La pagination par défaut est `LimitOffsetPagination` (30 objets).
- Accès : par défaut authentification Knox (token) et `IsAuthenticated`, avec throttling (`gardeniq/settings/third_party/rest_framework.py`). Pour une règle différente, surcharger `permission_classes` ou `get_permissions()` (ex. `UserAPIModelView`). Ne pas ouvrir un endpoint en `AllowAny` sans que ce soit demandé.
- Activation / désactivation : `DisableAPIViewMixin` (`gardeniq/base/views/mixins.py`, placé avant `BaseAPIModelViewSet`) et `ToggleObjectRouter` pour exposer `enable/` et `disable/`.
- Erreurs : le gestionnaire global `gardeniq/base/exception_handler.py` (`REST_FRAMEWORK["EXCEPTION_HANDLER"]`) donne à toute erreur le corps `{"status": <int>, "code": <str>, "message": <str>, "errors": <dict>}`. Dans une vue, lever l'exception, ne pas l'attraper ni renvoyer une `Response` d'erreur. Correspondances :
  - exceptions DRF : leur statut et leur code (`invalid`, `not_authenticated`, `permission_denied`, `not_found`, `method_not_allowed`, `throttled`…) ; une erreur de validation range ses messages dans `errors` par champ, ceux sans champ sous `non_field_errors` ;
  - `ValidationError` de Django (levée par un `save()` ou un `clean()`) → 400 `invalid`, comme celle de DRF ;
  - `ObjectDoesNotExist` (ex. `Channel.DoesNotExist`) → 400 `does_not_exist`, avec le message de l'exception ;
  - `ProtectedError` / `RestrictedError` de Django → 409 `protected`, les objets bloquants dans `errors` par modèle (`{"devices": ["Device `Card` : …"]}`) ; `ProtectedException` de `gardeniq/base/exceptions.py` → 409 `protected` ;
  - toute autre exception → 500 `server_error` avec un message générique ; le détail ne part que dans les logs (`gardeniq.base.exception_handler`). Avec `DEBUG`, elle n'est pas traitée : Django affiche sa page de debug avec la traceback.
  Un nouveau cas : une sous-classe d'`APIException` et une branche dans `_to_api_exception`, testées dans `gardeniq/base/tests/test_exception_handler.py`. Une bibliothèque qui renvoie son erreur en `Response` (ex. limite de tokens de knox) se convertit en exception dans la vue du projet (`users/views/auth.py`).
- Documentation OpenAPI (drf-spectacular) : personnaliser avec `extend_schema`, `extend_schema_view`, `extend_schema_serializer`, `extend_schema_field` directement sur la vue ou le serializer (ex. `LoginView`). Réglages globaux dans `gardeniq/settings/third_party/spectacular.py`. Pour une extension globale, créer `gardeniq/schema.py` (il n'existe pas encore). Swagger et ReDoc ne sont servis qu'avec `DEBUG`.
