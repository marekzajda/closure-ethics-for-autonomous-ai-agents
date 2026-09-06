"""Complete Sentinel translations; preserve source markup and executable examples."""
import re
from html import escape
from pathlib import Path

# Each row: source text-node index | Czech | German | French | Spanish.
ROWS = '''0|Spustitelná případová studie · v0.2.0|Ausführbare Fallstudie · v0.2.0|Étude de cas exécutable · v0.2.0|Caso práctico ejecutable · v0.2.0
1|Omega Sentinel: pozorování bez zásahu.|Omega Sentinel: Beobachtung ohne Eingriff.|Omega Sentinel : observer sans intervenir.|Omega Sentinel: observar sin intervenir.
2|Lokální telemetrický agent pro výzkumné běhy Omega ukazuje praktickou hranici Closure Ethics: dostatek autonomie pro pozorování a hlášení, ale záměrně nedostatečná oprávnění k řízení či přepisování sledovaného systému.|Ein lokaler Telemetrieagent für Omega-Forschungsläufe zeigt eine praktische Grenze von Closure Ethics: ausreichend Autonomie zum Beobachten und Berichten, aber bewusst keine Befugnis, das beobachtete System zu steuern oder umzuschreiben.|Un agent de télémétrie locale pour les calculs de recherche Omega illustre une limite pratique de Closure Ethics : assez d’autonomie pour observer et rendre compte, mais volontairement pas assez de droits pour contrôler ou réécrire le système observé.|Un agente de telemetría local para ejecuciones de investigación Omega demuestra un límite práctico de Closure Ethics: autonomía suficiente para observar e informar, pero sin autoridad para controlar o reescribir el sistema observado.
3|Zdrojový kód na GitHubu ↗|Quellcode auf GitHub ↗|Code source sur GitHub ↗|Código fuente en GitHub ↗
4|Zdrojový kód Omega Sentinel v0.2 ↗|Omega Sentinel v0.2 Quellcode ↗|Code source Omega Sentinel v0.2 ↗|Código de Omega Sentinel v0.2 ↗
5|Strojově čitelná politika ↗|Maschinenlesbare Richtlinie ↗|Politique lisible par machine ↗|Política legible por máquina ↗
6|Pravidlo návrhu:|Entwurfsregel:|Règle de conception :|Regla de diseño:
7| pozorovatel má být schopen odhalit selhání, ale nesmí je skrýt změnou sledovaného procesu nebo důkazů.| Ein Beobachter soll Fehler aufdecken können, sie aber nicht durch Änderungen am beobachteten Prozess oder an den Belegen verbergen können.| un observateur doit pouvoir révéler une défaillance, sans pouvoir la dissimuler en modifiant le processus ou les preuves qu’il observe.| un observador debe poder revelar un fallo, pero no ocultarlo modificando el proceso o las pruebas que observa.
8|Provozní účel|Betrieblicher Zweck|Rôle opérationnel|Propósito operativo
9|Úzce vymezený agent s užitečným úkolem.|Ein begrenzter Agent mit einer nützlichen Aufgabe.|Un agent au périmètre restreint, avec une tâche utile.|Un agente de alcance limitado con una tarea útil.
10|Procesy|Prozesse|Processus|Procesos
11|Stav výzkumného běhu|Zustand des Forschungslaufs|État des calculs de recherche|Estado de la ejecución de investigación
12|Vyhledává relevantní procesy Pythonu pomocí |Findet relevante Python-Prozesse über |Repère les processus Python pertinents via |Encuentra procesos Python relevantes mediante 
14| nebo víceúrovňových záložních metod Windows a výslovně hlásí zhoršenou kvalitu pozorování.| oder gestufte Windows-Ersatzverfahren und meldet eingeschränkte Beobachtungsqualität ausdrücklich.| ou des mécanismes de repli Windows successifs, et signale explicitement toute observation dégradée.| o métodos alternativos escalonados de Windows e informa explícitamente de la observación degradada.
15|Důkazy|Belege|Preuves|Pruebas
16|Logy a souhrny|Protokolle und Zusammenfassungen|Journaux et synthèses|Registros y resúmenes
17|Čte omezený počet posledních řádků logů, vyhledává stanovené chybové vzory a hlásí existující vědeckou klasifikaci bez její změny.|Liest eine begrenzte Anzahl letzter Protokollzeilen, erkennt definierte Fehlermuster und meldet eine vorhandene wissenschaftliche Klassifikation, ohne sie zu verändern.|Lit un nombre limité de dernières lignes des journaux, détecte les motifs d’erreur définis et rapporte la classification scientifique existante sans la modifier.|Lee un número limitado de líneas finales de los registros, detecta patrones de error definidos e informa de la clasificación científica existente sin modificarla.
18|Hardware|Hardware|Matériel|Hardware
19|Telemetrie GPU|GPU-Telemetrie|Télémétrie GPU|Telemetría GPU
20|Čte využití, paměť a teplotu pomocí |Liest Auslastung, Speicher und Temperatur über |Lit l’utilisation, la mémoire et la température via |Lee utilización, memoria y temperatura mediante 
22|; chybějící telemetrii přizná místo vymýšlení hodnot.|; fehlende Telemetrie wird sichtbar gemacht statt erfunden.| ; les données manquantes sont signalées plutôt qu’inventées.|; la telemetría ausente se señala en vez de inventarse.
23|Lokální stav|Lokaler Zustand|État local|Estado local
24|Přehled|Übersicht|Tableau de bord|Panel
25|Ve výchozím intervalu 30 sekund obnovuje přehled pro člověka a strojově čitelný aktuální stav.|Aktualisiert standardmäßig alle 30 Sekunden eine menschenlesbare Übersicht und den maschinenlesbaren aktuellen Zustand.|Actualise par défaut toutes les 30 secondes un tableau de bord lisible par l’humain et un état courant lisible par machine.|Actualiza de forma predeterminada cada 30 segundos un panel legible por personas y el estado actual legible por máquina.
26|Audit|Audit|Audit|Auditoría
27|Rozhodnutí Closure|Closure-Entscheidungen|Décisions Closure|Decisiones Closure
28|Zaznamenává rozhodnutí politiky pro každé deklarované čtení a zápis do lokální auditní stopy NDJSON.|Zeichnet die Richtlinienentscheidung für jeden deklarierten Lese- und Schreibvorgang in einer lokalen NDJSON-Auditspur auf.|Enregistre la décision de politique associée à chaque lecture et écriture déclarée dans une piste d’audit NDJSON locale.|Registra la decisión de política de cada lectura y escritura declarada en una pista de auditoría NDJSON local.
29|Datový most|Datenbrücke|Passerelle|Puente
30|Data nejsou oprávnění|Nutzdaten sind keine Berechtigung|Les données ne sont pas une autorisation|Los datos no son un permiso
31|Připravuje kompaktní lokální hlášení aktivity. Jeho publikování je záměrně svěřeno samostatné, nezávisle autorizované komponentě.|Erstellt eine kompakte lokale Statusmeldung. Ihre Veröffentlichung bleibt bewusst einer separaten, unabhängig autorisierten Komponente vorbehalten.|Prépare un signal d’activité local compact. Sa publication est volontairement confiée à un composant séparé, autorisé indépendamment.|Prepara una señal de actividad local compacta. Su publicación se delega deliberadamente en un componente separado con autorización independiente.
32|Mapa oprávnění|Befugnisübersicht|Carte des autorisations|Mapa de permisos
33|Užitečná hranice je výslovně určená.|Die sinnvolle Grenze ist ausdrücklich festgelegt.|La limite utile est explicite.|El límite útil es explícito.
34|Schopnost|Fähigkeit|Capacité|Capacidad
35|Stav|Status|Statut|Estado
36|Odůvodnění Closure|Closure-Begründung|Justification Closure|Justificación Closure
37|Čtení relevantních metadat procesů|Relevante Prozessmetadaten lesen|Lire les métadonnées pertinentes des processus|Leer metadatos relevantes de procesos
38|Povoleno|Erlaubt|Autorisé|Permitido
39|Nutné pro pozorování; použitá metoda a stav degradace zůstávají dohledatelné.|Für die Beobachtung notwendig; das verwendete Backend und sein Degradationszustand bleiben nachvollziehbar.|Nécessaire à l’observation ; le mécanisme utilisé et son état de dégradation restent traçables.|Necesario para observar; el mecanismo utilizado y su estado de degradación siguen siendo identificables.
40|Čtení omezených konců logů a souhrnů|Begrenzte Protokollenden und Zusammenfassungen lesen|Lire les fins limitées des journaux et les synthèses|Leer finales limitados de registros y resúmenes
41|Povoleno|Erlaubt|Autorisé|Permitido
42|Podporuje rozpoznání selhání bez změny vědeckých důkazů.|Unterstützt die Fehlererkennung, ohne wissenschaftliche Belege zu verändern.|Permet de reconnaître les défaillances sans modifier les preuves scientifiques.|Facilita detectar fallos sin alterar las pruebas científicas.
43|Zápis pěti souborů do |Fünf Dateien schreiben unter |Écrire cinq fichiers dans |Escribir cinco archivos en 
45|Povoleno|Erlaubt|Autorisé|Permitido
46|Lokální, pojmenovaná a nahraditelná telemetrie s nulovým deklarovaným vědeckým či vnějším dopadem.|Lokale, benannte und ersetzbare Telemetrie ohne deklarierten wissenschaftlichen oder externen Effekt.|Télémétrie locale, nommée et remplaçable, sans effet scientifique ou externe déclaré.|Telemetría local, identificada y reemplazable, sin efecto científico o externo declarado.
47|Spuštění, zastavení či restart procesu|Prozess starten, stoppen oder neu starten|Démarrer, arrêter ou redémarrer un processus|Iniciar, detener o reiniciar un proceso
48|Zakázáno|Verweigert|Refusé|Denegado
49|Oprávnění k pozorování nezakládá oprávnění k zásahu.|Beobachtungsbefugnis ergibt keine Eingriffsbefugnis.|L’autorité d’observation ne confère pas l’autorité d’intervention.|La autoridad para observar no otorga autoridad para intervenir.
50|Změna nebo smazání vědeckých souborů|Wissenschaftliche Dateien ändern oder löschen|Modifier ou supprimer des fichiers scientifiques|Modificar o borrar archivos científicos
51|Zakázáno|Verweigert|Refusé|Denegado
52|Zachovává důkazy, vratnost a nezávislost sledovaného běhu.|Bewahrt Belege, Umkehrbarkeit und Unabhängigkeit des überwachten Laufs.|Préserve les preuves, la réversibilité et l’indépendance des calculs surveillés.|Preserva las pruebas, la reversibilidad y la independencia de la ejecución supervisada.
53|Síťový přístup nebo publikování na GitHubu|Netzwerkzugriff oder GitHub-Veröffentlichung|Accès réseau ou publication sur GitHub|Acceso a la red o publicación en GitHub
54|Zakázáno|Verweigert|Refusé|Denegado
55|Komunikační výstup nezakládá identitu, přihlašovací údaje ani oprávnění publikovat.|Eine Kommunikationsausgabe begründet weder Identität noch Zugangsdaten oder Veröffentlichungsbefugnis.|Une sortie de communication n’implique ni identité, ni identifiants, ni autorisation de publication.|Una salida de comunicación no implica identidad, credenciales ni autorización para publicar.
56|Změna oprávnění nebo rozšíření trvalého běhu|Privilegien ändern oder Persistenz erweitern|Modifier les privilèges ou étendre la persistance|Cambiar privilegios o ampliar la persistencia
57|Zakázáno|Verweigert|Refusé|Denegado
58|Pozorovatel nemůže skrytě rozšířit vlastní provozní hranice.|Der Beobachter kann seine eigenen Betriebsgrenzen nicht unbemerkt erweitern.|L’observateur ne peut pas étendre silencieusement son propre périmètre d’action.|El observador no puede ampliar silenciosamente sus propios límites operativos.
59|Topologie řízení|Steuerungstopologie|Topologie de contrôle|Topología de control
60|Dělba pravomocí v malém systému.|Gewaltenteilung in einem kleinen System.|Séparation des pouvoirs dans un petit système.|Separación de poderes en un sistema pequeño.
61|Cesta pozorování|Beobachtungspfad|Chaîne d’observation|Ruta de observación
62|výzkumný běh → omezené čtecí operace → stav Sentinelu → Closure Kernel → lokální telemetrie|Forschungslauf → begrenzte Leser → Sentinel-Zustand → Closure Kernel → lokale Telemetrie|calculs de recherche → lecteurs limités → état Sentinel → Closure Kernel → télémétrie locale|ejecución de investigación → lectores limitados → estado Sentinel → Closure Kernel → telemetría local
63|Vnější cesta|Externer Pfad|Chaîne externe|Ruta externa
64|bridge.json → samostatně autorizovaný publikátor → GitHub|bridge.json → separat autorisierter Herausgeber → GitHub|bridge.json → composant de publication autorisé séparément → GitHub|bridge.json → publicador autorizado por separado → GitHub
65|. Druhá šipka není implementována uvnitř Sentinelu.|. Der zweite Pfeil ist nicht innerhalb von Sentinel implementiert.|. La seconde flèche n’est pas implémentée dans Sentinel.|. La segunda flecha no está implementada dentro de Sentinel.
66|Proč na tom záleží|Warum das wichtig ist|Pourquoi c’est important|Por qué importa
67|Pokud monitoring, zásahy a publikování sdílejí jedinou nerozlišenou pravomoc, může vadný či kompromitovaný agent změnit proces, přepsat důkazy a publikovat zavádějící zprávu. Omega Sentinel udržuje tyto pravomoci strukturálně oddělené.|Wenn Überwachung, Eingriff und Veröffentlichung eine einzige undifferenzierte Befugnis teilen, kann ein fehlerhafter oder kompromittierter Agent den Prozess verändern, Belege umschreiben und irreführend berichten. Omega Sentinel hält diese Befugnisse strukturell getrennt.|Si surveillance, intervention et publication partagent une autorité unique et indifférenciée, un agent défectueux ou compromis peut modifier le processus, réécrire les preuves et publier un récit trompeur. Omega Sentinel maintient ces pouvoirs structurellement séparés.|Si la supervisión, la intervención y la publicación comparten una sola autoridad indiferenciada, un agente defectuoso o comprometido puede cambiar el proceso, reescribir las pruebas y publicar un relato engañoso. Omega Sentinel mantiene estos poderes separados estructuralmente.
68|Obsah repozitáře|Repository-Inhalt|Contenu du dépôt|Contenido del repositorio
69|Spustitelný a kontrolovatelný.|Ausführbar und überprüfbar.|Exécutable et inspectable.|Ejecutable e inspeccionable.
70|Původní pozorovatel|Ursprünglicher Beobachter|Observateur d’origine|Observador original
72| je zpevněný základ v0.1.2. | ist die gehärtete Basis v0.1.2. | est la base renforcée v0.1.2. | es la base reforzada v0.1.2. 
74| přidává verzování schématu, latenci vzorkování, přehled a lokální data mostu.| ergänzt Schemaversionierung, Abtastlatenz, Übersicht und lokale Brückennutzdaten.| ajoute la gestion des versions du schéma, la latence d’échantillonnage, le tableau de bord et les données locales de passerelle.| añade versiones del esquema, latencia de muestreo, panel y datos locales del puente.
75|Spustitelná hranice politiky|Ausführbare Richtliniengrenze|Limite de politique exécutable|Límite de política ejecutable
77| a | und | et | y 
79| implementují veřejný seznam povolených I/O operací s výchozím odmítnutím. Testy ověřují povolený telemetrický cíl i zakázaný cíl vědeckého souboru.| implementieren die öffentliche I/O-Erlaubnisliste mit standardmäßiger Verweigerung. Tests prüfen sowohl das erlaubte Telemetrieziel als auch ein verweigertes wissenschaftliches Dateiziel.| implémentent la liste publique des E/S autorisées, avec refus par défaut. Les tests vérifient une destination de télémétrie autorisée et une destination de fichier scientifique refusée.| implementan la lista pública de E/S permitidas con denegación por defecto. Las pruebas verifican un destino de telemetría permitido y un destino de archivo científico denegado.
81|Nastavení a hranice oprávnění ↗|Einrichtung und Befugnisgrenzen ↗|Installation et limites d’autorité ↗|Configuración y límites de autoridad ↗
82|Testy ↗|Tests ↗|Tests ↗|Pruebas ↗
83|Vědecké vymezení|Wissenschaftliche Abgrenzung|Limites scientifiques|Límites científicos
84|Demonstrátor, nikoli důkaz vyřešení alignmentu.|Ein Demonstrator, keine Behauptung gelösten Alignments.|Un démonstrateur, pas une affirmation d’alignement résolu.|Un demostrador, no una afirmación de alineamiento resuelto.
85|Omega Sentinel ukazuje, že princip Closure Ethics lze převést na konkrétní softwarovou hranici oprávnění. Nedokazuje morální správnost, neřeší obecný AI alignment ani nezabezpečuje okolní operační systém. Jádro řídí deklarované I/O Sentinelu; oprávnění nasazení a případný vnější publikátor vyžadují nezávislé kontroly.|Omega Sentinel zeigt, dass ein Closure-Ethics-Prinzip in eine konkrete softwareseitige Befugnisgrenze übersetzt werden kann. Es begründet keine moralische Richtigkeit, löst nicht das allgemeine KI-Alignment und sichert nicht das umgebende Betriebssystem. Der Kernel regelt Sentinels deklarierte I/O; Bereitstellungsrechte und externe Herausgeber benötigen unabhängige Kontrollen.|Omega Sentinel montre qu’un principe de Closure Ethics peut devenir une limite concrète d’autorité logicielle. Il n’établit pas la justesse morale, ne résout pas l’alignement général de l’IA et ne sécurise pas le système d’exploitation environnant. Le noyau régit les E/S déclarées de Sentinel ; les droits de déploiement et tout composant externe de publication nécessitent des contrôles indépendants.|Omega Sentinel muestra que un principio de Closure Ethics puede convertirse en un límite concreto de autoridad del software. No establece la corrección moral, no resuelve el alineamiento general de la IA ni protege el sistema operativo circundante. El núcleo regula las E/S declaradas de Sentinel; los permisos de despliegue y cualquier publicador externo requieren controles independientes.'''

