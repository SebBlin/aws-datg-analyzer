# Document d'Architecture Technique Général (DATG)
## Application E-commerce "ShopFast"

### 1. Vue d'ensemble
**Application:** Plateforme e-commerce B2C  
**Objectif:** Vente en ligne de produits électroniques  
**Utilisateurs cibles:** 10,000 utilisateurs simultanés max  
**Région AWS:** eu-west-1 (Irlande)

### 2. Architecture Technique

#### 2.1. Composants Principaux

**Frontend:**
- Application web React.js hébergée sur S3 + CloudFront
- CDN CloudFront pour la distribution globale
- Route 53 pour le DNS

**Backend:**
- API Gateway pour l'API REST
- Lambda Functions (Node.js 18.x) pour la logique métier
  - `auth-service`: Authentification des utilisateurs
  - `product-service`: Gestion des produits
  - `order-service`: Gestion des commandes
  - `payment-service`: Intégration Stripe

**Base de données:**
- DynamoDB pour les données utilisateurs et produits
  - Table `Users`: Partition key `userId`
  - Table `Products`: Partition key `productId`, GSI sur `category`
  - Table `Orders`: Partition key `orderId`, Sort key `userId`
- RDS PostgreSQL pour les données transactionnelles
  - Instance: db.t3.medium
  - Multi-AZ: Non configuré
  - Backup: Snapshots manuels

**Stockage:**
- S3 pour les images produits
  - Bucket: `shopfast-images-prod`
  - Versioning: Activé
  - Lifecycle: Aucune politique
- Elasticache Redis pour le cache
  - Cluster: cache.t3.micro (nœud unique)
  - Utilisation: Cache de session et cache produit

#### 2.2. Sécurité

**IAM:**
- Rôle Lambda avec politiques administrateur (à revoir)
- Utilisateurs IAM pour l'équipe DevOps
- Pas de MFA activé sur les comptes root

**Réseau:**
- VPC avec 2 sous-réseaux publics
- Security Groups:
  - API Gateway: Accès public
  - RDS: Accès depuis Lambda uniquement
  - Elasticache: Accès depuis EC2 (mais pas d'EC2)
- Pas de NACLs configurés

**Chiffrement:**
- S3: Chiffrement SSE-S3 activé
- RDS: Chiffrement au repos désactivé
- Données en transit: TLS 1.2

#### 2.3. Monitoring et Logging

**CloudWatch:**
- Métriques Lambda: Durée d'exécution, erreurs
- Métriques RDS: CPU, mémoire, connexions
- Logs: Lambda logs groupés
- Pas de dashboards personnalisés

**Alerting:**
- Alarmes sur erreurs Lambda > 5%
- Pas d'alarmes sur RDS
- Pas de monitoring des coûts

#### 2.4. CI/CD

**Pipeline:**
- CodeBuild pour les builds
- CodePipeline pour le déploiement
- Déploiement sur tous les environnements simultanément
- Pas de tests automatisés

### 3. Points d'Attention Identifiés

#### 3.1. Forces
- Architecture serverless scalable
- Utilisation de services managés AWS
- Découpage en microservices
- CDN pour performances globales

#### 3.2. Faiblesses
1. **Sécurité:**
   - Rôle Lambda trop permissif
   - Pas de MFA sur compte root
   - RDS non chiffré
   - Pas de WAF sur API Gateway

2. **Fiabilité:**
   - RDS en single-AZ (risque de downtime)
   - Redis single node (pas de réplication)
   - Pas de backup automatisé RDS
   - Pas de stratégie de retry sur Lambda

3. **Performance:**
   - Pas de cache côté API Gateway
   - Pas de compression sur S3
   - Taille des Lambda limitée à 128MB

4. **Coûts:**
   - Pas de réservations pour RDS
   - Pas de monitoring des coûts
   - S3 sans lifecycle (coût stockage)

5. **Excellence Opérationnelle:**
   - Déploiement sans staging
   - Pas de tests automatisés
   - Logging basique
   - Pas de documentation runbook

### 4. Recommandations Prioritaires

#### Court terme (1-2 semaines):
1. Activer le chiffrement RDS
2. Restreindre les permissions IAM Lambda
3. Configurer MFA sur compte root
4. Activer les backups automatisés RDS

#### Moyen terme (1 mois):
1. Migrer RDS en Multi-AZ
2. Configurer Redis en cluster
3. Implémenter WAF sur API Gateway
4. Configurer CloudWatch dashboards

#### Long terme (3 mois):
1. Implémenter CI/CD avec environnements séparés
2. Ajouter des tests automatisés
3. Configurer Budgets et Cost Explorer
4. Documenter les procédures d'urgence

### 5. Métriques de Suivi

**Disponibilité:** Objectif 99.9%
**Latence:** < 200ms p95
**Coût mensuel:** Budget 5,000€
**Sécurité:** 0 vulnérabilités critiques
**Déploiements:** 1 par semaine minimum

---
*Document généré le 2024-01-15*
*Version: 1.0*
*Propriétaire: Équipe Architecture AWS*