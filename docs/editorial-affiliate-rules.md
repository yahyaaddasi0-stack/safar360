# Règles éditoriales — Micro-Khizana

## Couverture des articles de type liste

Lorsqu’un article présente explicitement une sélection ou une liste d’œuvres (par exemple « 8 روايات », « 5 كتب » ou « أفضل 10 أفلام »), le bloc Micro-Khizana doit couvrir **chaque élément recommandé dans l’article**, sans plafond arbitraire de deux produits. Le nombre d’entrées du bloc doit correspondre à la liste éditoriale complète, y compris lorsqu’elle dépasse huit références.

Avant publication :

1. Extraire les titres et auteurs depuis le texte de l’article, dans le même ordre.
2. Vérifier que chaque produit proposé correspond bien à l’œuvre citée et à une édition identifiable.
3. Contrôler la page Amazon et l’image de couverture avant de retenir le lien. Ne pas inventer un ASIN, un ISBN ou une URL.
4. Ajouter `tag=sard360-20` à chaque URL Amazon et rendre les liens avec `target="_blank" rel="sponsored nofollow noopener"`.
5. Si une œuvre n’a pas d’édition Amazon fiable, documenter l’absence et ne pas la remplacer par un produit hors sujet.
6. Afficher toutes les fiches dans une grille responsive, lisible sur mobile, sans hauteur fixe qui tronque le texte ou les boutons.

## Articles narratifs

Pour un article narratif ou une enquête qui ne formule pas de liste de recommandations, sélectionner seulement les ouvrages réellement pertinents au sujet. La sélection éditoriale peut contenir un ou deux livres; ne pas forcer de produits artificiels.

## Source de vérité et registre

Utiliser les identifiants, permaliens et champs de publication natifs retournés par l’API REST WordPress. Le registre `scripts/articles_registry.json` doit conserver l’ID, le titre, le slug et le champ `link` natif du post, le statut Micro-Khizana, les ISBN/ASIN extraits des cartes et le statut du rapprochement éventuel avec le catalogue Cinéma. Ne jamais construire un permalien en devinant sa date ou son slug.
