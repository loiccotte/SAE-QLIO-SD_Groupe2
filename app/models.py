"""
Modeles SQLAlchemy — Correspondance avec la base MES4 (MariaDB).

Ce module definit les 10 modeles ORM utilises par l'application.
La base MES4 contient 64 tables au total ; seules celles necessaires
au calcul des KPIs sont modelisees ici.

Correspondance Modele <-> Table BDD
====================================

+------------------+------------------------+--------+-----------------------------------------------+
| Modele Python    | Table MariaDB          | Lignes | Description                                   |
+------------------+------------------------+--------+-----------------------------------------------+
| Order            | tblfinorder            |    189 | Ordres de fabrication (OF)                     |
| OrderPosition    | tblfinorderpos         |    411 | Pieces produites par OF                        |
| Step             | tblfinstep             |   1460 | Etapes de production terminees                 |
| MachineReport    | tblmachinereport       |  10126 | Etats machine horodates (event-driven)         |
| ResourceOperation| tblresourceoperation   |    142 | Capacites et temps nominaux par machine/op     |
| Resource         | tblresource            |     12 | Machines de la ligne (12 dont 8 reelles)       |
| PartsReport      | tblpartsreport         |   1191 | Rapports de detection de pieces                |
| Buffer           | tblbuffer              |     10 | Zones de stockage (ASRS, buffers)              |
| BufferPosition   | tblbufferpos           |     77 | Positions individuelles dans les buffers       |
| ErrorCode        | tblerrorcodes          |      4 | Codes erreur de reference                      |
+------------------+------------------------+--------+-----------------------------------------------+

Relations principales :
- Order 1──N OrderPosition  (via ONo)
- OrderPosition ──> Step    (via ONo + OPos)
- Step ──> Resource         (via ResourceID)
- MachineReport ──> Resource(via ResourceID)
- PartsReport ──> Resource  (via ResourceID)
- Buffer 1──N BufferPosition(via ResourceId + BufNo)

Notes sur les donnees :
- Les ResourceID reels de production sont 1 a 8 (exclusion de 0, 9, 10, 90).
- ElectricEnergyReal et CompressedAirReal sont toujours a 0 dans le dump.
- Les donnees couvrent 2016-2025 (sessions de test, non continues).
"""

from . import db


# ============================================================================
# Production — Ordres de fabrication
# ============================================================================

class Order(db.Model):
    """Ordre de fabrication (OF).

    Table source : ``tblfinorder`` (189 lignes)

    Chaque OF represente une commande de production. Il contient les dates
    planifiees et reelles de debut/fin, ainsi que l'etat de l'ordre.

    Utilise par : KPI 7 (Lead Time)
    """
    __tablename__ = 'tblfinorder'

    ONo          = db.Column(db.Integer, primary_key=True)       # Numero d'ordre (PK)
    PlannedStart = db.Column(db.DateTime)                        # Debut planifie
    PlannedEnd   = db.Column(db.DateTime)                        # Fin planifiee
    Start        = db.Column(db.DateTime)                        # Debut reel
    End          = db.Column(db.DateTime)                        # Fin reelle
    CNo          = db.Column(db.Integer)                         # Numero client
    State        = db.Column(db.Integer)                         # Etat (3 = termine)
    Enabled      = db.Column(db.Boolean)                         # Actif oui/non

    positions = db.relationship('OrderPosition', backref='order', lazy='dynamic')


class OrderPosition(db.Model):
    """Piece produite au sein d'un ordre de fabrication.

    Table source : ``tblfinorderpos`` (411 lignes)

    Chaque position correspond a une piece physique. Le champ ``Error``
    indique si la piece est non-conforme.

    Utilise par : KPI 1 (OEE-Qualite), KPI 3 (Cadence), KPI 5 (Non-conformite)
    """
    __tablename__ = 'tblfinorderpos'

    ONo          = db.Column(db.Integer, db.ForeignKey('tblfinorder.ONo'), primary_key=True)
    OPos         = db.Column(db.Integer, primary_key=True)       # Position dans l'OF
    PlannedStart = db.Column(db.DateTime)
    PlannedEnd   = db.Column(db.DateTime)
    Start        = db.Column(db.DateTime)                        # Debut reel
    End          = db.Column(db.DateTime)                        # Fin reelle
    WPNo         = db.Column(db.Integer)                         # Numero de workpiece
    StepNo       = db.Column(db.Integer)                         # Derniere etape
    State        = db.Column(db.Integer)                         # Etat
    ResourceID   = db.Column(db.Integer)                         # Derniere machine
    OpNo         = db.Column(db.Integer)                         # Derniere operation
    PNo          = db.Column(db.Integer)                         # Numero de piece
    Error        = db.Column(db.Boolean)                         # 0 = OK, 1 = non-conforme
    OrderPNo     = db.Column(db.Integer)                         # PNo dans l'ordre


