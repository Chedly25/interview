# 🚀 Guide de Déploiement - Assistant Automobile

## 📋 Options de Déploiement

### 🥇 **Option 1: Railway (Recommandé pour débuter)**

**Avantages:** Déploiement automatique, domaine inclus, base de données managée
**Coût:** Gratuit (limite 500h/mois), puis $5-20/mois

#### Étapes:
1. **Créer un compte sur [Railway](https://railway.app)**
2. **Connecter votre repository GitHub**
3. **Déployer:**
   ```bash
   # Connecter Railway CLI
   npm install -g @railway/cli
   railway login
   
   # Initialiser le projet
   railway init
   
   # Déployer
   railway up
   
   # Configurer les variables d'environnement
   railway variables set ANTHROPIC_API_KEY=your_key_here
   ```

#### Configuration Railway:
- Utilise `railway.json` (déjà créé)
- Base de données PostgreSQL automatique
- SSL/HTTPS inclus
- Domaine: `https://your-app.railway.app`

---

### 🥈 **Option 2: DigitalOcean App Platform**

**Avantages:** Performances stables, base de données managée
**Coût:** $12/mois minimum

#### Étapes:
1. **Créer un compte [DigitalOcean](https://digitalocean.com)**
2. **Utiliser App Platform:**
   - Importer depuis GitHub
   - Utiliser `.do/app.yaml` (déjà créé)
   - Configurer les variables d'environnement
3. **Base de données:** PostgreSQL managée ($15/mois)

---

### 🥉 **Option 3: VPS (Contrôle total)**

**Avantages:** Contrôle complet, idéal pour scraping intensif
**Coût:** $5-10/mois (Hetzner, DigitalOcean, Linode)

#### Configuration VPS:

1. **Créer un serveur Ubuntu 22.04**
2. **Installation initiale:**
   ```bash
   # Connexion SSH
   ssh root@your-server-ip
   
   # Mise à jour système
   apt update && apt upgrade -y
   
   # Installation Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   
   # Installation Docker Compose
   apt install docker-compose-plugin -y
   
   # Installation Nginx et Certbot
   apt install nginx certbot python3-certbot-nginx -y
   ```

3. **Clonage et configuration:**
   ```bash
   # Cloner le projet
   git clone https://github.com/your-username/automotive-assistant.git
   cd automotive-assistant
   
   # Configuration production
   cp .env.production .env
   nano .env  # Modifier avec vos vraies valeurs
   
   # Générer certificats SSL
   certbot --nginx -d yourdomain.com
   
   # Déploiement
   chmod +x deploy.sh
   ./deploy.sh production
   ```

---

## 🔧 **Configuration Production**

### Variables d'Environnement Requises:
```bash
# API Claude (OBLIGATOIRE)
ANTHROPIC_API_KEY=sk-ant-api03-xxxx

# Base de données
POSTGRES_DB=automotive_assistant
POSTGRES_USER=automotive_user  
POSTGRES_PASSWORD=secure_password_123

# Domaine
API_URL=https://yourdomain.com
NEXT_PUBLIC_API_URL=https://yourdomain.com
```

### SSL/HTTPS:
```bash
# Pour VPS avec Let's Encrypt
certbot --nginx -d yourdomain.com

# Renouvellement automatique
echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
```

---

## 📊 **Monitoring et Maintenance**

### Logs et Debugging:
```bash
# Voir tous les logs
docker-compose -p automotive-assistant logs -f

# Logs spécifiques
docker-compose -p automotive-assistant logs backend
docker-compose -p automotive-assistant logs frontend

# Statut des services
docker-compose -p automotive-assistant ps
```

### Scraper Automatique:
```bash
# Cron job (toutes les 30 minutes)
*/30 * * * * cd /path/to/automotive-assistant && docker-compose --profile scraper run --rm scraper

# Test manuel
docker-compose --profile scraper run scraper
```

### Backup Base de Données:
```bash
# Backup PostgreSQL
docker-compose exec db pg_dump -U $POSTGRES_USER $POSTGRES_DB > backup.sql

# Restauration
docker-compose exec -T db psql -U $POSTGRES_USER $POSTGRES_DB < backup.sql
```

---

## 🔒 **Sécurité Production**

### Checklist Sécurité:
- ✅ HTTPS obligatoire (certificats SSL)
- ✅ Rate limiting (configuré dans nginx.conf)
- ✅ Variables d'environnement sécurisées
- ✅ Base de données avec mot de passe fort
- ✅ Firewall configuré (ports 80, 443, 22 uniquement)
- ✅ Mises à jour automatiques système

### Configuration Firewall:
```bash
# UFW (Ubuntu)
ufw allow 22    # SSH
ufw allow 80    # HTTP
ufw allow 443   # HTTPS  
ufw enable
```

---

## 💰 **Estimation des Coûts**

| Service | Gratuit | Basique | Production |
|---------|---------|---------|------------|
| **Railway** | 500h/mois | $5/mois | $20/mois |
| **DigitalOcean** | - | $12/mois | $30/mois |
| **VPS + SSL** | - | $5/mois | $10/mois |
| **Claude API** | $0 | $10/mois | $50/mois |

### Recommandations par Usage:
- **Test/Demo:** Railway gratuit
- **Production légère:** Railway $5/mois
- **Production intensive:** VPS $10/mois
- **Enterprise:** DigitalOcean $30/mois

---

## 🚀 **Déploiement Rapide (Railway)**

```bash
# 1. Installer Railway CLI
npm install -g @railway/cli

# 2. Login
railway login

# 3. Déployer
railway init
railway up

# 4. Variables d'environnement
railway variables set ANTHROPIC_API_KEY=your_key_here

# 5. Accéder à votre site
railway open
```

Votre site sera accessible en quelques minutes à une adresse comme:
`https://automotive-assistant-production.railway.app`

---

## 📞 **Support**

Si vous rencontrez des problèmes:
1. Vérifiez les logs: `docker-compose logs -f`
2. Testez la santé de l'API: `curl https://yourdomain.com/health`
3. Vérifiez les variables d'environnement
4. Consultez la documentation des plateformes