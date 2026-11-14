# Règles métier

## Validé avec le porteur du projet
Entité au Maroc : réception, préparation, transmission et suivi. L'organisme désigné par le pays décide. Tous profils et motifs envisagés. Inscription obligatoire avant orientation ; orientation activée par défaut mais facultative. Profil léger pour orientation, dossier détaillé ensuite. Format exact du dépôt encore ouvert.

Plafonds simultanés par candidat : brouillon 10 ; déposée 5 ; traitement interne 5 ; prête à transmettre 5 ; file de transmission 5 ; transmise 3 ; conservation 10.

Le candidat autorise la transmission après préparation. File FIFO selon la date d'autorisation ; transmission automatique dès disponibilité. File pleine : autorisation bloquée. Conservation distincte des dossiers prêts.

Délai de réponse : un mois. Rappels plateforme à J-7, J-3 et le dernier jour, interrompus dès réponse. Refus ou silence à échéance : conservation trois mois. Accord possible pendant conservation si place disponible. Puis annulation ; suppression possible par administrateur. À l'entrée du onzième dossier conservé, suppression automatique de celui entré en conservation en premier.

## Choix proposés par l'assistant, autorisé à compléter le schéma
- Tentative d'autorisation avec file pleine : passage en conservation si le dossier était prêt ; conservation inchangée s'il y était déjà. Pas d'autorisation enregistrée. Message explicatif.
- Mois calendaires ; si le jour n'existe pas dans le mois cible, dernier jour du mois. Heure de référence Africa/Casablanca. Conservation non prolongée par une tentative bloquée.
- Accord en conservation : nouvelle vérification de validité documentaire avant envoi ; anomalie renvoyée à un humain.
- Décision finale du partenaire : accordée ou refusée, libérant une place transmise. Une demande de complément conserve cette place.
- Échec technique de transmission : dossier maintenu dans la file, sans duplication ; envoi confirmé avant changement de statut.
- Demandes annulées et closes hors des quotas actifs. Suppression réservée aux règles validées et à l'administration.
- Démonstration des échanges partenaires simulée et explicitement indiquée.

## À préciser au fil de la conception
Nationalités/résidences couvertes, mineurs, formulaires et pièces, corrections, retraits, droits administrateurs, politique de conservation des demandes closes. Les plafonds ne doivent pas empêcher d'enregistrer une réponse officielle : prévoir une prise en charge administrative des exceptions.
