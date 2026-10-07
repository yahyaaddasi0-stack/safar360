# Politique Schema.org et JSON-LD de Sard360

Cette politique s’applique aux templates, aux builders statiques et aux scripts WordPress de Sard360. Les données structurées doivent décrire uniquement les contenus visibles et les métadonnées réellement présentes; ne jamais inventer un prix, une disponibilité, une date de publication, un auteur ou un identifiant bibliographique.

## Types à produire

- Les ouvrages présentés dans Micro-Khizana et les fiches de livres de Khizana utilisent `Book` avec `name`, `author` lorsqu’il est connu, `isbn` seulement après vérification d’une édition, `image` quand une jaquette existe et `offers` contenant une `Offer.url` vers l’URL Amazon affiliée. Un ASIN Amazon n’est jamais considéré comme preuve d’ISBN, même s’il passe le contrôle arithmétique ISBN. Si les métadonnées de l’offre contredisent l’auteur ou le titre visible, omettre l’Offer du JSON-LD et consigner l’écart dans le registre, sans altérer silencieusement la carte existante. Aucun `price` ni `availability` ne sera renseigné sans preuve actuelle.
- Les objets maîtres non livres de Khizana utilisent `Product` avec `name`, `description`, `image`, `category` et une ou plusieurs `Offer.url` correspondant aux variantes réellement visibles. Ne pas publier d’avis, d’évaluation, de stock ou de prix non sourcés.
- Les entrées de Cinéma Sard utilisent `VideoObject`, pas `Movie`, car il s’agit de vidéos YouTube/documents publiés sur une chaîne et non d’œuvres cinématographiques déclarées comme telles. Les propriétés sont dérivées du catalogue: `name`, `description`, `thumbnailUrl`, `embedUrl`, `contentUrl`, `duration` ISO 8601, `creator` (Sard 360) et la catégorie si disponible. `uploadDate` n’est ajouté que si une date réelle existe dans les données.

## Intégration et idempotence

Les builders statiques doivent sérialiser les données JSON avec échappement sûr pour `<`, `>` et `&`, puis émettre un seul bloc `<script type="application/ld+json">` par collection dans le HTML rendu. Les scripts d’injection WordPress utilisent un identifiant stable par contenu, détectent leur présence avant écriture et ajoutent les nouveaux blocs à côté du contenu existant sans modifier le HTML des cartes Micro-Khizana. Avant une mise à jour REST, recharger le contenu courant et refuser une écriture si le bloc d’affiliation a changé durant le traitement.

Les URLs Amazon publiées dans les `Offer` doivent utiliser le tag `sard360-20`. Le lien d’achat dans le HTML conserve `target="_blank"` et `rel="sponsored nofollow noopener"`. Un lien n’est publié que si le titre du produit et l’édition sont confirmés; une réponse HTTP 200 de page anti-robot Amazon ne constitue pas une validation produit. Pour une carte héritée sans ISBN explicitement vérifié, omettre `Book.isbn` plutôt que de l’inférer depuis l’ASIN.

## Validation de publication

Chaque changement doit passer: validation JSON, extraction/parsing des JSON-LD émis, build statique, contrôle de présence et d’absence de doublons, vérification des liens et contrôle REST/public des contenus WordPress modifiés. Google recommande JSON-LD et exige que les données structurées correspondent au contenu visible; un balisage valide ne garantit pas un résultat enrichi.

## Règle permanente pour les nouveaux contenus

- Tout livre ajouté à `products.json` ou à un bloc Micro-Khizana doit générer un nœud `Book`; lorsqu’un ISBN/ASIN n’est pas démontré, ne pas en fabriquer un. Les articles sous forme de liste doivent baliser **toutes** les œuvres effectivement retenues et visibles, sans plafond arbitraire de deux.
- Tout nouvel objet maître dans `products.json` doit générer un nœud `Product`; chaque variante publiée devient une `Offer.url`. Le template Khizana (`khizana.html`) crée les nœuds au chargement des données.
- Chaque entrée valide ajoutée à `cinema.json` doit créer un `VideoObject` dans le template `cinema.html` et dans l’export WordPress généré par `scripts/build-wordpress-embed.mjs`. Une entrée dépourvue d’identifiant YouTube n’est pas balisée.
- Le script de publication `scripts/enrich-pending-articles.py` ajoute désormais le `Book` JSON-LD en même temps que chaque nouveau bloc Micro-Khizana. `scripts/backfill-schema-org.py` sert aux reprises idempotentes et au backfill des articles et pages de catalogue existants; il enregistre des checkpoints atomiques dans `scripts/articles_registry.json` après chaque article WordPress confirmé.
- Procédure de maintenance: `node scripts/build-static.mjs`; ensuite exécuter `python3 scripts/backfill-schema-org.py` pour un dry-run, puis `python3 scripts/backfill-schema-org.py --apply` pour publier. Le script ne change ni le statut Astra ni les autres champs éditoriaux WordPress.
- Une `Offer` sans prix ni stock expose uniquement l’URL d’achat affiliée; elle est destinée à la description sémantique du contenu et n’affirme pas l’éligibilité aux résultats enrichis Product de Google.

## Sources de référence

- Schema.org `Book`: https://schema.org/Book
- Schema.org `Product`: https://schema.org/Product
- Schema.org `VideoObject`: https://schema.org/VideoObject
- Google Search, données structurées vidéo: https://developers.google.com/search/docs/appearance/structured-data/video
- Google Search, principes généraux et cohérence avec le contenu visible: https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data
- WordPress REST API, pages: https://developer.wordpress.org/rest-api/reference/pages/
- WordPress Application Passwords: https://developer.wordpress.org/advanced-administration/security/application-passwords/
