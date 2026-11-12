# Feature : champ JSON `pins_configuration` (datasheet d'une carte)

Dernière vérification : 2026-11-12 · 4dfd4c8

## Résumé

`pins_configuration` est la datasheet d'une catégorie de carte (`DeviceCategory`, ex. Raspberry Pi Pico) : les types de canaux qu'elle propose et, par type, ses canaux avec leurs broches. Le champ est obligatoire et validé par `DATASHEET_JSON_SCHEMA` à l'écriture par l'API et à chaque `save()` du modèle. À la création d'une carte (`Device`), la datasheet de sa catégorie sert à créer ses broches (`Pin`), chacune avec les canaux (`Channel`) qu'elle accepte.

## Contexte

Chaque carte (`Device`) appartient à une catégorie qui décrit son matériel une fois pour toutes. La datasheet permet de savoir quelles broches existent et ce qu'elles savent faire (numérique, PWM, analogique, bus I2C, SPI, UART), sans recopier ces informations sur chaque carte.

La page Notion « Device Category » appelait ce champ `setup_pins`. Le code l'a nommé `pins_configuration`. TK-74 l'a rendu obligatoire (plus de valeur par défaut), a ajouté la validation et le seeder, et a factorisé le schéma (fonction `_channels_schema`) sans en changer le comportement. TK-74 l'utilise aussi pour créer les broches d'une nouvelle carte : avant, chaque `Pin` se créait à la main avec un canal choisi obligatoire.

## Architecture

```mermaid
flowchart TD
    subgraph settings[settings/project/cards.py]
        CH[_channels_schema pin_count]
        SCHEMA[DATASHEET_JSON_SCHEMA]
    end
    subgraph hardware[app hardware]
        VALID[validations.jsonschema_validation]
        SER[DeviceCategorySerializer.validate_pins_configuration]
        MODEL[DeviceCategory.clean et save]
        DEV[Device.save]
        SEED[DeviceCategorySeeder]
        CHAN[Channel du ChannelSeeder]
        PIN[Pin et channels_available]
    end
    API[API REST /api/device-categories/] --> SER
    SEED --> SER
    CH --> SCHEMA
    SER --> VALID
    MODEL --> VALID
    VALID --> SCHEMA
    DEV -->|lit la datasheet de sa categorie| MODEL
    DEV -->|cree les broches| PIN
    CHAN --> PIN
```

*Le serializer et le modèle valident avec le même schéma ; à sa création, un `Device` lit la datasheet de sa catégorie pour créer ses broches.*

Le serializer renvoie une erreur 400 à l'API, `clean()` alimente les formulaires de modèle (admin), et `save()` protège toutes les autres écritures (shell, seeders, code métier).

## Flux / Comportement

```mermaid
sequenceDiagram
    participant C as Client API
    participant S as DeviceCategorySerializer
    participant J as jsonschema_validation
    participant M as DeviceCategory.save
    C->>S: POST /api/device-categories/ {name, pins_configuration}
    S->>J: validate_pins_configuration(value)
    alt schéma refusé
        J-->>C: 400 {"pins_configuration": [message]}
    else schéma accepté
        S->>M: save() valide une seconde fois
        M-->>C: 201 + représentation avec is_ready
    end
```

*Création d'une catégorie de carte ; le PUT suit le même chemin.*

### Format

```json
{
  "available_channels": ["digit", "analog"],
  "digits":  [{"name": "GP0", "pins": [0]}, {"name": "GP1", "pins": [1]}],
  "pwms":    [{"name": "PWM0", "pins": [0]}],
  "analogs": [{"name": "ADC0", "pins": [26]}],
  "i2cs":    [{"name": "I2C0", "pins": [0, 1]}],
  "spis":    [{"name": "SPI0", "pins": [0, 1, 2, 3]}],
  "uarts":   [{"name": "UART0", "pins": [0, 1]}]
}
```

| Clé | Obligatoire | Contenu | Broches par canal (positions typées) |
|---|---|---|---|
| `available_channels` | oui | Liste de chaînes : types de canaux proposés | — |
| `digits` | oui | Liste de canaux `{"name": str, "pins": [int]}` | 1 |
| `pwms` | oui | idem | 1 |
| `analogs` | oui | idem | 1 |
| `i2cs` | non | idem | 2 |
| `spis` | non | idem | 4 |
| `uarts` | non | idem | 2 |

