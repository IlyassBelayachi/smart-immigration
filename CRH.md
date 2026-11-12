# CRH — Compte rendu de Hicham

À la fin de chaque session de travail sur Smart Immigration, mettre à jour l’état du projet et les tâches restantes, puis ajouter une entrée datée à l’historique. Indiquer les changements livrés, les vérifications effectuées, les limites constatées et la prochaine action. Conserver les anciennes entrées.

## 11 novembre 2026 — État du projet

Le prototype local permet à un candidat fictif de préparer un dossier d’immigration et à un consultant de l’examiner. Le périmètre a évolué depuis les documents de cadrage initiaux. Le dépôt de dossiers est désormais général et couvre dix destinations. Les règles automatisées couvrent le parcours détaillé Canada–Études.

### Fonctionnalités disponibles

- **Accueil et comptes.** Deux espaces Candidat et Consultant, avec inscription, connexion et déconnexion. Les comptes consultants sont créés sur invitation. L’inscription candidat comporte des numéros fictifs de CIN et de passeport.
- **Espace candidat.** Tableau de bord avec prochaine action, état du dossier et activité récente. Le candidat peut accéder à son formulaire, retrouver ses pièces transmises et modifier son nom dans son profil. La démo gère un dossier par compte.
- **Dépôt général.** Le formulaire en quatre étapes couvre le projet, la situation, les pièces et le récapitulatif. Les champs varient selon le motif du séjour. Le catalogue couvre l’Espagne, la France, l’Italie, la Belgique, Israël, les Pays-Bas, l’Allemagne, le Canada, la Turquie et la Suisse. Il s’appuie sur le stock migratoire 2024 de l’ONU et renvoie vers des portails officiels. Le dépôt accepte les PDF, DOCX, JPG et PNG selon le type de pièce.
- **Parcours Canada–Études.** Le candidat peut évaluer son profil et son budget, lire des spécimens TXT ou PDF, y compris scannés, puis corriger et confirmer les champs. Le rapport applique trois critères de base et cinq vérifications complémentaires. Les incohérences de nom ou de montant détectées bloquent la transmission au consultant jusqu’à correction.
- **Espace consultant.** Le rapport d’examen présente les données saisies, les pièces originales disponibles, les champs extraits et les compteurs. Le consultant peut attribuer ou réattribuer un dossier, demander un complément, écrire une note interne, terminer l’examen ou autoriser l’envoi en motivant sa décision. Le candidat voit la décision et les demandes de complément. Les notes internes sont réservées aux consultants ayant accès au dossier.
- **Stockage.** SQLite conserve localement les comptes, les sessions, les dossiers, les fichiers du parcours général et l’historique. Le téléchargement d’un fichier vérifie l’accès au dossier. L’autorisation d’envoi est enregistrée dans la plateforme. La transmission vers une autorité reste externe.

### Vérifications disponibles

- **46 tests automatisés réussis** lors de la dernière exécution, dont les contrôles d’accès, la confidentialité des notes et les droits de décision.
- **OCR sur trois scans fictifs nets** avec 12 champs détectés sur 12, dont 10 reproduits à l’identique. Les écarts concernent un accent et un tiret. Le détail figure dans [l’évaluation OCR](eval/dossier/ocr.md).
- **Démo locale** relancée et réponse du serveur vérifiée sur [le port 8001](http://127.0.0.1:8001/demo/). Le dernier contrôle a confirmé la disponibilité de l’action d’autorisation d’envoi. Un nouvel essai du rapport complet dans le navigateur reste à faire.
- **Git.** La base locale est au commit `79dec7b`. Les développements de Hicham sont présents dans la copie de travail et restent à enregistrer sur une branche puis à partager.

## Travail restant

1. **Valider le parcours complet dans le navigateur.** Soumettre un dossier fictif avec du texte et plusieurs formats de pièces. Ouvrir le rapport côté consultant, vérifier les compteurs et les téléchargements, demander un complément, reprendre le dossier côté candidat, puis consigner l’autorisation d’envoi. Vérifier aussi l’affichage sur mobile.
2. **Améliorer le rapport et la lecture des pièces.** Conserver les originaux dans le parcours Canada–Études. Définir les champs utiles par type de pièce pour les parcours généraux, mesurer la qualité d’extraction sur un corpus annoté plus large et signaler clairement les lectures à vérifier.
3. **Étendre les règles par destination et motif.** Choisir les prochains parcours avec le binôme. Vérifier leurs exigences sur les sources officielles, documenter les exceptions et tester chaque règle avant de l’afficher comme contrôle automatisé.
4. **Partager et intégrer le travail.** Créer une branche dédiée, enregistrer les fichiers de la partie Dossier et de l’interface, pousser la branche et ouvrir une pull request. Convenir avec le collègue des échanges entre Dossier et son orchestrateur. Aligner les documents de cadrage avec le périmètre élargi.
5. **Préparer le rendu.** Vérifier le lancement sur les deux ordinateurs, élargir les scénarios d’évaluation, mesurer la justesse des résultats, le temps et le coût, puis préparer les chapitres de Hicham, la vidéo de secours et la soutenance.

## Historique

### 12 novembre 2026 — Brouillon du formulaire général

- Le candidat peut enregistrer les réponses de son formulaire multi-pays, puis les reprendre après reconnexion. Le brouillon est lié au compte, accessible au candidat et supprimé lors d’une transmission réussie.
- Les pièces sélectionnées restent dans le formulaire ouvert. Après reconnexion, elles doivent être sélectionnées à nouveau.
- 46 tests réussis, dont l’isolation du brouillon par compte et sa suppression après transmission. Syntaxe JavaScript et diff vérifiés. La reprise dans le navigateur reste à valider.
- Prochaine action. Publier la branche de la partie Dossier, puis rejouer le parcours complet côté candidat et consultant.

### 11 novembre 2026 — Accueil Consultant

- Ajout d’un tableau de bord pour les consultants connectés. Il compte les dossiers accessibles à examiner, en attente de complément et clôturés. Les cartes filtrent la liste qui donne accès au rapport et aux actions.
- Syntaxe JavaScript et différences Git vérifiées. L’essai de navigation avec des dossiers dans chaque statut reste à faire pendant la validation du parcours complet.

### 11 novembre 2026

- Création du CRH et consolidation de l’état de la partie Dossier.
- Dernière évolution recensée. Le consultant peut examiner un rapport par dossier, consigner des observations internes et motiver une autorisation d’envoi. La décision est visible côté candidat.
- Prochaine action. Rejouer le scénario complet dans le navigateur et préparer la branche de partage.
