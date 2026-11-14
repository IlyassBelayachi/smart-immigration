# Stratégie ML initiale — proposition

Aucune API payante. Exécution locale ; ressources matérielles à vérifier avant installation. Aucun entraînement lourd au démarrage.

1. Recommandation : catalogue sourcé et filtres explicites, puis score d'adéquation explicable. Une valeur inconnue reste inconnue. Pas de score d'acceptation. Comparaison par budget sur des estimations datées, avec devise, durée et périmètre des dépenses.
2. OCR : évaluer PaddleOCR préentraîné sur documents français/arabe. Mesurer taux d'erreur des caractères et exactitude des champs critiques ; correction humaine possible.
3. Classification : texte OCR, représentation TF-IDF, régression logistique de référence ; comparer éventuellement un SVM linéaire. Prévoir la catégorie inconnue et l'abstention.
4. Apprentissage supervisé de recommandations seulement après constitution de jugements pertinents. Aucun apprentissage de décisions de visa sans historique réel adapté.

Jeu documentaire : identifiant, type, langue, origine réelle anonymisée ou synthétique, famille de modèle de document, texte attendu, champs attendus, chemin du fichier, partition. Ne pas stocker de pièces personnelles dans un dépôt public.

Classes proposées : attestation de travail, certificat de scolarité, relevé bancaire, justificatif d'hébergement, autre. Ce sont des classes de recherche, pas une liste universelle de pièces exigées.

Séparer apprentissage, validation et test par famille de modèle documentaire et par personne ; les variantes d'un même document restent dans la même partition. Mesurer macro-F1, résultats par classe, matrice de confusion et taux d'abstention. Les performances synthétiques ne prouvent pas les performances réelles.

Les agents coordonneront lecture, vérification et accompagnement ; les quotas et transitions sont des règles déterministes. Prochaine livraison : premiers exemples documentaires fictifs explicitement marqués, puis pipeline de référence reproductible.
