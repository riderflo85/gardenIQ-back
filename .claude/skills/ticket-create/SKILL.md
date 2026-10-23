---
name: ticket-create
description: Transforme les entrées de `docs/backlog.md` au statut « À créer » en tickets du kanban Notion GardenIQ, au format du « Template User Story », après recherche de doublons et confirmation, puis écrit le numéro `TK-<id>` et le lien dans le backlog (statut « Ticket créé »). Sait aussi synchroniser le backlog avec Notion (ticket « Fait » → entrée « Traité »). Utiliser quand l'utilisateur demande "crée les tickets du backlog", "envoie le backlog sur Notion", "crée le ticket n°3", "synchronise le backlog", "ticket-create" ou équivalent.
---

# ticket-create

Fait passer des entrées de `docs/backlog.md` dans le kanban Notion, sans perdre ce qu'elles disent : chaque ticket reprend la user story, le constat et les critères d'acceptation de l'entrée, dans le format du « Template User Story » de l'équipe. Pour traiter un ticket existant, voir le skill `ticket`.

Le backlog est un fichier local, ignoré par git (`.gitignore`) : s'il n'existe pas, s'arrêter. Les outils Notion (`mcp__notion__*`) se chargent à la demande avec `ToolSearch` (`select:mcp__notion__notion-fetch,mcp__notion__notion-search,mcp__notion__notion-query-data-sources,mcp__notion__notion-create-pages,mcp__notion__notion-update-page`). Le kanban, ses propriétés et ses valeurs possibles sont décrits dans le skill `ticket` et dans `CLAUDE.md` (section « Notion »).

## Paramètres acceptés

- `ticket-create` → propose la liste des entrées `À créer` et laisse choisir lesquelles créer.
- `ticket-create 3 5` → seulement les entrées n°3 et n°5.
- `ticket-create sync` → synchroniser les statuts du backlog avec Notion, sans rien créer.

## Correspondance entrée du backlog → ticket

| Backlog | Ticket Notion |
|---|---|
| Titre (`## <n>. …`) | `Nom` : texte simple, sans balises de code (les noms de fichiers ou de fonctions restent entre guillemets). Pas de préfixe `[Back]` : le tag `back` porte le périmètre. |
| Type | `Tags`, **à confirmer** : `bug` → `bug`, `architecture` → `enhancement`, `remarque` → `enhancement`. Toujours ajouter `back`. |
| (valeur fixe) | `Statut` = `À faire`, `Équipe` = `Développement` |
| (à décider) | `Priorité` : proposer `Prio - Normale` par défaut, `Prio - Urgent` si l'entrée décrit un défaut qui casse un usage (démarrage, perte de données, faille d'accès), `Prio - Faible` pour une amélioration sans effet visible. L'utilisateur tranche. |
| (à demander) | `Assigné à` : jamais de valeur par défaut. |
| User story | Section `## 🎯 User Story`, en citation |
| Description | Section `## ⚙️ Conditions techniques / Contraintes` : le constat, comment l'observer, puis « Fichiers concernés » |
| Critères d'acceptation | Section `## 📋 Critères d’acceptation (Definition of Done)`, une case `- [ ]` par critère |
| « Lié à » / « Dépend de » | Section `## 🔄 Dépendances` : le `TK-<n>` du ticket lié s'il existe, sinon « entrée n°<n> du backlog » |
| Critères qui parlent de tests | Section `## 🧪 Tests & Validation`, uniquement s'il y en a |

Une section sans contenu dans le backlog est **omise** : ne rien inventer, ni tâches ni contraintes. Le modèle de l'équipe est la carte `Template User Story` (`TK-39`).

