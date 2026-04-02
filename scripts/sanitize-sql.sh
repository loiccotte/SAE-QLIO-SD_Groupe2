#!/bin/bash
# Supprime les octets nuls des fichiers SQL avant import MariaDB.
# Place dans docker-entrypoint-initdb.d/ AVANT le .sql (prefixe 00-).
for f in /docker-entrypoint-initdb.d/*.sql; do
    if [ -f "$f" ]; then
        count=$(tr -cd '\0' < "$f" | wc -c)
        if [ "$count" -gt 0 ]; then
            echo "Sanitize: suppression de $count octets nuls dans $f"
            tr -d '\0' < "$f" > "$f.clean"
            mv "$f.clean" "$f"
        fi
    fi
done