# ============================================================================
# Production — Etapes de fabrication
# ============================================================================

class Step(db.Model):
    """Etape de production terminee.

    Table source : ``tblfinstep`` (1460 lignes)

    Chaque ligne represente une operation executee par une machine sur une
    piece. Contient les mesures d'energie (theoriques et reelles) et le
    flag d'erreur.

    Utilise par :
    - KPI 1 (OEE-Performance) : comparaison temps nominal vs reel
    - KPI 4 (Temps de cycle) : AVG(End - Start) pour OpNo < 200
    - KPI 8 (Attente buffer) : OpNo entre 210 et 215
    - KPI 9-10 (Energie) : ElectricEnergyCalc, CompressedAirCalc
    """
    __tablename__ = 'tblfinstep'

    StepNo             = db.Column(db.Integer, primary_key=True)  # Numero d'etape
    ONo                = db.Column(db.Integer, primary_key=True)  # Numero d'ordre
    OPos               = db.Column(db.Integer, primary_key=True)  # Position dans l'OF
    WPNo               = db.Column(db.Integer)                    # Workpiece
    OpNo               = db.Column(db.Integer)                    # Code operation (< 200 = prod, 210-215 = buffer)
    Description        = db.Column(db.String(255))                # Description textuelle
    Start              = db.Column(db.DateTime)                   # Debut reel
    End                = db.Column(db.DateTime)                   # Fin reelle
    ResourceID         = db.Column(db.Integer)                    # Machine executante
    ElectricEnergyCalc = db.Column(db.Integer)                    # Energie electrique theorique (mWs)
    ElectricEnergyReal = db.Column(db.Integer)                    # Energie electrique reelle (toujours 0)
    CompressedAirCalc  = db.Column(db.Integer)                    # Air comprime theorique (mNl)
    CompressedAirReal  = db.Column(db.Integer)                    # Air comprime reel (toujours 0)
    ErrorStep          = db.Column(db.Boolean)                    # True si erreur durant l'etape
    Active             = db.Column(db.Boolean)                    # Etape active
    StaffId            = db.Column(db.Integer)                    # Operateur


# ============================================================================
# Machines — Etats et capacites
# ============================================================================

class MachineReport(db.Model):
    """Etat machine horodate (event-driven).

    Table source : ``tblmachinereport`` (10 126 lignes)

    Chaque ligne est un *evenement* : un changement d'etat d'une machine
    a un instant donne. La duree d'un etat se calcule par difference avec
    le timestamp du prochain evenement (meme ResourceID).

    Utilise par :
    - KPI 1 (OEE-Disponibilite) : ratio temps Busy / temps total
    - KPI 2 (Utilisation machine) : idem, par machine
    - KPI 6 (Temps detection) : delta entre ErrorL0/L2 et arret Busy
    """
    __tablename__ = 'tblmachinereport'

    ResourceID   = db.Column(db.Integer, primary_key=True)       # Machine
    TimeStamp    = db.Column(db.DateTime, primary_key=True)      # Horodatage
    ID           = db.Column(db.Integer, primary_key=True)       # Identifiant unique
    AutomaticMode = db.Column(db.Boolean)                        # Mode automatique
    ManualMode   = db.Column(db.Boolean)                         # Mode manuel
    Busy         = db.Column(db.Boolean)                         # Machine en production
    Reset        = db.Column(db.Boolean)                         # Reset en cours
    ErrorL0      = db.Column(db.Boolean)                         # Erreur niveau 0
    ErrorL1      = db.Column(db.Boolean)                         # Erreur niveau 1 (jamais active)
    ErrorL2      = db.Column(db.Boolean)                         # Erreur niveau 2


class ResourceOperation(db.Model):
    """Capacite et temps nominal par couple machine/operation.

    Table source : ``tblresourceoperation`` (142 lignes)

    Definit les valeurs de reference pour chaque operation sur chaque
    machine : temps de travail nominal, temps d'offset, et consommation
    theorique (electrique + air comprime).

    Utilise par :
    - KPI 1 (OEE-Performance) : WorkingTime comme temps nominal
    - KPI 9-10 (Energie) : ElectricEnergy, CompressedAir
    """
    __tablename__ = 'tblresourceoperation'

    ResourceID    = db.Column(db.Integer, primary_key=True)      # Machine
    OpNo          = db.Column(db.Integer, primary_key=True)      # Code operation
    WorkingTime   = db.Column(db.Integer)                        # Temps nominal (secondes)
    OffsetTime    = db.Column(db.Integer)                        # Temps d'offset (secondes)
    ElectricEnergy = db.Column(db.Integer)                       # Energie theorique (mWs)
    CompressedAir  = db.Column(db.Integer)                       # Air comprime theorique (mNl)


