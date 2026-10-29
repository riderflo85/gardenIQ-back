# Modèle de données

Dernière vérification : 2026-10-29 · 719d8a0

Diagramme relationnel des modèles Django du projet (apps `base`, `hardware`, `orderlg`, `users` ; `telemetry` n'a pas encore de modèle). Il est construit à la lecture de `gardeniq/<app>/models/` : les champs hérités des mixins abstraits de `base/models/mixins.py` sont dépliés dans chaque table, et chaque table a une clé primaire `id` automatique.

**À tenir à jour** : tout ajout, modification ou suppression d'un modèle, d'un champ ou d'une relation dans les modèles Django met ce fichier à jour dans le même commit (règle de `CLAUDE.md`).

```mermaid
erDiagram
    Status {
        int id PK
        varchar name
        text description "optionnel"
        slug tag "ex. device"
        varchar color "défaut #A2A2A2"
        bigint seed_id UK "nullable"
        bool is_ready
    }

    DeviceCategory {
        int id PK
        varchar name
        text description "optionnel"
        json pins_configuration "DATASHEET_JSON_SCHEMA"
        bigint seed_id UK "nullable"
        bool is_ready
    }

    Device {
        int id PK
        varchar name
        text description "optionnel"
        int category_id FK
        varchar uid UK "vide autorisé"
        varchar communication_protocol "USB"
        varchar path "optionnel"
        datetime last_seen "auto_now"
        int status_id FK
        varchar gd_firmware_version "optionnel"
        varchar mp_firmware_version "optionnel"
        bool need_upgrade
    }

    Channel {
        int id PK
        varchar name
        text description "optionnel"
    }

    Pin {
        int id PK
        int device_id FK "UK avec pin_number"
        int channel_choiced_id FK
        int pin_number "UK avec device_id"
    }

    ControllerCategory {
        int id PK
        varchar name
        json pin_init_cfg "PIN_INIT_CONFIG_JSON_SCHEMA"
        bigint seed_id UK "nullable"
        bool is_ready
    }

    Controller {
        int id PK
        varchar name
        int category_id FK
        int pin_id FK, UK
    }

    SensorCategory {
        int id PK
        varchar name
        varchar unity_value "optionnel"
        json pin_init_cfg "PIN_INIT_CONFIG_JSON_SCHEMA"
        bigint seed_id UK "nullable"
        bool is_ready
    }

    Sensor {
        int id PK
        varchar name
        int category_id FK
        int pin_id FK, UK
    }

    Order {
        int id PK
        varchar name
        slug slug UK
        text description
        varchar action_type "get ou set"
        int sensor_id FK "nullable"
        int controller_id FK "nullable"
        bool is_toggle_ctrl_value
        varchar ctrl_value "nullable"
        bool is_enabled
        bigint seed_id UK "nullable"
        bool is_ready
    }

    CustomUser {
        int id PK
        varchar username UK
        varchar email UK "vide autorisé"
        varchar first_name
        varchar last_name
        bool is_staff
        bool is_superuser
        bool is_active
    }

    DeviceCategory ||--o{ Device : "category PROTECT"
    Status ||--o{ Device : "status PROTECT, tag device"
    Device ||--o{ Pin : "device CASCADE"
    Channel ||--o{ Pin : "channel_choiced PROTECT"
    Channel }o--o{ Pin : "channels_available M2M"
    ControllerCategory ||--o{ Controller : "category PROTECT"
    Pin ||--o| Controller : "pin PROTECT, 1-1"
    SensorCategory ||--o{ Sensor : "category PROTECT"
    Pin ||--o| Sensor : "pin PROTECT, 1-1"
    Sensor |o--o{ Order : "sensor CASCADE"
    Controller |o--o{ Order : "controller CASCADE"
```

*Chaque relation porte le nom du champ côté enfant et son `on_delete`. La carte d'un capteur ou d'un contrôleur se lit par sa broche (`sensor.pin.device`, `sensor.pin.pin_number`). `CustomUser` n'est relié à aucun modèle du projet.*

## Contraintes et règles hors du diagramme

| Table | Règle | Où |
|---|---|---|
| `Pin` | Unicité du couple (`device`, `pin_number`) : contrainte `unique_device_pin_number` | `hardware/models/pin.py` |
| `Pin` | `channels_available` passe par la table de jointure implicite `hardware_pin_channels_available` | `hardware/models/pin.py` |
| `Device` | `status` limité aux `Status` dont le `tag` contient `device` (`limit_choices_to`, appliqué par les formulaires, pas par la base) | `hardware/models/device.py` |
| `Order` | Contrainte `check_order_action_type_sensor_controller` : soit un ordre de seeder pas prêt (`seed_id > 0`, `is_ready = False`, ni capteur ni contrôleur), soit `get` avec un capteur ou un contrôleur, soit `set` avec un contrôleur et sans capteur | `orderlg/models/order.py` |
| `DeviceCategory` | `pins_configuration` validé par `DATASHEET_JSON_SCHEMA` (`clean()` et `save()`) | [`features/pins-configuration.md`](features/pins-configuration.md) |
| `ControllerCategory`, `SensorCategory` | `pin_init_cfg` validé par `PIN_INIT_CONFIG_JSON_SCHEMA` (`clean()` et `save()`) | [`features/pin-init-cfg.md`](features/pin-init-cfg.md) |
| `Controller`, `Sensor` | Une broche n'a qu'un propriétaire : `pin` est un `OneToOneField` (unicité dans chaque table, en base), et `PinOwnerMixin` refuse en `clean()` et `save()` une broche déjà prise par l'autre table | `hardware/models/mixins.py`, `hardware/serializers/mixins.py` |

## Mixins abstraits

Les tables ci-dessus reçoivent leurs champs communs de ces mixins (`base/models/mixins.py`, `hardware/models/mixins.py`) :

| Mixin | Champs | Utilisé par |
|---|---|---|
| `NameMixinModel` | `name` | toutes les tables du projet sauf `Pin` et `CustomUser` |
| `OptionalDescriptionMixinModel` / `DescriptionMixinModel` | `description` (optionnelle / obligatoire) | `Status`, `DeviceCategory`, `Device`, `Channel` / `Order` |
| `SeederMixinModel` | `seed_id`, `is_ready` | `Status`, `DeviceCategory`, `ControllerCategory`, `SensorCategory`, `Order` |
| `SlugMixinModel` | `slug` | `Order` |
| `ProtectedDisabledMixinModel` | `is_enabled` | `Order` |
| `PinInitConfigMixin` | `pin_init_cfg` | `ControllerCategory`, `SensorCategory` |
| `PinOwnerMixin` | `pin` (un à un) | `Sensor`, `Controller` |

## Hors diagramme

Les tables des apps tierces ne sont pas représentées : `auth` (groupes et permissions de `CustomUser`), `knox` (jetons d'authentification, liés à `CustomUser`), `admin`, `contenttypes`, `sessions`. `CustomUser` hérite d'`AbstractUser` : seuls ses champs principaux sont listés.
