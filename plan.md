# Safar 360 - Architecture et Plan d'Implémentation

## 1. Vue d'Ensemble du Projet
'Safar 360' (سفر ٣٦٠) est une Single Page Application (SPA) immersive haut de gamme conçue pour dialoguer interactivement avec les grandes figures de l'histoire, des sciences, des arts et de la pensée arabo-musulmane et universelle.
L'interface est conçue en Dark & Gold luxueux, bilingue Arabe/Français, typographiée avec les polices 'Tajawal' et 'Cairo', et structurée en mode Right-To-Left (RTL) avec un agencement en écran scindé (Split-Screen).

## 2. Charte Graphique & Spécifications Design
- **Mouvement Esthétique** : Néo-orientalisme Numérique & Luxe Sombre (Dark & Gold Heritage).
- **Variables CSS Imposées** :
  - `--bg-dark: #0a0c0e;` (Fond immersif noir profond)
  - `--panel-bg: #12151b;` (Fond des panneaux et cartes)
  - `--accent-gold: #d4af37;` (Or impérial pour bordures, icônes et reflets)
  - `--accent-gold-hover: #f1c40f;` (Or vibrant au survol et états actifs)
  - `--border-color: #272d3b;` (Séparateurs et bordures subtiles)
  - `--bot-bubble: #1a202c;` (Bulle de réponse du personnage/IA)
  - `--user-bubble: #2d2b1e;` (Bulle de message de l'utilisateur aux reflets dorés)
  - `--mic-active: #e74c3c;` (Indicateur d'enregistrement vocal écarlate)
- **Typographie** :
  - Google Fonts : `Tajawal` (titres élégants, menus, calligraphie moderne) & `Cairo` (corps de texte, chat, boutons et données).
  - Direction globale : `dir="rtl"`.
- **Identité Visuelle & Signature** :
  - Motifs géométriques arabesques subtils en arrière-plan SVG.
  - Particules dorées animées sur un Canvas interactif.
  - Effet de tilt 3D et rotation 360° fluide sans framework lourd.

## 3. Structure des Composants
1. **Top Navigation Bar** :
   - Logo 'Safar 360' / 'سَفَر ٣٦٠' avec emblème doré et badge d'époque.
   - Menu de navigation (Exploration, Époques, Manuscrits, À propos).
   - Outils interactifs : Ambiance sonore (Oud/Désert audio toggle), Sélecteur de langue, Badge VIP Explorateur.
2. **Hero Carousel** (5 Personnages Clés) :
   - Tariq ibn Ziyad (قادة وفاتحون - Commandants & Conquérants)
   - Al-Khwarizmi (علماء ومفكرون - Savants & Penseurs)
   - Ibn Battuta (رحالة ومستكشفون - Explorateurs & Voyageurs)
   - Al-Mutanabbi (كتّاب وشعراء - Écrivains & Poètes)
   - Fatima al-Fihriya (ملكات ورائدات - Reines & Figures Féminines)
   - Commandes de défilement (précédent/suivant, indicateurs à puces, sélection directe).
3. **Category Filter Bar** :
   - Les 5 catégories exactes requises avec filtrage dynamique instantané.
4. **Main Split-Screen Layout** :
   - **Panneau Gauche : Chat Interface**
     - En-tête du personnage actif (avatar, statut en ligne, époque, bouton vider la discussion, synthèse vocale).
     - Zone de messages avec bulles bot (`--bot-bubble`) et utilisateur (`--user-bubble`).
     - Suggestions de questions historiques rapides.
     - Barre de saisie de message avec bouton microphone animé (`--mic-active`) et envoi doré.
     - Réponses dynamiques contextualisées selon le personnage sélectionné avec simulateur de frappe naturelle.
   - **Panneau Droit : Interactive Canvas**
     - Rendu 3D immersif avec effet de profondeur à la souris et poussière dorée animée sur canvas HTML5.
     - Onglets interactifs :
       * *Vue 360° / المشهد التاريخي* (Scène d'époque avec points d'intérêt cliquables).
       * *Chronologie & Faits Marquants / الخط الزمني* (Ligne de temps interactive).
       * *Artefacts & Manuscrits / مقتنيات وآثار* (Objets historiques 3D interactifs).
       * *Carte des Périples / مسار الرحلات* (Carte stylisée des expéditions).

## 4. Organisation des Fichiers
- `/home/ubuntu/safar360/index.html` : Structure sémantique HTML5 complète RTL.
- `/home/ubuntu/safar360/styles.css` : Feuille de styles CSS3 moderne, variables strictes, animations et responsive.
- `/home/ubuntu/safar360/app.js` : Logique Vanilla JS (carrousel, filtres, chat engine, canvas 360 et effets).
- `/home/ubuntu/safar360/manus-routes.json` : Manifeste des routes.
- `/home/ubuntu/safar360/server.js` : Serveur Node.js natif pour le port 3000.
