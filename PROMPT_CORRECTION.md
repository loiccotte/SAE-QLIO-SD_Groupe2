# Prompt de correction — Mise en conformité avec CDC + Maquette

Utilise ce prompt tel quel avec Claude Code pour corriger le site.

---

## PROMPT

Tu vas corriger les templates HTML Flask du projet MES 4.0 (dossier `templates/`) pour les rendre **exactement conformes** au CDC (`ressources/CDC_MES4.0_V2.pdf`) et à la maquette (`ressources/Groupe_2_Rendu_23_janvier-20260123T141131Z-3-001/Groupe_2_Rendu_23_janvier/Maquette_Groupe2.pdf`).

Lis d'abord le fichier `différence.md` à la racine du projet — il liste tous les écarts à corriger avec leur priorité.

Voici les corrections à effectuer, dans cet ordre de priorité :

---

### CORRECTION 1 — Couleurs des thèmes (`base.html` + `custom.css`)

Dans `base.html`, le bloc `tailwind.config`, remplace les couleurs par les valeurs exactes du CDC (p.12) :
- `perf` : `#ff0000` (au lieu de `#dc2626`)
- `qualite` : `#38b6ff` (au lieu de `#0284c7`)
- `delai` : `#f2c0ff` (au lieu de `#db2777`)
- `energie` : `#09b200` (au lieu de `#16a34a`)
- `stock` : `#737373` (au lieu de `#52525b`)

Dans `static/css/custom.css`, vérifie que les classes `kpi-bar-*` utilisent les nouvelles couleurs. Mets à jour toutes les occurrences de ces couleurs hexadécimales dans les fichiers CSS et JS inline.

---

### CORRECTION 2 — Fond des cartes KPI avec transparence 25% (`dashboard.html`)

Le CDC (p.12) exige que chaque carte du dashboard ait un fond coloré à 25% de transparence avec la couleur de son thème (pas juste une fine barre).

Dans `dashboard.html`, pour chaque carte `<a href="...">`, remplace le fond blanc par un fond semi-transparent avec la couleur du thème :
- Performance : `background-color: rgba(255, 0, 0, 0.08)` (rouge à ~8% pour rester lisible, correspondant à "25% transparence du fond" — interprété comme fond subtil teinté, pas opaque à 25%)
- Qualité : `background-color: rgba(56, 182, 255, 0.08)`
- Délai : `background-color: rgba(242, 192, 255, 0.15)` (rose clair, légèrement plus visible)
- Énergie : `background-color: rgba(9, 178, 0, 0.08)`
- Stock : `background-color: rgba(115, 115, 115, 0.08)`

La barre colorée en haut (`h-1.5`) reste mais utilise désormais la vraie couleur du thème.

---

### CORRECTION 3 — Flèches de tendance sur le dashboard (`dashboard.html`)

Le CDC (p.12) exige des flèches ▲ (positif, `#16a637`) et ▼ (négatif, `#ff000f`) sur chaque carte du dashboard pour montrer la tendance récente.

Le backend doit exposer un champ `trend` (`'up'` / `'down'` / `'stable'`) dans chaque objet KPI passé au template.

Dans `dashboard.html`, après la valeur principale de chaque carte, ajoute :
```html
{% if kpis.oee.trend == 'up' %}
<span class="text-sm font-bold" style="color: #16a637;">▲</span>
{% elif kpis.oee.trend == 'down' %}
<span class="text-sm font-bold" style="color: #ff000f;">▼</span>
{% endif %}
```
Applique ce bloc pour les 5 cartes : `oee.trend`, `non_conformity.trend`, `lead_time.trend`, `energy.trend`, `buffer.trend`.

Dans le backend (`routes.py` ou équivalent), calcule la tendance en comparant la valeur actuelle à la valeur moyenne des N dernières occurrences.

---

### CORRECTION 4 — Position LOGOUT (`base.html`)

La maquette place le bouton LOGOUT en **bas à droite de la page**, pas dans le header.

Dans `base.html` :
1. Retire le lien `Logout` du header (section droite du header).
2. Ajoute juste avant `</body>` un bouton fixe en bas à droite :

```html
<!-- LOGOUT fixé en bas à droite -->
<div class="fixed bottom-6 right-6 z-50">
    <a href="{{ url_for('auth.logout') }}"
       class="px-5 py-2 text-xs font-semibold uppercase tracking-wide
              bg-white border border-zinc-300 rounded-lg shadow-md
              text-zinc-700 hover:bg-zinc-100 hover:text-zinc-900
              transition-colors active:scale-[0.98]">
        LOGOUT
    </a>
</div>
```

---

### CORRECTION 5 — Titre "TABLEAU DE BORD GLOBAL" (`dashboard.html`)

La maquette affiche "TABLEAU DE BORD GLOBAL" comme titre principal visible de la page dashboard.

Dans `dashboard.html`, au début du `{% block content %}`, ajoute avant les cartes :
```html
<h1 class="text-2xl font-bold tracking-tight text-zinc-900 text-center mb-8 uppercase">
    Tableau de bord global
</h1>
```

