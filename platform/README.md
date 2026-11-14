# Atlas — première plateforme locale

Ouvrir `index.html` dans un navigateur (double-clic), ou lancer `node server.cjs` depuis ce dossier puis visiter http://127.0.0.1:5173.

Sans dépendance à installer ni API payante. Police distante facultative, avec repli système. Profils de démonstration et dossiers enregistrés dans le stockage local du navigateur. L'accès direct au fichier peut être limité par la politique du navigateur ; préférer le serveur local si nécessaire.

Fonctions : profil local, catalogue filtrable de 55 destinations, création de brouillons, dépôt, quotas, accord de transmission, file FIFO, conservation, historique et notifications. Le panneau Simulation agence permet de faire avancer les dossiers et de simuler une décision pour libérer une place.

Limites : pas d'authentification sécurisée, pas de serveur de données, pas de pièce jointe, pas de ML intégré ni d'organisme connecté. Données fictives uniquement. Les rappels et expirations sont traités pendant l'utilisation. Les notifications exactes d'un jour ne sont pas rattrapées si l'application était fermée ce jour-là. Le prototype ne fournit aucun classement de chances de visa.

Tests métier : `node test.cjs`.