class Resource(db.Model):
    """Machine de la ligne de production.

    Table source : ``tblresource`` (12 lignes)

    Liste des 12 machines. Seules les machines 1 a 8 sont reelles ;
    les IDs 0, 9, 10, 90 sont des machines de test ou virtuelles.

    Utilise par : tous les KPIs (resolution des noms de machines).
    """
    __tablename__ = 'tblresource'

    ResourceID   = db.Column(db.Integer, primary_key=True)       # ID machine
    ResourceName = db.Column(db.String(255))                     # Nom court
    Description  = db.Column(db.String(255))                     # Description longue


# ============================================================================
# Qualite — Detection de pieces
# ============================================================================

class PartsReport(db.Model):
    """Rapport de detection de piece.

    Table source : ``tblpartsreport`` (1 191 lignes)

    Chaque ligne est un evenement de detection d'une piece par une
    machine. Le champ ErrorID indique si la piece est defectueuse
    (0 = OK, autre = code erreur).

    Utilise par : KPI 5 (Non-conformite) — taux d'erreur par machine.

    Note : les ErrorID 5050 et 99 n'ont pas de correspondance dans
    tblerrorcodes (anomalie connue).
    """
    __tablename__ = 'tblpartsreport'

    ResourceID = db.Column(db.Integer, primary_key=True)         # Machine
    TimeStamp  = db.Column(db.DateTime, primary_key=True)        # Horodatage
    ID         = db.Column(db.Integer, primary_key=True)         # Identifiant unique
    PNo        = db.Column(db.Integer)                           # Numero de piece
    ErrorID    = db.Column(db.Integer)                           # 0 = OK, sinon code erreur


# ============================================================================
# Stockage — Buffers
# ============================================================================

class Buffer(db.Model):
    """Zone de stockage (buffer ou ASRS).

    Table source : ``tblbuffer`` (10 lignes)

    Chaque buffer a une capacite definie par Rows x Columns x max(Sides, 1).

    Utilise par : KPI 11 (Occupation buffers), KPI 12 (Variation stock).
    """
    __tablename__ = 'tblbuffer'

    ResourceId  = db.Column(db.Integer, primary_key=True)        # Machine associee
    BufNo       = db.Column(db.Integer, primary_key=True)        # Numero de buffer
    Description = db.Column(db.String(255))                      # Nom descriptif
    Type        = db.Column(db.Integer)                          # Type de buffer
    Sides       = db.Column(db.Integer)                          # Nombre de cotes
    Rows        = db.Column(db.Integer)                          # Nombre de rangees
    Columns     = db.Column(db.Integer)                          # Nombre de colonnes


class BufferPosition(db.Model):
    """Position individuelle dans un buffer.

    Table source : ``tblbufferpos`` (77 lignes)

    Chaque position peut contenir une piece (PNo > 0) ou etre vide (PNo = 0).
    Le champ Quantity est utilise pour le calcul de variation de stock.

    Utilise par : KPI 11 (Occupation buffers), KPI 12 (Variation stock).
    """
    __tablename__ = 'tblbufferpos'

    ResourceId = db.Column(db.Integer, primary_key=True)         # Machine associee
    BufNo      = db.Column(db.Integer, primary_key=True)         # Numero de buffer
    BufPos     = db.Column(db.Integer, primary_key=True)         # Position dans le buffer
    PNo        = db.Column(db.Integer)                           # Numero de piece (0 = vide)
    Quantity   = db.Column(db.Integer)                           # Quantite
    TimeStamp  = db.Column(db.DateTime)                          # Dernier horodatage
    ONo        = db.Column(db.Integer)                           # Ordre associe
    OPos       = db.Column(db.Integer)                           # Position dans l'ordre


# ============================================================================
# Reference — Codes erreur
# ============================================================================

class ErrorCode(db.Model):
    """Code erreur de reference.

    Table source : ``tblerrorcodes`` (4 lignes)

    Table de reference decrivant les codes erreur possibles.
    Note : certains ErrorID de tblpartsreport (5050, 99) n'y figurent pas.
    """
    __tablename__ = 'tblerrorcodes'

    ErrorId     = db.Column(db.Integer, primary_key=True)        # Code erreur
    Description = db.Column(db.String(255))                      # Description longue
    Short       = db.Column(db.String(255))                      # Description courte