---

### CORRECTION 6 — En-tête des pages thème : titre de page au centre (`base.html`)

La maquette montre le titre de la page (ex. "QUALITÉ", "DÉLAI") au centre de l'en-tête sur les pages thème, à la place du logo T'ÉLÉFAN.

Modifie `base.html` pour permettre aux pages enfants de surcharger le centre du header. Ajoute un `{% block header_center %}` :

Dans `base.html`, remplace le centre du header par :
```html
<!-- Centre : Logo ou titre page -->
<div class="text-center">
    {% block header_center %}
    <a href="{{ url_for('main.dashboard') }}" class="inline-block">
        <h1 class="text-xl font-bold tracking-tight text-zinc-900">
            T'ÉLÉFAN
        </h1>
        <p class="text-[10px] text-zinc-400 uppercase tracking-widest -mt-0.5">MES 4.0</p>
    </a>
    {% endblock %}
</div>
```

Dans chaque page thème (`performance.html`, `qualite.html`, `energie.html`, `stock.html`, `delai.html`), surcharge ce bloc :
```html
{% block header_center %}
<h1 class="text-xl font-bold tracking-widest uppercase text-zinc-900">
    Performance
</h1>
{% endblock %}
```
(Remplacer "Performance" par le nom de la page correspondante : Qualité, Délai, Énergie, Stock)

---

### CORRECTION 7 — Séparateur breadcrumb `>` au lieu de `/`

Dans toutes les pages thème (`performance.html`, `qualite.html`, `energie.html`, `stock.html`, `delai.html`), remplace `<span class="mx-1.5 text-zinc-300">/</span>` par `<span class="mx-1.5 text-zinc-400">&gt;</span>`.

---

### CORRECTION 8 — Accents T'ÉLÉFAN (`base.html`, `login.html`, `dashboard.html`)

Remplace partout `T'ELEFAN` (sans accents) par `T'ÉLÉFAN` (avec les deux É accentués) dans les textes affichés à l'utilisateur (balises `<h1>`, `<p>`, `<title>`, placeholders, etc.).

---

### CORRECTION 9 — Bouton connexion en bleu marine (`login.html`)

Dans `login.html`, le bouton "Se connecter" et le texte logo doivent être bleu marine (cohérent avec la maquette).

Remplace sur le bouton `submit` : classe `bg-zinc-900` → `bg-[#1a3a7a]` et `hover:bg-zinc-800` → `hover:bg-[#162f63]`.

Remplace sur le `<h1>` "T'ÉLÉFAN" : classe `text-zinc-900` → style `color: #1a2b5e` (bleu marine foncé).

---

### CORRECTION 10 — Taux d'utilisation par mois sur Performance (`performance.html` + backend)

**Dans le backend** (`routes.py` ou module de calcul) :
- La fonction qui calcule `utilization` doit renvoyer `by_month` (pas `by_machine`) : grouper les données par mois (format `"Jan"`, `"Fév"`, etc.) et calculer le taux d'utilisation moyen par mois.
- Ajouter un champ `alert` sur chaque mois pour signaler les mois où la dérive dépasse 10% (barre rouge).

**Dans `performance.html`** :
- Renomme `utilData` source : `utilization.by_month` (au lieu de `by_machine`)
- Les labels x deviennent les noms de mois
- Les barres avec `alert: true` sont colorées en rouge (`#ff0000`), les autres en rouge clair (`#ffaaaa`)
- Change l'orientation : `type: 'bar'` avec `orientation: 'h'` si le CDC exige horizontal, sinon vertical par mois.

---

### CORRECTION 11 — Ligne de cadence nominale sur Cadence réelle (`performance.html` + backend)

Le CDC (p.13) exige une ligne de référence "cadence nominale" (objectif) visible sur le graphique de cadence réelle.

**Dans le backend** : ajoute `throughput.nominal` (valeur fixe de la cadence nominale, ex. 60 pièces/heure) dans les données passées au template.

**Dans `performance.html`**, dans le graphique `throughput-chart`, ajoute une `shape` de type `line` horizontale :
```javascript
shapes: [{
    type: 'line',
    x0: 0, x1: 1, xref: 'paper',
    y0: {{ throughput.nominal }}, y1: {{ throughput.nominal }},
    line: { color: '#18181b', width: 2, dash: 'dot' }
}],
annotations: [{
    x: 1, xref: 'paper', xanchor: 'right',
    y: {{ throughput.nominal }}, yanchor: 'bottom',
    text: 'Nominale',
    showarrow: false,
    font: { size: 9, color: '#18181b' }
}]
```

---

### CORRECTION 12 — Axe X temporel sur Temps de détection défaut (`qualite.html` + backend)

