---
paths:
  - "gardeniq/*/migrations/**"
---

# Migrations

- Ne jamais modifier ni supprimer une migration déjà présente sur `main` : elle peut être déjà déployée et ne pas être réversible. En cas de doute, demander à l'utilisateur.
- Attention particulière à `users` : `AUTH_USER_MODEL = "users.CustomUser"`, donc toute modification de ses migrations touche aussi `knox` et les permissions. Les migrations de `orderlg` dépendent de celles de `hardware`, et celles de `hardware` de `base` : ne pas renuméroter ni réécrire une migration dont une autre app dépend.
- Les migrations sont générées par `./manage.py makemigrations` (jamais écrites de tête) et appliquées sur la base locale SQLite (`./manage.py migrate <app> <numero>`). Les relire avant de les garder.
- La migration fait partie du même commit que le changement de modèle. Avant de commiter ou de pousser, vérifier qu'aucune n'est oubliée : `./manage.py makemigrations --check --dry-run` (la CI ne le vérifie pas).
- Les données de référence (statuts, catégories…) passent par les seeders (`./manage.py seed`), pas par des migrations de données (`RunPython`, `RunSQL`) : il n'y en a aucune dans le projet.
- Plusieurs migrations créées dans une même app sur la branche : les fusionner en une seule avant de pousser, **uniquement celles de la branche**.
- Avant de changer de branche, défaire les migrations créées sur la branche courante : `./manage.py migrate <app> <numero précédent>`. Lister celles de la branche : `git diff --name-status main -- 'gardeniq/*/migrations/*.py'`. Si le résultat contient des migrations *modifiées* (`M`) ou *supprimées* (`D`), demander à l'utilisateur.
- Les tests construisent leur base à partir des migrations : une migration cassée fait échouer toute la suite.
- Les migrations sont exclues de black, isort, flake8 et des hooks de fin de fichier et d'espaces en fin de ligne : ne pas les reformater.
- Après une nouvelle version stable, les migrations squashées déjà déployées perdent leur liste `replaces` et leur suffixe `squashed` (voir `docs/git_version.md`). Il n'y en a aucune pour l'instant.
