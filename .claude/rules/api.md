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
- Erreurs attendues : les attraper dans la vue et renvoyer une réponse explicite (ex. 409 quand une `ProtectedException` de `gardeniq/base/exceptions.py` signale des relations protégées). Lever une `APIException` seulement en dernier recours.
- Documentation OpenAPI (drf-spectacular) : personnaliser avec `extend_schema`, `extend_schema_view`, `extend_schema_serializer`, `extend_schema_field` directement sur la vue ou le serializer (ex. `LoginView`). Réglages globaux dans `gardeniq/settings/third_party/spectacular.py`. Pour une extension globale, créer `gardeniq/schema.py` (il n'existe pas encore). Swagger et ReDoc ne sont servis qu'avec `DEBUG`.