Dans chaque canal, `name` et `pins` sont obligatoires. Une liste vide est acceptée pour un type obligatoire : `{"available_channels": [], "digits": [], "pwms": [], "analogs": []}` est la plus petite datasheet valide.

### Création des broches d'une carte

`Device.save()` appelle `_create_pins_with_datasheet()` quand la carte est nouvelle, dans la même transaction que son insertion. Chaque nom de `available_channels` doit exister en `Channel` (seeder). Sa clé dans la datasheet est son pluriel (`digit` → `digits`), et ses canaux donnent les numéros de broches.

```mermaid
sequenceDiagram
    participant C as Client API
    participant D as Device.save
    participant P as _create_pins_with_datasheet
    participant B as Base
    C->>D: POST /api/devices/ avec category
    D->>B: insertion du Device dans une transaction
    D->>P: carte nouvelle uniquement
    P->>B: lit les Channel de available_channels
    alt un canal absent de la base
        P-->>C: Channel.DoesNotExist, log WARNING, 400 does_not_exist, transaction annulee
    else tous les canaux presents
        P->>B: un Pin par numero, avec ses channels_available
        D-->>C: 201
    end
```

*Création d'une carte et de ses broches ; un canal non seedé annule tout.*

Exemple : avec la datasheet seedée du Raspberry Pi Pico, une nouvelle carte reçoit 29 broches (0 à 28), avec `digit` et `pwm` sur chacune et `analog` en plus sur 26, 27 et 28.

| Règle | Comportement |
|---|---|
| Broches créées | Une par numéro listé dans un type de `available_channels`. Un type absent de `available_channels` est ignoré, même si sa clé liste des broches. |
| `channels_available` | Les canaux dont un canal de la datasheet liste ce numéro, sans doublon. Un canal à plusieurs broches (I2C `[0, 1]`) est ajouté à chacune. |
| `channel_choiced` | Vide (`NULL`) : il se choisit ensuite. |
| Canal inconnu | `Channel.DoesNotExist` avec la catégorie et les noms manquants, un `WARNING` dans le logger `gardeniq.hardware.models.device` ; rien n'est écrit, ni carte ni broche. L'API répond 400 `does_not_exist` (voir `api-errors.md`). |
| Relance de `_create_pins_with_datasheet()` | Même résultat : les broches existantes sont réutilisées et leurs `channels_available` réécrits ; une broche absente de la datasheet n'est ni supprimée ni modifiée. |

## Configuration & Utilisation

| Élément | Valeur actuelle | Effet |
|---|---|---|
| `settings.DATASHEET_JSON_SCHEMA` | Schéma JSON draft 2020-12 (`settings/project/cards.py`) | Règles décrites ci-dessus |
| Valeur par défaut du champ | Aucune | Champ obligatoire en base, à l'API et dans le seeder |
| Sérialisation | `DeviceCategoryListReadOnlySerializer` masque le champ ; détail et écriture l'affichent | La liste reste légère |
| Seeder | `fixtures/sources/device_categories.json` : Raspberry Pi Pico (`seed_id` 1) | `./manage.py seed --app hardware [--update]` |
| Canaux (`Channel`) | `fixtures/sources/channels.json` (`ChannelSeeder`) : `digit`, `analog`, `pwm`, `i2c`, `spi`, `uart` | À seeder avant de créer une carte : chaque nom de `available_channels` doit exister |

```bash
curl -X POST http://localhost:8000/api/device-categories/ \
  -H "Authorization: Token <jeton>" -H "Content-Type: application/json" \
  -d '{"name": "Carte de test", "pins_configuration": {"available_channels": ["digit"], "digits": [{"name": "GP0", "pins": [0]}], "pwms": [], "analogs": []}}'
```

## Points d'attention

