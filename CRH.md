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

### Comptes fictifs pour la démo React

- Deux comptes de test ont été créés dans la base SQLite locale, un par rôle. La connexion et le rôle de chaque compte ont été vérifiés sur le port 8002.
- Le compte candidat a été préparé avec le statut vérifié pour permettre les essais du parcours Dossier. La vérification d’identité reste un scénario de test distinct.

### Version fusionnée — Orientation et examen des dossiers

- Le portail React propose un dialogue guidé sur le motif, la région, la langue, les contacts et la disposition à apprendre une autre langue. Les suggestions exposent leurs raisons et préremplissent la destination et le motif.
- Le formulaire React enregistre la description du projet et le coût du trajet pour Canada–Études. Il exploite la lecture des spécimens PDF et TXT existante et transmet les champs éditables au consultant. Le rapport affiche également les sources et compteurs des critères.
- Le candidat peut répondre à une demande de complément dans le portail React. La demande revient dans la file d’examen et le complément est visible côté consultant.
- Vérifications locales. 69 tests pour la version fusionnée, 46 pour le portail historique, tests de simulation et compilation React réussis. Le test ciblé confirme la lecture d’un spécimen, sa présence dans le dossier consultant et le cycle de complément. Le serveur React compilé répond sur le port 8002.
- Prochaines tâches. Rejouer le parcours dans le navigateur, unifier le stockage des pièces originales entre les portails, étendre l’extraction aux CV et attestations génériques, puis évaluer sur des dossiers fictifs annotés plus variés. Les anciens dossiers restent dans leurs espaces respectifs.

### 12 novembre 2026 — Relance de la démo

- Le serveur local était arrêté. Après relance, la page de démo répond avec un statut HTTP 200 et l’API de sauvegarde du brouillon est disponible.
- Prochaine vérification. Reprendre un brouillon après reconnexion depuis le navigateur.

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

### 18 novembre 2026 — Formulaire et orientation

- Le formulaire recueille des informations communes et des détails propres au motif. Le candidat peut transmettre son dossier sans destination arrêtée.
- Le chatbot accepte des préférences facultatives. Le rapport consultant reprend les informations fournies, les points à compléter et les destinations à explorer. Les vérifications automatisées d’admissibilité couvrent le parcours Canada–Études.
- Prochaine action. Ajouter des critères officiels par pays et motif, puis valider les rapports avec un consultant.

### 18 novembre 2026 — Entretien en texte libre et dossier par étapes

- Le formulaire React est organisé en cinq étapes. Il couvre le projet, le parcours, la démarche envisagée, le financement et l’installation, puis la relecture avant transmission.
- L’entretien demande six réponses libres, peut demander une précision sur le budget et attend une confirmation explicite avant d’afficher les pistes. Le consultant peut relire l’entretien depuis le dossier transmis.
- Le classement local exploite les préférences linguistiques et géographiques, les contacts identifiés et certaines exclusions explicites. Les autres éléments sont fournis au consultant pour examen.
- L’accueil sert l’interface React lorsque celle-ci a été compilée. La démo historique reste accessible sur /demo/.
- Prochaine action. Ajouter les justificatifs réels par démarche dans le portail React et élargir les critères officiels de compatibilité.

### Formulaire de démonstration

- Tous les champs d’une nouvelle demande sont facultatifs. Le candidat peut parcourir les cinq étapes à vide et utiliser le bouton final pour transmettre sa demande.

### Entretien d’orientation — Réponses prises en compte

- Le chatbot relève les informations réparties dans les messages libres, adapte les relances et présente les éléments reconnus avant confirmation. Les langues déjà indiquées ne sont pas redemandées.
- Exemple vérifié. Un candidat qui indique trois langues et souhaite rester proche du Maroc peut signaler qu’il n’a rien d’autre à ajouter, relire son récapitulatif, puis obtenir des pistes fondées sur les préférences reconnues.
- Le message de test qui indique que ce sont les seules informations disponibles mène directement au récapitulatif.

### Livraison P2 — Canada, permis d’études

- Onze contrôles sourcés dans le parcours Dossier. Les trois nouveaux contrôles portent sur l’explication du projet, la garde des mineurs et le séjour temporaire.
- Deux fonctions compatibles avec AgentResult permettent au futur appelant de lire les pièces, suspendre pour confirmation, puis vérifier le dossier. Le raccord dans le chef d’orchestre relève du travail commun avec P1.
- Corpus livré. 40 spécimens annotés, 30 profils fictifs et 30 cas de contradictions. Résultats locaux : 149/149 champs TXT conformes, 10/12 champs OCR reproduits exactement, 330/330 verdicts attendus et 30/30 cas de contradiction conformes. Durée observée 4,074 s et aucun appel payant pour le protocole P2.
- 75 tests réussis. Le scénario automatisé passe de la question sourcée aux trois pièces, à la checklist et à la décision du consultant. Le lancement Windows avec un environnement Python existant a répondu sur le port 8006.
- Le script de démonstration, les chapitres P2 et les 15 questions de jury sont dans eval/dossier/livrables-p2.md. Restent côté équipe la validation sur le deuxième PC, le raccord P1, la mesure V4 avec et sans le Contrôleur et les répétitions.
- Le parcours a aussi été exécuté dans Edge avec deux comptes fictifs. Vidéo de secours enregistrée dans eval/dossier/demo-p2.webm.
- Version préparée pour publication sur la branche travail/version-18-nov, avec les livrables et la vidéo P2.