Squelette du contenu (syntaxe Notion : indentation par tabulations, caractères `\ * ~ ` $ [ ] < > { } |` échappés avec `\` hors des blocs de code) :

```markdown
## 🎯 User Story
> En tant que …, je veux … afin de ….

## ⚙️ Conditions techniques / Contraintes
Constat : …

- Fichiers concernés : `gardeniq/…`

## 📋 Critères d’acceptation (Definition of Done)
- [ ] …
- [ ] …

## 🔄 Dépendances
- …
```

Avant d'écrire du contenu, **lire la spécification** `notion://docs/enhanced-markdown-spec` (`notion-fetch` avec cet identifiant), comme l'exige l'outil de création.

## Procédé

### 1. Lire le backlog

Lire `docs/backlog.md` en entier. Retenir les entrées dont le statut est `À créer`. Ignorer `Ticket créé` et `Traité` : ne jamais recréer un ticket déjà créé. Présenter un tableau (n°, titre, type) et, sans paramètre, demander lesquelles créer.

### 2. Vérifier que le kanban n'a pas changé

Lire le schéma : `notion-fetch` sur `collection://28f54287-aae0-81ff-b3d7-000b26a0535c`. Les noms de propriétés et les options de `Statut`, `Tags`, `Équipe` et `Priorité` doivent exister tels que décrits dans le skill `ticket`. Une option manquante (par exemple un tag) : s'arrêter et le dire, sans contourner.

### 3. Chercher les doublons

Pour chaque entrée, deux contrôles :
- lister les tickets ouverts (`notion-query-data-sources`, mode `rows`, `Statut` différent de `Fait`) et comparer les titres ;
- chercher les mots-clés du titre et les noms de fichiers cités avec `notion-search` (`data_source_url` du kanban).

Un ticket proche trouvé : afficher son `TK-<n>`, son titre et son statut, et demander : créer quand même, lier l'entrée à ce ticket (écrire son numéro dans le backlog, sans créer), ou ignorer.

### 4. Préparer et confirmer

Construire chaque ticket selon la correspondance ci-dessus. Poser **une seule question groupée** pour ce qui manque (priorité, assignation, confirmation des tags). Puis afficher, avant toute écriture :

```
n° backlog | Nom | Tags | Priorité | Équipe | Assigné à
```

et l'aperçu du contenu du premier ticket. Les tickets sont visibles de toute l'équipe : attendre une confirmation explicite. Une demande claire dans le message initial (« crée les tickets 3 et 5, priorité normale, assignés à Florent ») vaut confirmation.

### 5. Créer

Appeler `notion-create-pages` avec `allow_async: false` (le numéro du ticket est nécessaire tout de suite) :

```json
{"parent": {"type": "data_source_id", "data_source_id": "28f54287-aae0-81ff-b3d7-000b26a0535c"},
 "allow_async": false,
 "pages": [{
   "properties": {
     "Nom": "Les routes enable et disable renvoient toujours 405",
     "Statut": "À faire",
     "Tags": ["bug", "back"],
     "Équipe": "Développement",
     "Priorité": "Prio - Normale",
     "Assigné à": ["👤 Florent"]
   },
   "content": "## 🎯 User Story\n> En tant que …"
 }]}
```

Ne pas renseigner `Id carte` (automatique), ni `Date d'échéance`, `Sous tâches`, `Pull Requests GitHub`, `Nom de la branche GitHub`. Omettre `Priorité` ou `Assigné à` si l'utilisateur n'a rien décidé.

### 6. Vérifier

Relire chaque page créée avec `notion-fetch` (URL donnée par la création) : lire `Id carte` (le `TK-<n>` attribué), contrôler propriétés et contenu, et que la page n'est pas tronquée. Une page absente ou incomplète : le dire, ne pas supposer que la création a réussi.

### 7. Mettre à jour le backlog

Pour chaque entrée créée, remplacer la ligne de statut :

```
- **Statut** : Ticket créé le <date> — **Ticket** : TK-<n> ([Notion](<url>))
```

Si une entrée cite une autre entrée (« Dépend de : 3 »), ajouter le `TK-<n>` correspondant une fois créé. Ne jamais supprimer d'entrée. Puis rendre compte : un tableau n° du backlog → `TK-<n>` → lien, et ce qui n'a pas été créé et pourquoi.

## Synchroniser (`ticket-create sync`)

Aucune création. Pour chaque entrée portant un `TK-<n>` :

1. Lire le ticket dans Notion (`Id carte`, mode `rows`) : statut, assigné, relation `Pull Requests GitHub`.
2. Statut `Fait` : relire aussi le code ou rejouer la vérification décrite par l'entrée (règle de `CLAUDE.md`), puis proposer de passer l'entrée à `Traité` avec la date et la PR. Un statut Notion seul ne prouve pas que le problème a disparu.
3. Autre statut : le noter dans le compte rendu, sans changer l'entrée.
4. Ticket introuvable (supprimé, renuméroté) : le signaler.
5. Entrée `Traité` dans le backlog alors que le ticket n'est pas `Fait` : le signaler. Changer le statut Notion se fait avec le skill `ticket`, jamais ici.

Modifier le backlog seulement après l'accord de l'utilisateur sur les passages à `Traité`.

## À éviter

- Créer sans recherche de doublons ni confirmation.
- Recréer une entrée déjà `Ticket créé`.
- Écrire `Id carte`, supprimer une page, modifier le schéma de la base.
- Inventer des tâches, des contraintes ou une priorité absentes du backlog.
- Mettre dans un ticket des valeurs du `.env`, des jetons ou des identifiants réels.
- Donner pour lien le chemin d'un fichier local : le backlog n'est pas partagé, le ticket doit se suffire à lui-même.