- **Nombre et type de broches non contrôlés au-delà des positions listées.** `prefixItems` ne type que les positions décrites : `pins: []` est accepté, `pins: [1, "x"]` aussi pour un canal à une broche, et un `i2cs` avec une seule broche passe. Seule une broche non entière à une position listée est refusée. Entrée n°14 de `docs/backlog.md`.
- **Schéma ouvert.** Les clés inconnues, au premier niveau comme dans un canal, sont acceptées. Le schéma ne relie pas les valeurs de `available_channels` aux clés présentes. Un nom sans clé correspondante ne crée aucune broche, sans avertissement (`TODO` dans `_create_pins_with_datasheet`). Le lien avec le modèle `Channel` n'est vérifié qu'à la création d'une carte.
- **Broches créées à l'insertion seulement.** Changer la catégorie d'une carte existante, ou modifier la datasheet de sa catégorie, ne recrée ni ne met à jour ses broches.
- **Pas de contrôle sur une broche modifiée ensuite.** Une `Pin` créée ou modifiée par l'API (`/api/pins/`) ou l'admin n'est pas confrontée à la datasheet : rien ne vérifie que son numéro ou son `channel_choiced` y figurent.
- **Canaux multi-broches.** Le rôle de chaque broche d'un canal I2C, SPI ou UART (SDA, SCL…) et le nom du canal (`I2C0`) ne sont pas conservés : chaque broche reçoit seulement le type de canal.
- **Admin Django.** Le schéma est vérifié par `clean()` (formulaire d'admin) et par `save()` : l'erreur s'affiche sous le champ, avec un texte d'aide sur le format (`PINS_CONFIGURATION_HELP_TEXT`, `hardware/admin.py`).

## Tests & Vérification

```bash
pytest -n auto --reuse-db -- gardeniq/hardware/tests/tests_models/test_device.py
pytest -n auto --reuse-db -- gardeniq/hardware/tests/tests_serializers/test_device.py
pytest -n auto --reuse-db -- gardeniq/hardware/tests/tests_views/test_device.py
pytest --reuse-db -- gardeniq/hardware/tests/tests_seeders/test_devicecategory.py
pytest --reuse-db -- gardeniq/hardware/tests/test_admin.py
```

La création des broches est couverte par `TestDeviceCreatePinsWithDatasheet` et `TestDeviceSave` (`tests_models/test_device.py`), dont le Pico seedé et ses 29 broches, et par les tests de création de `tests_views/test_device.py` (201 avec broches, 400 `does_not_exist`).

## Fichiers clés

| Chemin | Rôle |
|---|---|
| `gardeniq/settings/project/cards.py` | `DATASHEET_JSON_SCHEMA` et `_channels_schema` |
| `gardeniq/hardware/validations.py` | `jsonschema_validation` (schéma → `ValidationError` Django) |
| `gardeniq/hardware/models/device.py` | `DeviceCategory` : champ et validation dans `clean()` et `save()` ; `Device.save` et `_create_pins_with_datasheet` : création des broches |
| `gardeniq/hardware/models/pin.py` | `Channel` (`name` unique) et `Pin` (`channels_available`, `channel_choiced` nullable) |
| `gardeniq/hardware/fixtures/sources/channels.json` | Canaux seedés par `ChannelSeeder` |
| `gardeniq/hardware/admin.py` | Texte d'aide du champ JSON (`JSONHelpTextAdminMixin`) |
| `gardeniq/hardware/serializers/device.py` | `DeviceCategorySerializer.validate_pins_configuration`, serializers liste, détail et seeder |
| `gardeniq/hardware/fixtures/seeders/devicecategory.py` | `DeviceCategorySeeder` |
| `gardeniq/hardware/fixtures/sources/device_categories.json` | Datasheet du Raspberry Pi Pico |

## Références

- Ticket TK-74 « Appliquer le diagramme de relation » ([Notion](https://app.notion.com/p/3b454287aae080c3a0e5d15b6c2de667)).
- Notion : [Device Category](https://app.notion.com/p/37354287aae0809997b6fc3f0938c7a8), [Ajout d'un nouveau device (micro contrôleur)](https://app.notion.com/p/37354287aae0803b8739e364daa905dc).
- Voir aussi :
  - [`docs/features/pin-init-cfg.md`](pin-init-cfg.md) : la configuration d'initialisation d'une broche (`ControllerCategory`, `SensorCategory`).
  - [`docs/features/api-errors.md`](api-errors.md) : la réponse 400 `does_not_exist` quand un canal manque.
  - [`docs/modele-de-donnees.md`](../modele-de-donnees.md) : `Device`, `Pin` et `Channel` dans le diagramme relationnel.