**Dans le backend** : la liste `detection_time.by_event` doit inclure un champ `timestamp` (heure de l'événement, format `"HH:MM"`).

**Dans `qualite.html`** : remplace `d.machine + ' #' + (i + 1)` par `d.timestamp` sur l'axe X du graphique de détection.

---

### CORRECTION 13 — Axe Y Stock variation jusqu'à 25% minimum (`stock.html`)

Dans `stock.html`, dans le graphique `stock-var-chart`, remplace :
```javascript
range: [0, 10],
```
par :
```javascript
range: [0, Math.max(25, Math.max.apply(null, svData.map(function(d) { return d.variation_pct; })) * 1.2)],
```

Ajoute également une ligne d'alerte à 20% :
```javascript
shapes: [{
    type: 'line',
    x0: 0, x1: 1, xref: 'paper',
    y0: 20, y1: 20,
    line: { color: '#ef4444', width: 1.5, dash: 'dash' }
}],
annotations: [{
    x: 1, xref: 'paper', xanchor: 'right',
    y: 20, yanchor: 'bottom',
    text: 'Alerte 20%',
    showarrow: false,
    font: { size: 9, color: '#ef4444' }
}]
```

---

### CORRECTION 14 — Alerte Énergie sur le dashboard (`dashboard.html` + backend)

Le CDC exige une alerte ⚠ sur la carte Énergie si dérive > 10%/semaine.

**Dans le backend** : calcule `kpis.energy.status` (`'normal'` / `'warning'` / `'critical'`) en comparant la consommation actuelle à la semaine précédente.

**Dans `dashboard.html`**, dans la carte Énergie, ajoute le bloc d'alerte identique aux autres cartes :
```html
{% if kpis.energy.status != 'normal' %}
<span class="alert-blink">
    <svg class="w-5 h-5" style="color: #09b200;" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
    </svg>
</span>
{% endif %}
```

---

### CORRECTION 15 — Supprimer les sections "Résumé" inutiles (`energie.html`, `stock.html`)

La maquette ne montre pas de section résumé sur les pages Énergie et Stock.

Dans `energie.html` : supprime le bloc `<div class="mt-6 bg-white ...">` (le résumé Énergie par unité / Air comprimé par unité).
Dans `stock.html` : supprime le bloc `<div class="mt-6 bg-white ...">` (le résumé Taux occupation global / Nombre de buffers / Alerte).

---

### CORRECTION 16 — Export avec filtre de période (`base.html` + backend)

Le CDC (p.11) exige un filtre de période dans l'export : "Année → Mois → Jour → Heure".

**Dans `base.html`**, dans le dropdown d'export, remplace le contenu par :
```html
<p class="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-3">Période</p>
<div class="grid grid-cols-2 gap-2 mb-3">
    <select id="export-year" class="text-xs border border-zinc-200 rounded-lg px-2 py-1.5 bg-zinc-50">
        <option value="">Année</option>
        <!-- Options générées par JS -->
    </select>
    <select id="export-month" class="text-xs border border-zinc-200 rounded-lg px-2 py-1.5 bg-zinc-50">
        <option value="">Mois</option>
        <option value="1">Janvier</option>…<option value="12">Décembre</option>
    </select>
    <select id="export-day" class="text-xs border border-zinc-200 rounded-lg px-2 py-1.5 bg-zinc-50">
        <option value="">Jour</option>
        <!-- 1-31 générés par JS -->
    </select>
    <select id="export-hour" class="text-xs border border-zinc-200 rounded-lg px-2 py-1.5 bg-zinc-50">
        <option value="">Heure</option>
        <!-- 0-23 générés par JS -->
    </select>
</div>
<p class="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-3">Format</p>
<div class="flex gap-2 mb-4">
    <button onclick="doExport('pdf')" …>PDF</button>
    <button onclick="doExport('excel')" …>Excel</button>
</div>
```

**Modifie `doExport(format)`** pour inclure les paramètres de période dans l'URL :
```javascript
function doExport(format) {
    var params = new URLSearchParams();
    var year = document.getElementById('export-year').value;
    var month = document.getElementById('export-month').value;
    var day = document.getElementById('export-day').value;
    var hour = document.getElementById('export-hour').value;
    if (year) params.set('year', year);
    if (month) params.set('month', month);
    if (day) params.set('day', day);
    if (hour) params.set('hour', hour);
    window.location.href = '/export/' + format + (params.toString() ? '?' + params.toString() : '');
    document.getElementById('export-modal').classList.add('hidden');
}
```

**Dans le backend** (`export_routes.py` ou équivalent) : lire les paramètres `year`, `month`, `day`, `hour` dans `request.args` et filtrer les données SQL en conséquence avant de générer le PDF/Excel.

---

### ORDRE D'EXÉCUTION RECOMMANDÉ

1. Commence par les corrections purement CSS/HTML qui n'impactent pas le backend : **1, 2, 4, 5, 6, 7, 8, 9, 13, 15**
2. Ensuite les corrections qui nécessitent des ajouts dans les templates + modifications backend légères : **3, 10, 11, 12, 14**
3. En dernier la fonctionnalité d'export avec filtre : **16** (la plus complexe)

Après chaque correction, vérifie visuellement en comparant avec la maquette correspondante.
