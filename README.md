# 🚗 Assistant Automobile Français

Une application web moderne pour analyser les voitures d'occasion avec l'intelligence artificielle Claude.

## 📋 Fonctionnalités

- **Scraping automatique** : Récupère les annonces LeBonCoin avec pagination
- **Interface moderne** : Frontend Next.js 14 avec Tailwind CSS et mode sombre
- **Analyse IA** : Utilise Claude pour évaluer les prix et détecter les problèmes
- **Filtres avancés** : Prix, département, type de carburant
- **Base de données** : SQLite avec SQLAlchemy pour la persistance
- **Docker** : Déploiement facile avec Docker Compose

## 🚀 Installation Rapide

### Prérequis
- Docker et Docker Compose
- Clé API Anthropic (Claude)

### Étapes

1. **Cloner le projet**
```bash
git clone <repository-url>
cd automotive-assistant
```

2. **Configuration**
```bash
cp .env.example .env
# Modifier .env avec votre clé API Anthropic
```

3. **Lancement**
```bash
docker-compose up -d
```

4. **Accès**
- Frontend: http://localhost:3000
- API Backend: http://localhost:8000
- Documentation API: http://localhost:8000/docs

## 📁 Structure du Projet

```
automotive-assistant/
├── backend/                 # API FastAPI
│   ├── main.py             # Points d'API principaux
│   ├── database.py         # Modèles SQLAlchemy
│   ├── scraper.py          # Scraper LeBonCoin
│   └── requirements.txt    # Dépendances Python
├── frontend/               # Interface Next.js
│   ├── app/               # Pages App Router
│   ├── components/        # Composants React
│   └── package.json       # Dépendances Node.js
├── docker-compose.yml     # Configuration Docker
└── README.md
```

## 🔧 Développement Local

### Backend (FastAPI)
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev
```

### Scraper Manuel
```bash
cd backend
python scraper.py
```

## 📊 API Endpoints

- `GET /api/cars` - Liste des voitures avec filtres
- `GET /api/cars/{id}` - Détails d'une voiture
- `POST /api/cars/{id}/analyze` - Analyse IA avec Claude
- `GET /health` - Statut de l'API

## 🤖 Analyse IA Claude

L'analyse automatique fournit :
- **Évaluation du prix** : Correct, élevé ou bon marché
- **Signaux d'alarme** : Problèmes potentiels détectés
- **Conseils de négociation** : Stratégies personnalisées
- **Note globale** : Score sur 10 avec recommandation

## 🔄 Scraper LeBonCoin

### Fonctionnalités
- Respect des limites de taux (2 requêtes/seconde)
- Déduplication automatique
- Gestion de la pagination (max 100 voitures)
- Extraction complète des métadonnées

### Programmation
```bash
# Cron pour scraper toutes les 30 minutes
*/30 * * * * docker-compose run --rm scraper
```

## 🐳 Déploiement Docker

### Production
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Scraper Schedulé
```bash
docker-compose --profile scraper run scraper
```

## 🛠️ Configuration Avancée

### Variables d'Environnement

| Variable | Description | Défaut |
|----------|-------------|---------|
| `DATABASE_URL` | URL base de données | `sqlite:///./data/cars.db` |
| `ANTHROPIC_API_KEY` | Clé API Claude | Requis |
| `NEXT_PUBLIC_API_URL` | URL API frontend | `http://localhost:8000` |
| `LEBONCOIN_DEPARTMENT` | Département scraping | `69` |
| `MAX_CARS_PER_RUN` | Limite scraper | `100` |

### Départements Supportés
- 01 - Ain
- 69 - Rhône (défaut)
- 75 - Paris
- 13 - Bouches-du-Rhône
- 33 - Gironde
- Et plus...

## 📱 Interface Utilisateur

### Page Principale
- Grille de cartes voitures responsive
- Filtres prix et département
- Tri par prix, année, kilométrage
- Pagination infinie

### Page Détail
- Galerie d'images interactive
- Informations complètes
- Bouton analyse IA
- Lien vers LeBonCoin

### Mode Sombre
Interface complètement adaptée avec basculement automatique.

## 🔍 Dépannage

### Problèmes Communs

**Erreur de connexion API**
```bash
# Vérifier les services
docker-compose ps
# Vérifier les logs
docker-compose logs backend
```

**Scraper ne fonctionne pas**
```bash
# Tester manuellement
docker-compose exec backend python scraper.py
```

**Images ne se chargent pas**
Vérifier la configuration des domaines dans `next.config.js`

## 📈 Monitoring

### Logs
```bash
# Tous les services
docker-compose logs -f

# Service spécifique
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Métriques
- Base de données: `/app/data/cars.db`
- Logs: Intégrés Docker
- Santé API: `/health`

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature
3. Commit les changements
4. Push vers la branche
5. Créer une Pull Request

## 📄 Licence

MIT License - voir le fichier LICENSE pour les détails.

## 🌐 Déploiement en Production

Votre application peut être déployée sur plusieurs plateformes:

### 🚀 **Déploiement Rapide (Railway - Recommandé)**
```bash
npm install -g @railway/cli
railway login
railway init
railway up
railway variables set ANTHROPIC_API_KEY=your_key_here
```

### 🔧 **Autres Options**
- **DigitalOcean App Platform** - $12/mois
- **VPS avec Docker** - $5-10/mois
- **Railway** - Gratuit puis $5-20/mois

📖 **Guide complet:** Voir [DEPLOYMENT.md](./DEPLOYMENT.md)

## 🎯 Roadmap

- [ ] Authentification utilisateur
- [ ] Favoris et alertes
- [ ] Comparaison de voitures
- [ ] Export PDF des analyses
- [ ] Intégration d'autres sites
- [ ] API mobile
- [ ] Notifications push