TRANSLATIONS = {}
for row in ROWS.splitlines():
    index, *values = row.split('|')
    assert len(values) == 4
    TRANSLATIONS[int(index)] = values

META = {
 'cs': ('Omega Sentinel v0.2 | Případová studie Closure Ethics', 'Lokální telemetrický agent s omezenými oprávněními, auditní stopou a odděleným publikováním.'),
 'de': ('Omega Sentinel v0.2 | Closure Ethics Fallstudie', 'Lokaler Telemetrieagent mit begrenzten Befugnissen, Auditspur und getrennter Veröffentlichung.'),
 'fr': ('Omega Sentinel v0.2 | Étude de cas Closure Ethics', 'Agent de télémétrie locale avec autorité limitée, piste d’audit et publication séparée.'),
 'es': ('Omega Sentinel v0.2 | Caso práctico Closure Ethics', 'Agente de telemetría local con autoridad limitada, pista de auditoría y publicación separada.'),
}

def localized(lang):
    source = (Path(__file__).resolve().parents[1] / 'docs/sentinel.html').read_text(encoding='utf-8')
    main = re.search(r'<main>.*?</main>', source, re.S)[0]
    parts = re.split(r'(<[^>]+>)', main)
    indices = [i for i, t in enumerate(parts) if t.strip() and not t.startswith('<')]
    # Technical filenames and the executable command block remain verbatim.
    unchanged = {13,21,44,71,73,76,78,80}
    assert len(indices) == 86 and set(TRANSLATIONS) | unchanged == set(range(86))
    column = ('cs','de','fr','es').index(lang)
    for index, values in TRANSLATIONS.items():
        parts[indices[index]] = escape(values[column], quote=False)
    return (*META[lang], ''.join(parts))
