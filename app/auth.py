"""
Authentification et controle d'acces (RBAC).

Ce module gere :
- Les comptes utilisateurs (hardcodes pour la version beta)
- La connexion / deconnexion via session Flask
- Deux decorateurs de protection des routes :
  - ``@login_required`` : verifie que l'utilisateur est connecte
  - ``@role_required(min_role)`` : verifie le role minimum requis

Hierarchie des roles
=====================

+---------------+--------+-----------------------------------------------+
| Role          | Niveau | Acces                                         |
+---------------+--------+-----------------------------------------------+
| admin         |      3 | Dashboard, detail, export, administration      |
| responsable   |      2 | Dashboard, detail, export                      |
| employe       |      1 | Dashboard, detail uniquement                   |
+---------------+--------+-----------------------------------------------+

Note : les mots de passe sont stockes en clair dans ``USERS`` car il
s'agit d'une version beta / academique. En production, il faudrait
utiliser une table BDD avec hachage bcrypt/argon2.
"""

from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

bp = Blueprint('auth', __name__)

# ---------------------------------------------------------------------------
# Utilisateurs hardcodes (beta)
# A remplacer par une table BDD avec hachage de mots de passe en production
# ---------------------------------------------------------------------------
USERS: dict[str, dict] = {
    'admin': {
        'password': 'admin123',
        'role': 'admin',
        'name': 'Administrateur',
    },
    'responsable': {
        'password': 'resp123',
        'role': 'responsable',
        'name': 'Responsable Production',
    },
    'operateur': {
        'password': 'oper123',
        'role': 'employe',
        'name': 'Operateur',
    },
}

# Hierarchie des roles : plus le niveau est eleve, plus les droits sont etendus
ROLE_HIERARCHY: dict[str, int] = {
    'admin': 3,
    'responsable': 2,
    'employe': 1,
}


# ---------------------------------------------------------------------------
# Decorateurs de protection
# ---------------------------------------------------------------------------

def login_required(f):
    """Decorateur verifiant que l'utilisateur est connecte.

    Redirige vers ``/login`` si aucune session active.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def role_required(min_role: str):
    """Decorateur verifiant que l'utilisateur a le role minimum requis.

    Compare le niveau du role de l'utilisateur connecte avec le niveau
    du ``min_role`` exige. Redirige vers le dashboard avec un flash
    d'erreur si le role est insuffisant.

    Args:
        min_role: Le role minimum requis ('employe', 'responsable' ou 'admin').
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_role = session.get('role', 'employe')
            if ROLE_HIERARCHY.get(user_role, 0) < ROLE_HIERARCHY.get(min_role, 0):
                flash("Acces non autorise.", "error")
                return redirect(url_for('main.dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ---------------------------------------------------------------------------
# Routes d'authentification
# ---------------------------------------------------------------------------

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion.

    GET  : affiche le formulaire de login.
    POST : valide les identifiants et cree la session.
    """
    # Si deja connecte, rediriger vers le dashboard
    if 'user' in session:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        username = request.form.get('identifiant', '').strip()
        password = request.form.get('mot_de_passe', '')

        user = USERS.get(username)
        if user and user['password'] == password:
            session['user'] = username
            session['role'] = user['role']
            session['name'] = user['name']
            return redirect(url_for('main.dashboard'))

        flash('Identifiant ou mot de passe incorrect.', 'error')

    return render_template('login.html')


@bp.route('/logout')
def logout():
    """Deconnexion : vide la session et redirige vers le login."""
    session.clear()
    return redirect(url_for('auth.login'))
