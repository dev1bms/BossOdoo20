# -*- coding: utf-8 -*-
"""Plan de lanzamiento BOSS Odoo 20 en task.bosscontinental.com (siembra idempotente, 26/10/2026).

Uso (en el servidor, ~/boss-tasks):
    .venv/bin/python manage.py seed_launch            # aplica el plan: sprints semanales, epics, festivos, tareas
    .venv/bin/python manage.py seed_launch --dry-run  # solo muestra lo que haría

Hitos aprobados por Belal el 26/10/2026 (sustituyen al 30/11 y a cualquier calendario anterior):
  semana 19–25 oct = inicio del registro de avance real · 20/11/2026 entrega completa · operación en pruebas hasta
  el 1/12/2026 · 2–31/12 corrección, estabilización y preparación del cambio · 1/1/2027 Odoo 20 único sistema.

Reglas:
  * Idempotente por Sprint.name, Phase.name, Holiday.date y Task.code; todo en una transacción.
  * Las tareas del plan del 21/10 (BOSS20-000…026) se conservan: se actualiza su estado SOLO con evidencia
    (commit, fichero o lectura del sistema) y se registra en el historial y en un comentario.
  * Las tareas creadas hoy para trabajo ya realizado (semana 19–25 oct) lo dicen en su descripción: son
    planificación reconstruida a posteriori; sus fechas son las de los commits.
  * Nunca cambia estado, avance ni horas reales que un usuario haya registrado después (solo aplica estados a
    tareas que siguen como las dejó la siembra anterior).
  * Las fechas de las tareas de Cristina y Ángel son propuestas de Belal, no compromisos suyos.
"""
from datetime import date, datetime, time

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from panel.models import (Comment, Department, Holiday, Phase, Sprint, Task, log_activity, log_task_changes,
                          snapshot_task)

D = date
P = Task.Priority
T = Task.TaskType
S = Task.Status

USERS = {"belal": "balswerki@bosscontinental.com", "cristina": "csantisteban@bosscontinental.com",
         "angel": "adesantisteban@bosscontinental.com"}
DEPTS = {"sys": "Sistemas / Odoo 20", "fin": "Administración / Finanzas", "com": "Comercial / CRM",
         "ops": "Operaciones", "dir": "Dirección"}

HOLIDAYS = [
    (D(2026, 11, 2), "Todos los Santos (traslado)"),
    (D(2026, 11, 9), "Nuestra Señora de La Almudena"),
    (D(2026, 12, 8), "Inmaculada Concepción"),
    (D(2026, 12, 25), "Navidad"),
    (D(2027, 1, 1), "Año Nuevo"),
    (D(2027, 1, 6), "Epifanía"),
]

EPICS = {
    "E1": "E1 · Setup y gobierno",
    "E2": "E2 · Arquitectura (ADR)",
    "E3": "E3 · Estudios de servicios IMB",
    "E4": "E4 · Motor de tarifas",
    "E5": "E5 · Validación y entrega",
    "E6": "E6 · Ciclo operativo y expediente",
    "E7": "E7 · Facturación y contabilidad",
    "E8": "E8 · Tarifas y documentos de proveedores (Hoja1)",
    "E9": "E9 · Migración de datos de Odoo 17",
    "E10": "E10 · Informes y previsiones",
    "E11": "E11 · Usuarios, formación y pruebas de usuario",
    "E12": "E12 · Infraestructura, arranque y continuidad",
}

# key: (nombre, inicio, fin, estado, objetivo, nombre anterior a renombrar o None)
SPRINTS = {
    "S43": ("S43 · 19–25 oct · Arranque (realizado)", D(2026, 10, 19), D(2026, 10, 25), Sprint.Status.CLOSED,
            "Registro del avance real: catálogo, motor de tarifas, tabla de IVA, ciclo operativo completo, guía "
            "publicada y despliegue en boss20 (commits del 21 al 23/10). Planificación reconstruida el 26/10 con las "
            "fechas reales de los commits.", "Sprint 0 · Arranque"),
    "S44": ("S44 · 26 oct–1 nov · Decisiones y datos", D(2026, 10, 26), D(2026, 11, 1), Sprint.Status.ACTIVE,
            "Sesiones con Ángel (contabilidad) y Cristina (tarifas); corrección de D-1 y D-2; usuarios en boss20; "
            "documentos de tarifa pedidos; repositorio remoto; lista aerolínea/handler de Odoo 17.",
            "Sprint 1 · Modelo y estudios"),
    "S45": ("S45 · 2–8 nov · Hoja1 y fase B (4 días laborables)", D(2026, 11, 2), D(2026, 11, 8),
            Sprint.Status.PLANNED,
            "Tarifas lote 1 cargadas; NOA/ATA y aerolínea↔handler en el expediente; venta ALM (B1); ETX/DET (B3); "
            "QBR (B2); informe de previsiones; alcance y mapeo de la migración.", "Sprint 2 · Motor de tarifas"),
    "S46": ("S46 · 9–15 nov · Datos y preparación (4 días laborables)", D(2026, 11, 9), D(2026, 11, 15),
            Sprint.Status.PLANNED,
            "Tarifas lote 2; migración de maestros en boss20; usuarios, permisos, correo y plantillas; informes de "
            "facturación y rentabilidad; SII/VeriFactu según decisión; formación 1; entorno Mac.", None),
    "S47": ("S47 · 16–20 nov · Entrega completa", D(2026, 11, 16), D(2026, 11, 20), Sprint.Status.PLANNED,
            "Ensayo de migración completo con conciliación; copias y vuelta atrás; verificación final de Hoja1 "
            "(28 requisitos) con evidencias; acta de entrega el 20/11.", None),
    "S48": ("S48 · 23–29 nov · Operación en pruebas (21/11–1/12)", D(2026, 11, 21), D(2026, 11, 29),
            Sprint.Status.PLANNED,
            "Escenarios completos con las personas de cada área sobre datos migrados; incidencias registradas y "
            "corregidas.", "Operación en pruebas · 21 nov–1 dic"),
    "S49": ("S49 · 30 nov–6 dic · Cierre de pruebas (1/12) y corrección", D(2026, 11, 30), D(2026, 12, 6),
            Sprint.Status.PLANNED,
            "Informe de cierre de la operación en pruebas el 1/12; regla del sistema de referencia en diciembre; "
            "corrección de incidencias.", None),
    "S50": ("S50 · 7–13 dic · Estabilización", D(2026, 12, 7), D(2026, 12, 13), Sprint.Status.PLANNED,
            "Incidencias priorizadas cerradas (8/12 festivo).", "Estabilización y preparación del cambio · 2–31 dic"),
    "S51": ("S51 · 14–20 dic · Formación y ensayo del cambio", D(2026, 12, 14), D(2026, 12, 20),
            Sprint.Status.PLANNED,
            "Formación restante por rol; ensayo completo del cambio definitivo con conciliación.", None),
    "S52": ("S52 · 21–27 dic · Copias, vuelta atrás y lista de comprobación", D(2026, 12, 21), D(2026, 12, 27),
            Sprint.Status.PLANNED,
            "Copias y restauración verificadas; lista del cambio aprobada por Cristina y Ángel (25/12 festivo).", None),
    "S53": ("S53 · 28 dic–3 ene · Cambio definitivo (1/1/2027)", D(2026, 12, 28), D(2027, 1, 3),
            Sprint.Status.PLANNED,
            "Corte de Odoo 17 el 31/12, copia final, carga de diferencias, conciliación; el 1/1/2027 Odoo 20 es el "
            "único sistema y Odoo 17 queda en solo lectura.", "Cambio definitivo · 1–8 ene 2027"),
    "S2701": ("S01/2027 · 4–8 ene · Soporte posterior al cambio", D(2027, 1, 4), D(2027, 1, 8),
              Sprint.Status.PLANNED,
              "Primera semana de operación real en Odoo 20: soporte inmediato, incidencias con prioridad, acta de "
              "aceptación el 8/1.", None),
}

RETRO = ("Tarea creada el 26/10/2026 para reflejar trabajo ya realizado (planificación reconstruida a posteriori); "
         "las fechas son las de los commits.")
NOT_COMMITTED = "Fecha propuesta por Belal el 26/10/2026; no confirmada por la persona responsable."
DOC = "https://doc.bosscontinental.com/new/"
SYS = "https://system.bosscontinental.com"


def desc(*parts):
    return "\n".join(p for p in parts if p)


def mad(day, hour=18):
    """Hora local de Madrid de un día (para completed_at de trabajo ya hecho)."""
    return timezone.make_aware(datetime.combine(day, time(hour, 0)), timezone.get_default_timezone())


# Cada tarea: dict con code, title, epic, type, sprint, points, start, due, priority, deps, hours, who, dept,
# status (None = no tocar), done (fecha de cierre real, solo con status hecha), desc, evidence (comentario), links.
TASKS = [
    # ===================================================================== S43 · 19–25 oct (realizado)
    dict(code="000", title="Paso 1: análisis de la situación y preguntas abiertas", epic="E1", type=T.ANALYSIS,
         sprint="S43", points=2, start=D(2026, 10, 21), due=D(2026, 10, 21), priority=P.HIGH, deps=[], hours=4,
         who="belal", dept="sys", status=S.DONE, done=D(2026, 10, 21),
         desc=desc("Resultado: análisis de lo pedido y preguntas abiertas para Belal (paso 1 del KICKOFF).",
                   "Fuente: KICKOFF_PROMPT.md.", "Aceptación: Belal responde a las preguntas (hecho el 21–22/10)."),
         evidence="Cerrada el 26/10 con evidencia: docs/preguntas-abiertas.md y docs/fuentes.md (commit 155ce70, "
                  "21/10/2026); respuestas de Belal recogidas en docs/preguntas-abiertas.md.",
         links=[f"{DOC}#/preguntas"]),
    dict(code="001", title="Task manager: Scrum (sprints, backlog, tablero, burndown) + Gantt y publicación",
         epic="E1", type=T.INFRA, sprint="S43", points=5, start=D(2026, 10, 21), due=D(2026, 10, 22),
         priority=P.HIGH, deps=[], hours=8, who="belal", dept="sys", status=S.DONE, done=D(2026, 10, 21),
         desc=desc("Resultado: task.bosscontinental.com con sprints, backlog, tablero, story points, burndown y Gantt.",
                   "Aceptación: publicado y verificado en el navegador."),
         evidence="Cerrada el 26/10 con evidencia: plataforma en producción (servicio boss-tasks activo desde el "
                  "23/10 06:18 UTC; siembra seed_boss20 del 21/10 con 3 sprints y 24 tareas; historial del 21/10).",
         links=["https://task.bosscontinental.com/gantt/"]),
    dict(code="002", title="Estructura del repositorio, CLAUDE.md y .gitignore", epic="E1", type=T.INFRA,
         sprint="S43", points=2, start=D(2026, 10, 21), due=D(2026, 10, 21), priority=P.HIGH, deps=["000"],
         hours=3, who="belal", dept="sys", status=S.DONE, done=D(2026, 10, 21),
         desc=desc("Resultado: addons/, docs/adr, dev/, .gitignore sin código de Odoo ni PDF de proveedores; "
                   "CLAUDE.md con las reglas del proyecto."),
         evidence="Cerrada el 26/10 con evidencia: commits 08324fc y dc1897b (21/10/2026); CLAUDE.md y .gitignore "
                  "en el repositorio BossOdoo20.", links=[]),
    dict(code="004", title="ADR-001: versión, arquitectura y módulos de tarifas", epic="E2", type=T.DOCS,
         sprint="S43", points=3, start=D(2026, 10, 21), due=D(2026, 10, 21), priority=P.HIGH, deps=["002"],
         hours=3, who="belal", dept="sys", status=S.DONE, done=D(2026, 10, 21),
         desc="Resultado: docs/adr/001-architecture-and-modules.md (contexto, alternativas, decisión, consecuencias).",
         evidence="Cerrada el 26/10 con evidencia: docs/adr/001-architecture-and-modules.md (commit 08324fc, 21/10).",
         links=[f"{DOC}#/arquitectura"]),
    dict(code="005", title="ADR-002: modelo de datos de tarifas", epic="E2", type=T.DOCS, sprint="S43", points=5,
         start=D(2026, 10, 21), due=D(2026, 10, 21), priority=P.CRITICAL, deps=["004"], hours=4, who="belal",
         dept="sys", status=S.DONE, done=D(2026, 10, 21),
         desc="Resultado: docs/adr/002-pricing-model.md: tarifa con documento, vigencia y versiones; línea por "
              "servicio; métodos; ámbito; mínimo/máximo; aprobación; servicio único de cálculo.",
         evidence="Cerrada el 26/10 con evidencia: docs/adr/002-pricing-model.md (commit 08324fc, 21/10/2026).",
         links=[f"{DOC}#/metodos"]),
    dict(code="006", title="Plantilla del estudio de servicio (docs/services)", epic="E3", type=T.DOCS,
         sprint="S43", points=1, start=D(2026, 10, 21), due=D(2026, 10, 21), priority=P.MEDIUM, deps=["005"],
         hours=1, who="belal", dept="sys", status=S.CANCELLED, done=None,
         desc=desc("Sustituida: no se creó docs/services; el estudio por servicio vive en docs/matriz-servicios.md "
                   "(unidad, método, IVA, estado) y docs/ejemplos-referencia.md (casos comprobados con documentos "
                   "reales), más la página de cada servicio en la guía."),
         evidence="Cancelada el 26/10: sustituida por docs/matriz-servicios.md, docs/ejemplos-referencia.md y las "
                  "78 páginas de servicio de la guía (commits 155ce70 y 45220ef, 21/10/2026).",
         links=[f"{DOC}#/catalogo"]),
    dict(code="010", title="Estudio THC (importación marítima FCL) + casos dorados", epic="E3", type=T.ANALYSIS,
         sprint="S43", points=3, start=D(2026, 10, 21), due=D(2026, 10, 21), priority=P.HIGH, deps=["005"],
         hours=4, who="belal", dept="sys", status=S.DONE, done=D(2026, 10, 21),
         desc="Resultado: THC estudiado con el documento MSC 09/2026 p.12 (R1), tarifa de muestra cargada y "
              "prueba de referencia; equivale a docs/services/THC.md del plan original.",
         evidence="Cerrada el 26/10 con evidencia: docs/ejemplos-referencia.md R1; prueba de referencias de "
                  "boss_pricing (0 fallos, 23/10); tarifa [MUESTRA] MSC en boss20 (esperando aprobación).",
         links=[f"{DOC}#/srv-THC"]),
    dict(code="003", title="Entorno de desarrollo y pruebas (Docker local, BD desechable) y servidor boss20",
         epic="E1", type=T.INFRA, sprint="S43", points=3, start=D(2026, 10, 21), due=D(2026, 10, 21),
         priority=P.CRITICAL, deps=["002"], hours=6, who="belal", dept="sys", status=S.DONE, done=D(2026, 10, 21),
         desc="Resultado: dev/test.sh (pila Docker local con BD en memoria para pruebas), dev/deploy.sh con "
              "comprobación de identidad del entorno, servidor boss20 con Odoo 20 Enterprise.",
         evidence="Cerrada el 26/10 con evidencia: dev/test.sh, dev/compose.test.yml, dev/deploy.sh (commits "
                  "8f0744c y 9bc6dbe, 21/10/2026); pruebas Odoo ejecutadas en BD desechable el 23/10.",
         links=[SYS]),
    dict(code="020", title="Motor de cálculo en Python puro + tests sobre casos dorados", epic="E4", type=T.DEV,
         sprint="S43", points=8, start=D(2026, 10, 21), due=D(2026, 10, 22), priority=P.CRITICAL,
         deps=["005", "003"], hours=16, who="belal", dept="sys", status=S.DONE, done=D(2026, 10, 22),
         desc="Resultado: addons/boss_pricing/engine (fijo, por unidad, mayor de dos bases, tramos, porcentaje, "
              "tiempo con franquicia, periodos de 24 h o días, excepciones de fin de semana) con sus pruebas.",
         evidence="Cerrada el 26/10 con evidencia: commits 08324fc, b242af1 (21/10) y 312088f (23/10); 21/21 "
                  "pruebas del motor (python -m unittest) el 23/10/2026.", links=[f"{DOC}#/metodos"]),
    dict(code="021", title="Módulo Odoo: tarifa de proveedor (documento, vigencia, versiones, línea por servicio)",
         epic="E4", type=T.DEV, sprint="S43", points=8, start=D(2026, 10, 21), due=D(2026, 10, 22),
         priority=P.HIGH, deps=["005", "003"], hours=16, who="belal", dept="sys", status=S.DONE,
         done=D(2026, 10, 22),
         desc="Resultado: boss.tariff y boss.tariff.line con documento y página, vigencia, versiones, ámbito, "
              "aprobación (borrador → esperando aprobación → aprobada) e importador de muestras.",
         evidence="Cerrada el 26/10 con evidencia: commits 08324fc, 2140038, 31d64ee (21/10/2026); 10 tarifas "
                  "[MUESTRA] cargadas en boss20 y esperando aprobación (lectura del 26/10).",
         links=[f"{DOC}#/tarifa-alta"]),
    dict(code="013", title="Estudio DEM/OCU/ALM (cargos por tiempo)", epic="E3", type=T.ANALYSIS, sprint="S43",
         points=5, start=D(2026, 10, 22), due=D(2026, 10, 23), priority=P.CRITICAL, deps=["005"], hours=8,
         who="belal", dept="sys", status=S.DONE, done=D(2026, 10, 23),
         desc="Resultado: días libres, eventos que abren y cierran el periodo, tramos relativos o por número de "
              "día, periodos de 24 h o días naturales, mínimo; casos R8–R18 (MSC, Hapag, CMA) y R01–R05 (WFS).",
         evidence="Cerrada el 26/10 con evidencia: docs/ejemplos-referencia.md, guía «Almacenaje» y «Métodos» "
                  "(commits 9b4e632 y 312088f, 23/10/2026); decisiones P40–P42 aprobadas por Belal el 23/10.",
         links=[f"{DOC}#/almacenaje"]),
    dict(code="022", title="Condiciones de ámbito y servicio único de matching y cálculo", epic="E4", type=T.DEV,
         sprint="S43", points=5, start=D(2026, 10, 21), due=D(2026, 10, 22), priority=P.HIGH, deps=["020", "021"],
         hours=8, who="belal", dept="sys", status=S.DONE, done=D(2026, 10, 22),
         desc="Resultado: boss.pricing.price_cost(): una sola función para oferta y expediente, con estados "
              "explícitos (ok, faltan datos, sin tarifa, pendiente de aprobación, conflicto, no preparado).",
         evidence="Cerrada el 26/10 con evidencia: addons/boss_pricing/models/boss_pricing.py (commit b242af1, "
                  "21/10); usada por oferta y expediente (commit b318401, 23/10).", links=[f"{DOC}#/coste"]),
    dict(code="011", title="Estudio BL/DOC", epic="E3", type=T.ANALYSIS, sprint="S43", points=2,
         start=D(2026, 10, 21), due=D(2026, 10, 21), priority=P.MEDIUM, deps=["005"], hours=2, who="belal",
         dept="sys", status=S.DONE, done=D(2026, 10, 21),
         desc="Resultado: BL una vez por expediente (R4, MSC p.12); DOC para el house; máster por expediente (P25).",
         evidence="Cerrada el 26/10 con evidencia: docs/ejemplos-referencia.md R4; decisión P25 (Cristina 28/09) en "
                  "docs/preguntas-abiertas.md.", links=[f"{DOC}#/srv-BL"]),
    dict(code="012", title="Estudio T3 / T3-PAD", epic="E3", type=T.ANALYSIS, sprint="S43", points=2,
         start=D(2026, 10, 21), due=D(2026, 10, 21), priority=P.MEDIUM, deps=["005"], hours=2, who="belal",
         dept="sys", status=S.DONE, done=D(2026, 10, 21),
         desc="Resultado: T3-PAD por tamaño de contenedor (R2, MSC p.12); T3 de otras navieras y de grupaje "
              "pendientes de documento (Hoja1 H1-01).",
         evidence="Cerrada el 26/10 con evidencia: docs/ejemplos-referencia.md R2; docs/mapeo-hoja1.md H1-01.",
         links=[f"{DOC}#/srv-T3-PAD"]),
    dict(code="014", title="Estudio GLO (CCC, FUELEU, LOG)", epic="E3", type=T.ANALYSIS, sprint="S43", points=2,
         start=D(2026, 10, 21), due=D(2026, 10, 21), priority=P.MEDIUM, deps=["005"], hours=2, who="belal",
         dept="sys", status=S.DONE, done=D(2026, 10, 21),
         desc="Resultado: GLO-CCC por contenedor DV/HC (R5) y GLO-FUELEU por TEU origen China (R3); lista "
              "«Lejano Oriente» pendiente de Cristina (P24); GLO por documento pendiente de decisión (H1-13).",
         evidence="Cerrada el 26/10 con evidencia: docs/ejemplos-referencia.md R3 y R5; docs/mapeo-hoja1.md H1-12 a "
                  "H1-14.", links=[f"{DOC}#/srv-GLO-CCC"]),
    dict(code="015", title="Estudio FAD (despacho de importación)", epic="E3", type=T.ANALYSIS, sprint="S45",
         points=2, start=D(2026, 11, 3), due=D(2026, 11, 5), priority=P.MEDIUM, deps=["D01"], hours=2,
         who="belal", dept="sys", status=None, done=None,
         desc=desc("Resultado: FAD con las tarifas reales de Aducex y Ramos Vila (1 contenedor / 2 o más; varias "
                   "partidas) cargadas y comprobadas con un ejemplo de referencia.",
                   "Estado real 26/10: método «por despacho» configurado; sin documento (Hoja1 H1-02). Cristina "
                   "28/09: el operador elige el agente, sin elección automática.",
                   "Fecha original del plan del 21/10: sin fecha (backlog). Nueva fecha: 5/11, por falta de los "
                   "documentos (tarea D01).",
                   "Aceptación: ejemplo de referencia con la tarifa real en docs/ejemplos-referencia.md y prueba "
                   "de referencias en verde."),
         evidence=None, links=[f"{DOC}#/srv-FAD"]),
    dict(code="016", title="Estudio TTE-FCL (transporte de contenedor)", epic="E3", type=T.ANALYSIS, sprint="S45",
         points=3, start=D(2026, 11, 4), due=D(2026, 11, 6), priority=P.MEDIUM, deps=["D01"], hours=3,
         who="belal", dept="sys", status=None, done=None,
         desc=desc("Resultado: TTE-FCL con una tarifa real por ruta y tramos, cargada y comprobada.",
                   "Estado real 26/10: método por tramos configurado; sin documento (Hoja1 H1-18).",
                   "Fecha original: backlog sin fecha. Nueva fecha: 6/11, por falta del documento (tarea D01).",
                   "Aceptación: ejemplo de referencia y prueba en verde."),
         evidence=None, links=[f"{DOC}#/srv-TTE-FCL"]),
    dict(code="017", title="Estudio FMI (flete marítimo con oferta)", epic="E3", type=T.ANALYSIS, sprint="S43",
         points=3, start=D(2026, 10, 21), due=D(2026, 10, 21), priority=P.MEDIUM, deps=["005"], hours=2,
         who="belal", dept="sys", status=S.DONE, done=D(2026, 10, 21),
         desc="Resultado: los fletes (FMI, FME, FAI, FAE) se cotizan con importe manual de la oferta del "
              "proveedor (modo «importe manual»), en su moneda con el tipo del día de la oferta (P03).",
         evidence="Cerrada el 26/10 con evidencia: docs/matriz-servicios.md (fletes en modo manual, 12 servicios "
                  "manuales en boss20, lectura del 26/10); ajuste de moneda P03 activo en boss20.",
         links=[f"{DOC}#/iva-moneda"]),
    dict(code="023", title="Contexto de envío en la oferta (contenedores, pesos, volúmenes, fechas, ruta)",
         epic="E4", type=T.DEV, sprint="S43", points=3, start=D(2026, 10, 22), due=D(2026, 10, 22),
         priority=P.MEDIUM, deps=["022"], hours=6, who="belal", dept="sys", status=S.DONE, done=D(2026, 10, 22),
         desc="Resultado: datos del envío en la oferta y en el expediente (contenedores por tamaño y tipo, kg "
              "brutos, m³, palés, kg tasable de la AWB, fechas, puerto, país, naviera) y una sola función de "
              "cantidad por base de cobro.",
         evidence="Cerrada el 26/10 con evidencia: commits 6f20152 (22/10) y b318401 (23/10); guía "
                  "«Oferta y envío» y «Cantidades».", links=[f"{DOC}#/oferta-envio"]),
    dict(code="024", title="Cargos por tiempo en el expediente (periodo real con horas, recálculo)", epic="E4",
         type=T.DEV, sprint="S43", points=5, start=D(2026, 10, 23), due=D(2026, 10, 23), priority=P.MEDIUM,
         deps=["013", "022"], hours=10, who="belal", dept="sys", status=S.DONE, done=D(2026, 10, 23),
         desc="Resultado: ALM/DEM/OCU con periodo real (inicio y fin con fecha y hora), lecturas de 24 h o días "
              "naturales, mínimo por estancia, excepciones de fin de semana; recálculo del coste previsto.",
         evidence="Cerrada el 26/10 con evidencia: commits 312088f, 125f55b y fusión fdb4cbd (23/10/2026); test "
                  "de referencia de WFS R01–R05; boss20 E260002 (AWB 500→620 kg, +3 días).",
         links=[f"{DOC}#/almacenaje"]),
    dict(code="025", title="Espacio «Tarifas y proveedores»: alta de precios con PDF y página, prueba de cálculo",
         epic="E4", type=T.DEV, sprint="S43", points=5, start=D(2026, 10, 22), due=D(2026, 10, 22),
         priority=P.MEDIUM, deps=["021"], hours=10, who="belal", dept="sys", status=S.DONE, done=D(2026, 10, 22),
         desc="Resultado: una sola forma de introducir un precio ligada a su documento; filtros por estado; "
              "«Probar cálculo» con simulación de borradores; tarifas DEMO aisladas.",
         evidence="Cerrada el 26/10 con evidencia: commits a02548e, 3bef1b2, 8e9171b (22/10/2026); guía "
                  "«Alta de tarifa» y «Aprobación».", links=[f"{DOC}#/tarifa-alta"]),
    dict(code="026", title="Traducción es_ES y pruebas automáticas en verde", epic="E5", type=T.TEST,
         sprint="S43", points=3, start=D(2026, 10, 22), due=D(2026, 10, 23), priority=P.MEDIUM, deps=["022"],
         hours=6, who="belal", dept="sys", status=S.DONE, done=D(2026, 10, 23),
         desc="Resultado: textos fuente en inglés y traducción es.po de los cuatro módulos; 27 pruebas de Odoo "
              "(boss_expediente 13, boss_pricing_sale 13, boss_pricing 1) y 21 del motor sin fallos.",
         evidence="Cerrada el 26/10 con evidencia: i18n/es.po de cada módulo (commit 5b2d337 y siguientes); "
                  "pruebas del 23/10 en 8ec4a2c: 0 fallos (docs/ciclo-operativo.md).",
         links=[f"{DOC}#/mantenimiento"]),
    dict(code="030", title="Revisión con Cristina y Ángel + documentación de entrega", epic="E5",
         type=T.TRAINING, sprint="S44", points=3, start=D(2026, 10, 21), due=D(2026, 10, 30), priority=P.HIGH,
         deps=["020"], hours=6, who="belal", dept="dir", status=S.IN_PROGRESS, done=None, progress=60,
         desc=desc("Resultado: Cristina y Ángel han visto el sistema y han ratificado (o cambiado) las decisiones "
                   "de su ámbito.",
                   "Estado real 26/10: documentación entregada (guía ES/EN publicada el 23/10, decisiones P03–P44 "
                   "aprobadas por Belal, hoja de pruebas de Ángel del 26/10); las sesiones no se han celebrado.",
                   "Fecha original: backlog sin fecha. Nueva fecha: 30/10 (sesiones A01 y C01).",
                   "Aceptación: actas de las dos sesiones con las ratificaciones registradas en "
                   "docs/preguntas-abiertas.md."),
         evidence="En progreso desde el 26/10: documentación y hoja de pruebas listas (commits 0192e66 y 367cbcd); "
                  "sesiones pendientes (tareas A01 y C01).", links=[f"{DOC}#/preguntas"]),
    dict(code="007", title="Repositorio remoto (GitHub) y copia del código; calidad (ruff, pre-commit)", epic="E1",
         type=T.INFRA, sprint="S44", points=2, start=D(2026, 10, 26), due=D(2026, 10, 27), priority=P.CRITICAL,
         deps=["003"], hours=3, who="belal", dept="sys", status=None, done=None,
         desc=desc("Resultado: el repositorio BossOdoo20 tiene un remoto (GitHub de dev1bms u otro aprobado por "
                   "Belal) con todos los commits; ruff y pre-commit configurados.",
                   "Estado real 26/10: no hay remoto (todos los commits son locales: riesgo de pérdida).",
                   "Fecha original del plan: 3/11. Nueva fecha: 27/10, adelantada por decisión de Belal (26/10): el código sigue local y el equipo actual es lento.",
                   "Aceptación: `git remote -v` muestra el remoto y `git push` en verde; ruff sin errores."),
         evidence=None, links=[]),
    # ---- Trabajo de la semana 19–25 oct no previsto en el plan del 21/10 (reconstruido)
    dict(code="R01", title="Catálogo de servicios BOSS (78) con unidad, método de cálculo y clase de IVA",
         epic="E4", type=T.DEV, sprint="S43", points=5, start=D(2026, 10, 21), due=D(2026, 10, 21),
         priority=P.HIGH, deps=[], hours=8, who="belal", dept="sys", status=S.DONE, done=D(2026, 10, 21),
         desc=desc(RETRO, "Resultado: boss_services con los servicios como productos estándar, bases de cobro como "
                          "unidades, modo de coste (tarifa, manual, propio, pendiente) y clase de IVA."),
         evidence="Commit 08324fc (21/10/2026); boss20: 77 servicios activos (lectura del 26/10).",
         links=[f"{DOC}#/catalogo"]),
    dict(code="R02", title="Tabla de IVA BOSS: impuesto de Odoo por clase, zona del cliente y suplidos", epic="E7",
         type=T.DEV, sprint="S43", points=3, start=D(2026, 10, 22), due=D(2026, 10, 22), priority=P.HIGH, deps=[],
         hours=6, who="belal", dept="sys", status=S.DONE, done=D(2026, 10, 22),
         desc=desc(RETRO, "Resultado: reglas de Ángel (31/08) como funciones puras y tabla configurable; un caso "
                          "sin fila deja el IVA pendiente y bloquea enviar o aceptar."),
         evidence="Commit 1f49df8 (22/10/2026); boss20: 6 filas (lectura del 26/10); P17 aplicado el 23/10.",
         links=[f"{DOC}#/iva-moneda"]),
    dict(code="R03", title="Precio de venta desde el coste (listas de precios: fijo, recargo, margen, mínimo)",
         epic="E4", type=T.DEV, sprint="S43", points=3, start=D(2026, 10, 22), due=D(2026, 10, 22),
         priority=P.MEDIUM, deps=["022"], hours=6, who="belal", dept="sys", status=S.DONE, done=D(2026, 10, 22),
         desc=desc(RETRO, "Resultado: base «coste previsto de la línea» en las reglas de lista de precios, recargo "
                          "o margen sobre venta, margen mínimo; los valores por cliente los fija Cristina (P01/P02)."),
         evidence="Commit 70491d3 (22/10/2026); guía «Listas de precios».", links=[f"{DOC}#/tarifa-listas"]),
    dict(code="R04", title="Ciclo operativo: expediente, partes, pedidos de compra, facturación por servicios, "
                           "abonos y rentabilidad", epic="E6", type=T.DEV, sprint="S43", points=13,
         start=D(2026, 10, 23), due=D(2026, 10, 23), priority=P.CRITICAL, deps=["023"], hours=24, who="belal",
         dept="sys", status=S.DONE, done=D(2026, 10, 23),
         desc=desc(RETRO, "Resultado: boss_expediente: expediente E26xxxx abierto al aceptar, cuenta analítica, "
                          "partes y roles, solicitudes de presupuesto sin duplicados, «Marcar como prestado», "
                          "facturación por servicios (hitos), abonos, coste extra refacturado, bloqueos al "
                          "contabilizar y resumen de rentabilidad con origen de cada cifra."),
         evidence="Commits f06470c, 344bd0f, fusión fdb4cbd (23/10/2026); 13 pruebas de boss_expediente en BD "
                  "desechable; ejemplos [DEMO] E260001–E260011 en boss20.", links=[f"{DOC}#/expediente"]),
    dict(code="R05", title="Recálculo con datos reales, una oferta en varios expedientes, servicio añadido tras "
                           "aceptar", epic="E6", type=T.DEV, sprint="S43", points=8, start=D(2026, 10, 23),
         due=D(2026, 10, 23), priority=P.HIGH, deps=["R04"], hours=12, who="belal", dept="sys", status=S.DONE,
         done=D(2026, 10, 23),
         desc=desc(RETRO, "Resultado: coste previsto recalculado con los datos del expediente (historial de "
                          "recálculos), reparto de una oferta aceptada entre expedientes, servicio BOSS o de "
                          "proveedor añadido tras la aceptación con motivo y foto."),
         evidence="Commits 344bd0f y b318401 (23/10/2026); pruebas test_file_followup (6 métodos); boss20 "
                  "E260003 (CSA), E260009/E260010 (reparto).", links=[f"{DOC}#/anadir-servicios"]),
    dict(code="R06", title="Guía de usuario ES/EN publicada en doc.bosscontinental.com/new", epic="E5",
         type=T.DOCS, sprint="S43", points=5, start=D(2026, 10, 21), due=D(2026, 10, 23), priority=P.HIGH,
         deps=[], hours=12, who="belal", dept="sys", status=S.DONE, done=D(2026, 10, 23),
         desc=desc(RETRO, "Resultado: 30 páginas ES/EN (ciclo, roles, tarifas, métodos, servicios, expediente, "
                          "compras, facturación, rentabilidad, almacenaje, decisiones) con capturas reales."),
         evidence="Commits 45220ef (21/10) … 0192e66 (23/10, versión 20261023g); páginas verificadas con curl el "
                  "23/10.", links=[DOC]),
    dict(code="R07", title="Despliegue en boss20 (8ec4a2c) y configuración de las decisiones del 23/10", epic="E5",
         type=T.INFRA, sprint="S43", points=3, start=D(2026, 10, 23), due=D(2026, 10, 23), priority=P.CRITICAL,
         deps=["R04"], hours=4, who="belal", dept="sys", status=S.DONE, done=D(2026, 10, 23),
         desc=desc(RETRO, "Resultado: módulos desplegados con la web parada; tabla de IVA (Art.22, CAN), tipo de "
                          "cambio, bloqueo de pago, control por cantidades recibidas, suplidos (419000: ver D-2)."),
         evidence="Commit 8ec4a2c desplegado el 23/10 (dev/deploy.sh); lectura de boss20 del 26/10: versiones "
                  "instaladas iguales al commit, ajustes de compañía aplicados.", links=[SYS]),
    dict(code="R08", title="Muestras de tarifas reales cargadas y enviadas a aprobación (MSC, WFS, IRENEO, CMA, "
                           "Hapag)", epic="E8", type=T.MIGRATION, sprint="S43", points=5, start=D(2026, 10, 21),
         due=D(2026, 10, 22), priority=P.HIGH, deps=["021"], hours=8, who="belal", dept="sys", status=S.DONE,
         done=D(2026, 10, 22),
         desc=desc(RETRO, "Resultado: 10 tarifas [MUESTRA] desde documentos reales, cada precio con página; "
                          "ejemplos de referencia R1–R27 y prueba automática con las muestras privadas."),
         evidence="Commit 31d64ee (21/10); boss20: 10 tarifas esperando aprobación, 0 aprobadas (lectura del "
                  "26/10); docs/revision-tarifas.md.", links=[f"{DOC}#/tarifa-aprobacion"]),
    dict(code="R09", title="Decisiones del 23/10 (P03–P44) aprobadas por Belal y documentadas", epic="E5",
         type=T.DOCS, sprint="S43", points=2, start=D(2026, 10, 23), due=D(2026, 10, 23), priority=P.HIGH,
         deps=[], hours=4, who="belal", dept="dir", status=S.DONE, done=D(2026, 10, 23),
         desc=desc(RETRO, "Resultado: propuestas aprobadas por Belal con fase A/B/C; pendientes de ratificación "
                          "por Ángel (finanzas, IVA) y Cristina (servicios, precios, operaciones)."),
         evidence="Commit 8ec4a2c (docs) y 367cbcd (26/10, columna «Ratificación»); guía «Decisiones pendientes».",
         links=[f"{DOC}#/preguntas"]),
    dict(code="R10", title="Rendimiento medido en navegador real (0,95–1,47 s por pantalla)", epic="E12",
         type=T.TEST, sprint="S43", points=2, start=D(2026, 10, 23), due=D(2026, 10, 23), priority=P.MEDIUM,
         deps=["R07"], hours=3, who="belal", dept="sys", status=S.DONE, done=D(2026, 10, 23),
         desc=desc(RETRO, "Resultado: tiempos de carga de formulario y lista en Chrome con sesión normal; las "
                          "esperas de 20–50 s eran del panel oculto del navegador interno, no del servidor."),
         evidence="docs/ciclo-operativo.md (registro del 23/10); dev/perf_probe.py.", links=[]),
    # ===================================================================== S44 · 26 oct–1 nov
    dict(code="W01", title="Hoja de pruebas de Ángel, copia local aislada y ensayo de los 8 casos", epic="E7",
         type=T.TEST, sprint="S44", points=5, start=D(2026, 10, 26), due=D(2026, 10, 26), priority=P.HIGH,
         deps=["R07"], hours=8, who="belal", dept="sys", status=S.DONE, done=D(2026, 10, 26),
         desc="Resultado: docs/pruebas-angel.md (8 casos, 90 min, entorno por caso); copia local aislada "
              "(dev/test.sh uat: sin tareas programadas, correo ni servicios en línea); ensayo deshecho que "
              "descubrió los defectos D-1 y D-2.",
         evidence="Commits 367cbcd y e04500f (26/10/2026); aislamiento comprobado (ProxyError, 0 crons).",
         links=[]),
    dict(code="W02", title="Revisión de tarifas para Cristina y especificación de la venta única de ALM (P43)",
         epic="E8", type=T.DOCS, sprint="S44", points=3, start=D(2026, 10, 26), due=D(2026, 10, 26),
         priority=P.HIGH, deps=["R08"], hours=5, who="belal", dept="sys", status=S.DONE, done=D(2026, 10, 26),
         desc="Resultado: docs/revision-tarifas.md (10 tarifas: documento, vigencia, servicios, ámbito, decisión) y "
              "docs/especificacion-alm-venta.md (regla del 25/09 leída en Odoo 19, 14 puntos por decidir).",
         evidence="Commit 367cbcd (26/10/2026).", links=[]),
    dict(code="W03", title="Mapeo de Hoja1 y plan de lanzamiento semanal en la plataforma", epic="E1", type=T.DOCS,
         sprint="S44", points=5, start=D(2026, 10, 26), due=D(2026, 10, 26), priority=P.HIGH, deps=[], hours=8,
         who="belal", dept="dir", status=S.DONE, done=D(2026, 10, 26), progress=90,
         desc="Resultado: docs/mapeo-hoja1.md (28 requisitos con estado, prueba, evidencia y tareas) y este plan "
              "(sprints semanales hasta el 1/1/2027) sembrado en la plataforma. Revisión: Belal.",
         evidence="Cerrada el 26/10/2026 tras la revisión de Belal: plan aplicado con sus correcciones (decisiones "
                  "W04 separadas en tareas, GitHub y Mac en la semana actual, seguimiento semanal hasta el 8/1/2027, "
                  "horas y capacidad por sprint, requisitos de Hoja1 con el tipo de falta) y verificado releyendo la "
                  "plataforma; docs/mapeo-hoja1.md en el repositorio (commit del 26/10).",
         links=["https://task.bosscontinental.com/gantt/"]),
    dict(code="W04", title="Decisión de Belal: cuentas de suplidos en boss20 (D-2), corrección D-1 y publicación de "
                           "la guía", epic="E7", type=T.ANALYSIS, sprint="S44", points=1, start=D(2026, 10, 26),
         due=D(2026, 10, 27), priority=P.CRITICAL, deps=["W01"], hours=1, who="belal", dept="dir", status=S.DONE,
         done=D(2026, 10, 26),
         desc=desc("Tres decisiones aplazadas el 26/10 por Belal hasta terminar el plan:",
                   "1) D-2: volver ARA, IVA, PLA y DUM a las cuentas de la categoría (estado anterior al 23/10) hasta "
                   "que Ángel fije las cuentas de suplidos (hoy 419000, cuenta a pagar, impide facturar). Cambio "
                   "contable en boss20.",
                   "2) D-1: corregir el bloqueo de pago para que no cuente líneas de cantidad 0 (código + prueba, "
                   "sin desplegar hasta la decisión).",
                   "3) Publicar la guía corregida (ratificaciones pendientes) en doc.bosscontinental.com.",
                   "Aceptación: respuesta registrada en esta tarea; las tareas W05, W06 y W07 se ejecutan según ella."),
         evidence="Decisiones de Belal del 26/10/2026: 1) D-1: corrección local con pruebas aprobada; el despliegue en "
                  "boss20 es una tarea aparte tras la verificación (W09). 2) D-2: preparar el mapa de cuentas, la "
                  "corrección y las pruebas de facturación en local y presentarlas a Ángel; el cambio contable en boss20 "
                  "depende de que apruebe el mapa (W10); la vuelta a las cuentas de la categoría NO se aprueba. 3) Guía: "
                  "publicar la versión corregida tras verificar la construcción, con los defectos y decisiones "
                  "pendientes explicados (W07).", links=[]),
    dict(code="W05", title="Corregir D-1: el bloqueo de pago ignora las líneas de cantidad 0 (código + prueba)",
         epic="E7", type=T.FIX, sprint="S44", points=2, start=D(2026, 10, 27), due=D(2026, 10, 28),
         priority=P.HIGH, deps=["W04"], hours=3, who="belal", dept="sys", status=S.DONE, done=D(2026, 10, 26),
         desc=desc("Resultado: `_boss_bill_needs` (boss_expediente/models/account_move.py) no cuenta las líneas "
                   "de factura con cantidad 0; prueba en test_file_followup.",
                   "Fuente: defecto D-1 del ensayo del 26/10 (docs/pruebas-angel.md).",
                   "Aceptación: prueba nueva en verde; pago permitido tras facturar al cliente aunque el pedido "
                   "tenga servicios sin prestar. El despliegue en boss20 es la tarea W09."),
         evidence="Corregido el 26/10/2026: boss_expediente/models/account_move.py (_boss_bill_needs ignora las líneas "
                  "con cantidad 0) y prueba test_zero_quantity_bill_lines_do_not_hold_the_payment en verde (BD "
                  "desechable, dev/test.sh run boss_expediente).", links=[]),
    dict(code="W06", title="D-2: mapa de cuentas de suplidos (como Odoo 17), corrección y pruebas de facturación en local; propuesta a Ángel", epic="E7",
         type=T.FIX, sprint="S44", points=2, start=D(2026, 10, 27), due=D(2026, 10, 27), priority=P.CRITICAL,
         deps=["W04"], hours=3, who="belal", dept="sys", status=S.DONE, done=D(2026, 10, 26),
         desc=desc("Resultado: ARA, IVA, PLA y DUM se pueden facturar al cliente y registrar como factura del "
                   "agente en boss20.",
                   "Fuente: defecto D-2 (419000 es cuenta a pagar; Odoo 17 usa 419001–419007 de pasivo corriente).",
                   "Decisión de Belal (26/10, W04-2): preparar en local el mapa de cuentas, la corrección y las "
                   "pruebas y presentarlas a Ángel; la reversión a las cuentas de la categoría no se aprueba. El "
                   "cambio en boss20 es la tarea W10, que depende de la aprobación de Ángel (A02).",
                   "Aceptación: docs/cuentas-suplidos.md, script dev/setup_suplidos_accounts.py y prueba automática en "
                   "verde (factura del agente y factura al cliente con las cuentas propuestas)."),
         evidence="Hecho el 26/10/2026: docs/cuentas-suplidos.md (mapa 419001–419007 como Odoo 17, preguntas para "
                  "Ángel), dev/setup_suplidos_accounts.py (bloqueado en boss20 sin aprobación) y prueba "
                  "test_paid_on_behalf_on_current_liability_accounts en verde.", links=[f"{DOC}#/facturacion"]),
    dict(code="W07", title="Publicar la guía corregida (ratificaciones pendientes, decisiones abiertas)", epic="E5",
         type=T.DOCS, sprint="S44", points=1, start=D(2026, 10, 27), due=D(2026, 10, 28), priority=P.MEDIUM,
         deps=["W04"], hours=1, who="belal", dept="sys", status=S.DONE, done=D(2026, 10, 26),
         desc="Resultado: doc.bosscontinental.com/new con las páginas del commit 367cbcd (decisiones con columna "
              "«Ratificación», cuestiones contables abiertas, D-1 y D-2). Aceptación: la página «Decisiones "
              "pendientes» muestra «Ratificación» y los defectos D-1 y D-2 (comprobado con curl).",
         evidence="Publicada el 26/10/2026 (versión 20261026a) tras construir la guía (30 páginas, sin fuentes "
                  "ausentes); comprobado con curl que la página de decisiones muestra «Ratificación» y «Defectos "
                  "conocidos».", links=[f"{DOC}#/preguntas"]),
    dict(code="W08", title="Usuarios de boss20 para Ángel, Cristina y operaciones, con sus roles", epic="E11",
         type=T.INFRA, sprint="S44", points=2, start=D(2026, 10, 27), due=D(2026, 10, 28), priority=P.HIGH,
         deps=[], hours=2, who="belal", dept="sys", status=None, done=None,
         desc=desc("Resultado: usuarios internos en boss20 (hoy solo existe el de Belal): Ángel (Contabilidad "
                   "administrador, Ventas todos los documentos, Compras usuario), Cristina (Ventas administrador, "
                   "Compras, aprobador de tarifas) y los que indique Cristina para operaciones; sin servidor de "
                   "correo, las contraseñas se entregan en persona.",
                   "Aceptación: cada persona entra y ve lo que define docs/guide «Roles» (prueba con captura)."),
         evidence=None, links=[f"{DOC}#/roles"]),
    dict(code="A01", title="Sesión con Ángel: hoja de pruebas (8 casos) y ratificación de las decisiones contables",
         epic="E7", type=T.TEST, sprint="S44", points=3, start=D(2026, 10, 29), due=D(2026, 10, 30),
         priority=P.CRITICAL, deps=["W01", "W08"], hours=3, who="belal", dept="fin", status=None, done=None,
         desc=desc("Resultado: docs/pruebas-angel.md cumplimentada (resultado real por caso) y las decisiones de "
                   "Ángel registradas: P17, P30, P31, P32, P03, P11, P38, P39, P33; cuentas de suplidos (D-2); IVA "
                   "de CAU/QBR; impuestos de compra por tipo de factura; QBR; margen mínimo; SII/VeriFactu (P45).",
                   "Entornos: boss20 solo borradores; contabilizar y pagar en la copia local aislada.",
                   f"Convoca Belal; participa Ángel. {NOT_COMMITTED}",
                   "Aceptación: hoja firmada y docs/preguntas-abiertas.md actualizado con fecha y fuente."),
         evidence=None, links=[f"{DOC}#/preguntas"]),
    dict(code="A02", title="Ángel: cuentas de suplidos por concepto y sentido, y cuentas por categoría (P18, P37)",
         epic="E7", type=T.ANALYSIS, sprint="S44", points=2, start=D(2026, 10, 29), due=D(2026, 11, 4),
         priority=P.CRITICAL, deps=["A01"], hours=2, who="angel", dept="fin", status=None, done=None,
         desc=desc("Decisión: qué cuentas usan los suplidos (ARA, IVA, PLA, DUM) al facturar al cliente y al "
                   "registrar la factura del agente. Odoo 17 usa 419001 IVA repercutido, 419002 aranceles "
                   "repercutidos, 419003 IVA soportado, 419004 aranceles soportados, 419005 antidumping, 419006 y "
                   "419007 plástico (pasivo corriente). Y las cuentas de ingreso y gasto por categoría de servicio.",
                   f"Mientras tanto: cuentas de la categoría. {NOT_COMMITTED}",
                   "Aceptación: lista de cuentas por concepto firmada; aplicada en W06."),
         evidence=None, links=[f"{DOC}#/preguntas"]),
    dict(code="A03", title="Ángel: SII o VeriFactu y declaraciones que debe preparar Odoo 20 desde el arranque (P45)",
         epic="E7", type=T.ANALYSIS, sprint="S44", points=2, start=D(2026, 10, 29), due=D(2026, 11, 6),
         priority=P.CRITICAL, deps=["A01"], hours=2, who="angel", dept="fin", status=None, done=None,
         desc=desc("Decisión: si BOSS debe enviar facturas a la AEAT (SII o VeriFactu) desde el 1/1/2027 y qué "
                   "modelos (303, 349, 390…) genera Odoo 20. Hoy boss20 no tiene ningún módulo SII ni VeriFactu "
                   "(lectura del 26/10) y nada se envía.",
                   f"{NOT_COMMITTED}",
                   "Aceptación: decisión escrita; si aplica, tarea de instalación y configuración (N06)."),
         evidence=None, links=[]),
    dict(code="A04", title="Ángel: IVA de CAU y QBR para cliente español, porcentaje de QBR, margen mínimo y "
                           "CAU/SEG (P17, P03, P01/P02, P13)", epic="E7", type=T.ANALYSIS, sprint="S45", points=2,
         start=D(2026, 10, 29), due=D(2026, 11, 6), priority=P.HIGH, deps=["A01"], hours=2, who="angel",
         dept="fin", status=None, done=None,
         desc=desc("Decisiones de IVA y finanzas sin respuesta supuesta: impuesto de los NS que no son suplidos "
                   "(CAU, QBR) para cliente español; porcentaje del quebranto y factura en EUR de pedido en USD; "
                   "valor del margen mínimo y quién aprueba vender por debajo; porcentajes y mínimos de CAU y SEG "
                   "(con Cristina).",
                   f"Mientras tanto: IVA pendiente en esos casos; sin QBR; sin margen mínimo. {NOT_COMMITTED}"),
         evidence=None, links=[f"{DOC}#/preguntas"]),
    dict(code="C01", title="Cristina: revisión y aprobación de las 10 tarifas de muestra (P19) y ratificación de las "
                           "lecturas WFS", epic="E8", type=T.ANALYSIS, sprint="S44", points=3,
         start=D(2026, 10, 28), due=D(2026, 10, 30), priority=P.CRITICAL, deps=["W02", "W08"], hours=3,
         who="cristina", dept="com", status=None, done=None,
         desc=desc("Resultado: cada tarifa [MUESTRA] (MSC ×3, WFS ×2, CMA CGM, Hapag-Lloyd, IRENEO ×3) revisada con "
                   "su PDF y los ejemplos de docs/ejemplos-referencia.md, y aprobada, devuelta a borrador con la "
                   "corrección, o no aprobada (IRENEO 2025 no se prorroga). Lecturas WFS P40, P41, P29, P42 "
                   "ratificadas o cambiadas.",
                   "Fuente: Hoja1 fila 7 y 10 (H1-01, 05, 12, 14, 15, 16, 20, 25, 27, 28); docs/revision-tarifas.md.",
                   "Ojo: 8 de las 10 llegaron sin «Ámbito revisado»; revisarlo antes de aprobar.",
                   f"Convoca Belal; aprueba Cristina en Tarifas → Esperando aprobación. {NOT_COMMITTED}",
                   "Aceptación: estado de cada tarifa en boss20 cambiado por Cristina; tras aprobar, prueba del "
                   "escenario de referencia con una oferta en borrador (tarea D04)."),
         evidence=None, links=[f"{DOC}#/tarifa-aprobacion"]),
    dict(code="C02", title="Cristina: decisiones pendientes de servicios (VET, GLO por documento, Lejano Oriente, DET, "
                           "ETX, venta ALM D1–D7, servicios sin definir, numeración)", epic="E8",
         type=T.ANALYSIS, sprint="S44", points=3, start=D(2026, 10, 28), due=D(2026, 11, 4), priority=P.CRITICAL,
         deps=["W02"], hours=3, who="cristina", dept="ops", status=None, done=None,
         desc=desc("Decisiones que bloquean Hoja1: VET (H1-11, P16), qué GLO por documento se proponen solos "
                   "(H1-13), lista de países «Lejano Oriente» (H1-14, P24), DET código propio o dentro de DEM (H1-17, "
                   "P09), ETX concepto y unidad (H1-25, P10), venta única de ALM puntos D1–D7 de "
                   "docs/especificacion-alm-venta.md (P43), servicios por definir o retirar (P16), numeración "
                   "E26xxxx al arrancar (P36), acuerdos de varios envíos (P34).",
                   f"{NOT_COMMITTED}",
                   "Aceptación: respuestas escritas en docs/preguntas-abiertas.md con fecha; las tareas B01, B03 y "
                   "D02 se desbloquean."),
         evidence=None, links=[f"{DOC}#/preguntas"]),
    dict(code="C03", title="Cristina: tarifa IRENEO 2026 o confirmación escrita de los precios 2025 (P28)", epic="E8",
         type=T.ANALYSIS, sprint="S44", points=1, start=D(2026, 10, 28), due=D(2026, 11, 6), priority=P.HIGH,
         deps=[], hours=1, who="cristina", dept="ops", status=None, done=None,
         desc=desc("Resultado: documento IRENEO 2026 (HAN, X-R, TTE-CON, SEG, FS) o confirmación escrita; las "
                   "tarifas de 2025 no se prorrogan (Hoja1 H1-20).", f"{NOT_COMMITTED}",
                   "Aceptación: documento en la carpeta NEW ODOO y tarifa nueva cargada (D02)."),
         evidence=None, links=[f"{DOC}#/srv-TTE-CON"]),
    dict(code="D01", title="Reunir los documentos de tarifa que faltan (lista del 07/10: aduanas, Hapag, Transglory, "
                           "PFT, inspecciones, CES, navieras D&D, 2.º handler)", epic="E8", type=T.MIGRATION,
         sprint="S44", points=3, start=D(2026, 10, 27), due=D(2026, 11, 4), priority=P.CRITICAL, deps=[], hours=6,
         who="cristina", dept="ops", status=None, done=None,
         desc=desc("Resultado: en la carpeta NEW ODOO los documentos vigentes: Aducex y Ramos Vila (FAD), agente de "
                   "exportación (DEX), gastos locales Hapag-Lloyd (T3, THC, CES), CFS Transglory (THC-LCL), "
                   "acuerdos PFT de los agentes, precios por documento (ROH, SOI, INS, SAN, VET), cesión CES, "
                   "D&D de ONE, MSK, ZIM y OOCL, y el segundo handler aéreo (IAS o SAASA: import y export).",
                   "Fuente: Hoja1 filas 7 y 10; hoja «Documentos no encontrados» del 07/10 (37 servicios sin "
                   "documento el 26/10: docs/revision-tarifas.md).",
                   f"Responsable: Pendiente de asignar (propuesta del 07/10: Laura / operaciones; Cristina "
                   f"coordina). {NOT_COMMITTED}",
                   "Aceptación: cada documento con proveedor, edición y vigencia; lo que no exista se anota como "
                   "«no existe» para usar coste manual con justificante."),
         evidence=None, links=[f"{DOC}#/sin-precio"]),
    dict(code="F03", title="Extraer de Odoo 17 la lista aerolínea / aeropuerto / handling y proponer la asociación "
                           "(Hoja1 C10)", epic="E8", type=T.ANALYSIS, sprint="S44", points=3, start=D(2026, 10, 29),
         due=D(2026, 10, 30), priority=P.HIGH, deps=[], hours=4, who="belal", dept="sys", status=None, done=None,
         desc=desc("Resultado: script de solo lectura sobre Odoo 17 (expedientes aéreos: aerolínea, aeropuerto, "
                   "handler usado) y lista en .research (datos reales, fuera de Git) para que Cristina valide la "
                   "asociación.",
                   "Estado real 26/10: no implementado (H1-26).",
                   "Aceptación: lista validada por Cristina; sirve de carga para F02."),
         evidence=None, links=[]),
    dict(code="N01", title="Alcance de la migración de Odoo 17: qué datos, qué expedientes abiertos, fecha de corte",
         epic="E9", type=T.ANALYSIS, sprint="S44", points=2, start=D(2026, 10, 28), due=D(2026, 10, 30),
         priority=P.CRITICAL, deps=[], hours=3, who="belal", dept="dir", status=None, done=None,
         desc=desc("Decisión de Belal con Cristina: maestros (clientes, proveedores, roles, puertos, tipos de "
                   "contenedor, aerolíneas/handlers), expedientes abiertos a 1/1/2027 (y sus ofertas), histórico "
                   "en Odoo 17 solo lectura; facturas y contabilidad se quedan en Odoo 17 (criterio del mapeo de "
                   "Odoo 19, Q11) salvo que Ángel decida otra cosa.",
                   "Estado real 26/10: no hay ningún script de migración en el repositorio; boss20 no tiene "
                   "clientes ni proveedores reales.",
                   "Aceptación: alcance escrito en docs/migracion.md con criterios de conciliación."),
         evidence=None, links=[]),
    dict(code="TP01", title="Quotation templates with BOSS lines: standard Odoo templates verified on the local copy",
         epic="E6", type=T.TEST, sprint="S44", points=2, start=D(2026, 10, 26), due=D(2026, 10, 26),
         priority=P.CRITICAL, deps=[], hours=3, who="belal", dept="sys", status=S.DONE, done=D(2026, 10, 26),
         desc="Result: a standard Odoo 20 quotation template (sale_management, already installed on boss20) filled a "
              "BOSS quotation with the 7 standard lines of an air import FOB (FAI, HAN, AWB, CSA, FAD, ETX, TTE-CON): "
              "right unit and executor (BOSS/supplier), cost status per line (manual for the freight, 'no tariff' until "
              "a tariff is approved, 'pending decision' for ETX), supplier chosen per line. No new module is needed; "
              "Belal's Odoo 19 template module is not reused.\nSource: meeting of 26/10 with Cristina and Ángel "
              "(Cofitel air import FOB must show its standard services automatically).",
         evidence="Probe dev/uat_template_probe.py on the local copy (rolled back), 26/10/2026: 7 lines created from "
                  "the template through the form onchange, BOSS fields computed on each line.", links=[]),
    dict(code="TP02", title="Create the quotation templates on boss20: air import FOB (Cofitel), sea FCL import, air "
                            "export; standard vs optional services per case", epic="E6", type=T.DEV, sprint="S44",
         points=3, start=D(2026, 10, 27), due=D(2026, 10, 29), priority=P.CRITICAL, deps=["TP01"], hours=5,
         who="belal", dept="sys", status=S.IN_PROGRESS, done=None, progress=90,
         desc="Result: [DEMO] templates on boss20, selectable (no default template for every quotation; no tariff or "
              "accounting setting changed). Done 26/10: «[DEMO] Importación aérea FOB» from the real Cofitel offer "
              "05570 (FAI, HAN, AWB, CSA, FAD, ETX, TTE-CON: 7 of the 8 lines of the offer; the 8th, origin pickup "
              "Shenzhen, is left out because its code is not confirmed, see TP03); «[DEMO] Importación marítima FCL» "
              "(reference: [DEMO] quotation S00009 of the guide and the MSC 2026 local charges document) and «[DEMO] "
              "Exportación aérea» (reference: WFS export tariff) as proposals. Code c1091b9 deployed: template lines "
              "are counted from the shipment and container services split per container group. Draft quotation "
              "S00024 «[DEMO] Caso Cofitel — Importación aérea» on boss20 shows the 7 lines (HAN 500 kg and AWB priced "
              "with [DEMO] tariffs, FAI manual, FAD and TTE-CON without tariff, ETX pending decision).\nRemaining: "
              "Cristina confirms the three lists (TP03); then the names lose «Cristina confirma».",
         evidence="26/10/2026: dev/setup_templates.py on boss20 (templates 1–3, quotation S00024 with 7 lines, HAN "
                  "500 kg); deploy log deploy_20261026 (c1091b9); test test_quotation_template_lines_count_the_shipment "
                  "green (16/16 boss_pricing_sale).", links=[f"{DOC}#/oferta-envio"]),
    dict(code="TP03", title="Cristina: services that ALWAYS apply per case (direction × mode × Incoterm) and services "
                            "that apply SOMETIMES, with a real Odoo 17 file as reference", epic="E8", type=T.ANALYSIS,
         sprint="S44", points=2, start=D(2026, 10, 27), due=D(2026, 10, 30), priority=P.CRITICAL, deps=[], hours=2,
         who="cristina", dept="ops", status=None, done=None,
         desc=desc("Searched first (Belal's rule 26/10): Odoo 19 project + database boss_uat, Odoo 17 concepts, Boss-Project "
                   "knowledge base, PrevAdder C# code, Cristina's NEW ODOO files. Findings in docs/respuestas-cristina.md: "
                   "case codes decoded (B13, approved); the service-proposal rule of Odoo 19 (Cristina's 'paso cero', 31/08) "
                   "with the per-case lists read from boss_uat (classification by Belal 15/10, not validated); Incoterm only "
                   "decides the invoiced party; ETX = energy tax of the handlers on air import (WFS, Iberia, Swissport), "
                   "bought per AWB, sold per shipment, VAT NR; three ALM sale rules in the sources (PrevAdder/offers vs "
                   "25/09); EPX exists nowhere; TRE/TRI/TCC/TTC retired for TTE; multi-shipment agreements exist in Odoo 17 "
                   "(boss_market); numbering format E26xxxx.",
                   "What still needs Cristina (short list, each with a proposal in docs/respuestas-cristina.md §3): 1) validate "
                   "the always/sometimes lists per case (IAB, IMB, EAB, EMB) and whether they change with the Incoterm; "
                   "2) ALM sale rule: 25/09 (48 h, day 8) or offers (3 days, day 10/20), DHL variant; 3) origin pickup of a "
                   "FOB air import = EXW-AIR per document?; 4) what «EPX» meant; 5) Far East list; 6) VET and DET proposals; "
                   "7) IRENEO 2026 (C03). No longer asked: meaning of case codes, role of the Incoterm, ETX concept and scope, "
                   "retired services, numbering format, CRM not mandatory, GLO per document, multi-shipment model, minimum "
                   "margin (Angel).", NOT_COMMITTED,
                   "Acceptance: Cristina answers the 7 points on the draft; templates TP02 updated from them."),
         evidence="Research of 26/10/2026 documented in docs/respuestas-cristina.md (sources listed there); matrix extract in .research/matriz-odoo19.txt.", links=[]),
    dict(code="TP04", title="Demo of the next meeting: Cofitel air import FOB end to end (quotation from template → "
                            "costs → confirm → file → ATA/Pickup → recompute), run by Cristina", epic="E5",
         type=T.TRAINING, sprint="S44", points=2, start=D(2026, 10, 29), due=D(2026, 10, 30), priority=P.CRITICAL,
         deps=["TP02", "W08", "F01"], hours=3, who="belal", dept="dir", status=S.IN_PROGRESS, done=None, progress=60,
         desc=desc("Result: one-page demo script; environment ready BEFORE the meeting (templates, [DEMO] customer or "
                   "Cofitel entered as test customer, users for Cristina and Ángel, WFS tariff approved or [DEMO] "
                   "tariff); Cristina runs the flow herself; what works / what fails recorded; decisions TP03, C02 and "
                   "A02 taken in the meeting.", NOT_COMMITTED),
         evidence="Rehearsal on boss20 on 26/10/2026 (dev/tp04_accept_s00024.py): «Confirm» on S00024 as it comes from the "
                  "template is blocked with the list of lines without sale price (expected); after completing shipment "
                  "data, a manual freight cost, sale prices and the reason for the three services without tariff, the "
                  "acceptance opened file E260013 with the 7 services once (none missing, none duplicated); recompute "
                  "with AWB 500 → 620 kg changed the HAN need and kept the sale unchanged. Defect found and fixed on the "
                  "way: with «Lock confirmed sales» on, acceptance failed (commit 5c83693, tests 16/16 on the server, "
                  "deployed). Pending: Cristina runs it herself from the interface in the meeting.",
         links=[f"{DOC}#/demo-ciclo", f"{SYS}/odoo/action-sale.action_quotations_with_onboarding/24"]),
    # ===================================================================== S45 · 2–8 nov
    dict(code="D02", title="Cargar y enviar a aprobación las tarifas recibidas (lote 1: aduanas, Hapag, Transglory, "
                           "inspecciones, IRENEO 2026) con ejemplos de referencia", epic="E8", type=T.MIGRATION,
         sprint="S45", points=8, start=D(2026, 11, 3), due=D(2026, 11, 6), priority=P.CRITICAL,
         deps=["D01", "C03"], hours=12, who="belal", dept="sys", status=None, done=None,
         desc=desc("Resultado: cada documento recibido cargado como tarifa (precio con página, ámbito revisado), "
                   "enviado a aprobación; ejemplo de referencia por servicio y prueba de referencias en verde.",
                   "Fuente: Hoja1 H1-01 a H1-10, H1-12, H1-13, H1-18, H1-19, H1-20, H1-28.",
                   "Aceptación: tarifas en «Esperando aprobación» en boss20; docs/ejemplos-referencia.md ampliado; "
                   "aprobación de Cristina (C04)."),
         evidence=None, links=[f"{DOC}#/tarifa-alta"]),
    dict(code="F01", title="Campos NOA y ATA con fecha y hora en el expediente; alimentan el periodo de ALM/DEM/OCU "
                           "(Hoja1 C8, D8)", epic="E6", type=T.DEV, sprint="S44", points=3, start=D(2026, 10, 29),
         due=D(2026, 10, 30), priority=P.HIGH, deps=[], hours=6, who="belal", dept="sys", status=None, done=None,
         desc=desc("Resultado: NOA (fecha y hora) y ATA con hora en «Referencias y fechas» del expediente; al "
                   "rellenarlos se propone el inicio del periodo real de los servicios por tiempo; evento en el "
                   "expediente; recálculo.",
                   "Adelantada a la semana del 26/10 (hueco de capacidad; no depende de ninguna decisión). Estado real 26/10: ATA solo fecha; NOA solo como inicio del periodo del servicio (H1-21, H1-22).",
                   "Aceptación: prueba automática (NOA → periodo ALM → coste recalculado) y captura en la guía."),
         evidence=None, links=[f"{DOC}#/expediente"]),
    dict(code="F02", title="Aerolínea y handling en el expediente, emparejados con el aeropuerto; asociación "
                           "aerolínea → handler (Hoja1 B9, C9)", epic="E6", type=T.DEV, sprint="S45", points=5,
         start=D(2026, 11, 4), due=D(2026, 11, 6), priority=P.HIGH, deps=["F03"], hours=10, who="belal",
         dept="sys", status=None, done=None,
         desc=desc("Resultado: modelo de asociación (aerolínea, aeropuerto → handler) cargado desde F03; en el "
                   "expediente aéreo, al elegir aerolínea y aeropuerto se propone el handler (editable); el "
                   "handler es el proveedor por defecto de HAN, ALM, AWB, ETX.",
                   "Estado real 26/10: no implementado (H1-23, H1-24). Cristina 28/09: asociación «más adelante»; "
                   "se hace ahora porque Hoja1 la pide.",
                   "Aceptación: prueba automática y oferta [DEMO] aérea con handler propuesto."),
         evidence=None, links=[f"{DOC}#/expediente"]),
    dict(code="B01", title="Fase B1: venta única de ALM (tarifa de venta con el motor por tiempo + regla de lista; "
                           "ADR-006)", epic="E4", type=T.DEV, sprint="S45", points=8, start=D(2026, 11, 3),
         due=D(2026, 11, 6), priority=P.HIGH, deps=["C02"], hours=14, who="belal", dept="sys", status=None,
         done=None,
         desc=desc("Resultado: según docs/especificacion-alm-venta.md: tarifa de venta BOSS (aprobada por Cristina), "
                   "base nueva de lista de precios «Tarifa de venta BOSS», precio con explicación en la oferta, "
                   "foto al aceptar; pruebas E1–E6 del motor y una oferta con ALM.",
                   "Bloqueo: necesita las respuestas D1–D7 de Cristina (C02). Los importes reales quedan fuera "
                   "de Git.",
                   "Aceptación: pruebas en verde; oferta [DEMO] con ALM muestra el precio y su explicación."),
         evidence=None, links=[f"{DOC}#/almacenaje"]),
    dict(code="B03", title="Fase B3: ETX (compra por AWB máster, venta por expediente) y DET (código propio o "
                           "dentro de DEM)", epic="E4", type=T.DEV, sprint="S45", points=3, start=D(2026, 11, 5),
         due=D(2026, 11, 6), priority=P.HIGH, deps=["C02"], hours=5, who="belal", dept="sys", status=None,
         done=None,
         desc=desc("Resultado: ETX y DET configurados (unidad, método, modo de coste) con el documento del "
                   "proveedor; DET de MSC exportación cargado si procede (Hoja1 H1-17, H1-25).",
                   "Aceptación: ejemplo de referencia por servicio y prueba en verde."),
         evidence=None, links=[f"{DOC}#/catalogo"]),
    dict(code="B02", title="Fase B2: QBR — factura en EUR de una oferta en USD con el tipo de la naviera y línea de "
                           "quebranto", epic="E7", type=T.DEV, sprint="S45", points=5, start=D(2026, 11, 5),
         due=D(2026, 11, 6), priority=P.MEDIUM, deps=["A04"], hours=8, who="belal", dept="sys", status=None,
         done=None,
         desc=desc("Resultado: asistente «Facturar servicios» con moneda de la factura; línea QBR con el porcentaje "
                   "aprobado; diferencia de cambio registrada como decida Ángel.",
                   "Bloqueo: porcentaje y tratamiento contable (A04).",
                   "Aceptación: prueba con un pedido en USD facturado en EUR en BD desechable."),
         evidence=None, links=[f"{DOC}#/iva-moneda"]),
    dict(code="P01", title="Informe de previsiones: expedientes con venta, coste previsto y real, margen, fechas, "
                           "por semana y mes (lista y pivot)", epic="E10", type=T.DEV, sprint="S45", points=5,
         start=D(2026, 11, 4), due=D(2026, 11, 6), priority=P.HIGH, deps=[], hours=10, who="belal", dept="sys",
         status=None, done=None,
         desc=desc("Resultado: vista de lista y pivot sobre expedientes y sus servicios (venta acordada, coste en la "
                   "aceptación, comprometido, real, previsto, márgenes, facturado, cobrado, pagado) filtrable por "
                   "estado, cliente, modo y fechas (ETD/ETA/ATA/NOA); exportable.",
                   "Fuente: Hoja1 «PREVISIONES» (A6); informe de previsiones de Odoo 17 (extensión).",
                   "Estado real 26/10: las cifras existen por expediente («Resumen» y «Dónde salen las cifras»); no "
                   "hay vista agregada.",
                   "Aceptación: Cristina valida las columnas con los [DEMO]; cuadra con el resumen de cada expediente."),
         evidence=None, links=[f"{DOC}#/rentabilidad"]),
    dict(code="N02", title="Migración: mapeo de campos y script de lectura de Odoo 17 (maestros y expedientes "
                           "abiertos) probado en la copia local", epic="E9", type=T.MIGRATION, sprint="S45",
         points=8, start=D(2026, 11, 3), due=D(2026, 11, 6), priority=P.CRITICAL, deps=["N01"], hours=14,
         who="belal", dept="sys", status=None, done=None,
         desc=desc("Resultado: docs/migracion.md con el mapeo por grupo (clientes y proveedores con "
                   "deduplicación por NIF y nombre, roles, puertos, tipos de contenedor, aerolíneas/handlers, "
                   "expedientes abiertos con partes, contenedores, referencias y fechas); script de solo lectura "
                   "de Odoo 17 y carga en la copia local con informe de calidad (duplicados, sin NIF, zonas).",
                   "Aceptación: carga en la copia local sin errores; conteos legacy = nuevos; lista de revisión "
                   "humana para los casos dudosos."),
         evidence=None, links=[]),
    dict(code="C04", title="Cristina: aprobación de las tarifas del lote 1 y validación de la lista aerolínea/handler",
         epic="E8", type=T.ANALYSIS, sprint="S45", points=2, start=D(2026, 11, 5), due=D(2026, 11, 6),
         priority=P.CRITICAL, deps=["D02", "F03"], hours=2, who="cristina", dept="com", status=None, done=None,
         desc=desc("Resultado: tarifas del lote 1 aprobadas (o devueltas con corrección) y lista aerolínea / "
                   "aeropuerto / handler validada.", f"{NOT_COMMITTED}",
                   "Aceptación: estados cambiados en boss20; lista firmada."),
         evidence=None, links=[f"{DOC}#/tarifa-aprobacion"]),
    dict(code="D04", title="Probar el escenario de referencia de cada tarifa aprobada con una oferta en borrador",
         epic="E8", type=T.TEST, sprint="S45", points=2, start=D(2026, 11, 5), due=D(2026, 11, 6),
         priority=P.HIGH, deps=["C01"], hours=4, who="belal", dept="sys", status=None, done=None,
         desc=desc("Resultado: por cada tarifa aprobada, una oferta en borrador (cliente de prueba no DEMO) con los "
                   "datos del ejemplo de referencia da el coste del ejemplo; la oferta no se envía.",
                   "Fuente: condición 5 de docs/revision-tarifas.md.",
                   "Aceptación: tabla tarifa → oferta → coste esperado = obtenido, en docs/ejemplos-referencia.md."),
         evidence=None, links=[f"{DOC}#/seleccion"]),
    # ===================================================================== S46 · 9–15 nov
    dict(code="D03", title="Cargar el segundo handler aéreo (import y export) y HAN/AWB de exportación de WFS "
                           "(Hoja1 B10, D10)", epic="E8", type=T.MIGRATION, sprint="S46", points=5,
         start=D(2026, 11, 10), due=D(2026, 11, 12), priority=P.HIGH, deps=["D01"], hours=8, who="belal",
         dept="sys", status=None, done=None,
         desc=desc("Resultado: HAN, ETX, ALM y AWB del segundo handler (IAS o SAASA) para importación y "
                   "exportación, y los códigos de exportación de WFS que faltan, cargados y enviados a aprobación.",
                   "Estado real 26/10: solo WFS (import: HAN, ALM, AWB; export: ALM, X-R).",
                   "Aceptación: tarifas esperando aprobación; ejemplos de referencia; aprobación de Cristina (C05)."),
         evidence=None, links=[f"{DOC}#/srv-HAN"]),
    dict(code="D05", title="Cargar D&D de ONE, MSK, ZIM y OOCL y gastos locales de otras navieras (lote 2) "
                           "(Hoja1 E10)", epic="E8", type=T.MIGRATION, sprint="S46", points=5,
         start=D(2026, 11, 10), due=D(2026, 11, 13), priority=P.HIGH, deps=["D01"], hours=8, who="belal",
         dept="sys", status=None, done=None,
         desc=desc("Resultado: OCU/DEM/DET de importación de las 5 navieras de Hoja1 (hoy solo MSC; CMA y Hapag "
                   "adicionales) y los gastos locales recibidos, cargados con sus ejemplos.",
                   "Aceptación: tarifas esperando aprobación y prueba de referencias en verde."),
         evidence=None, links=[f"{DOC}#/srv-DEM"]),
    dict(code="C05", title="Cristina: aprobación de las tarifas del lote 2 (handler 2, navieras)", epic="E8",
         type=T.ANALYSIS, sprint="S46", points=2, start=D(2026, 11, 12), due=D(2026, 11, 13), priority=P.HIGH,
         deps=["D03", "D05"], hours=2, who="cristina", dept="com", status=None, done=None,
         desc=desc("Resultado: tarifas del lote 2 aprobadas o devueltas.", f"{NOT_COMMITTED}"),
         evidence=None, links=[f"{DOC}#/tarifa-aprobacion"]),
    dict(code="B04", title="Fase B4/B5: almacenaje especial (condición de tipo de carga, código de almacén) y "
                           "acuerdo de precio para varios envíos", epic="E4", type=T.DEV, sprint="S46", points=5,
         start=D(2026, 11, 10), due=D(2026, 11, 13), priority=P.MEDIUM, deps=["C02"], hours=8, who="belal",
         dept="sys", status=None, done=None,
         desc=desc("Resultado: condición de tipo de carga en las tarifas de ALM, código del almacén fuera del "
                   "aeropuerto si Cristina y Ángel lo aprueban (P44), y acuerdo de precio para varios envíos "
                   "sobre el reparto entre expedientes (P34), si Cristina da los datos.",
                   "Si no hay datos a 9/11, se pasa a la estabilización de diciembre (no es básico para la entrega)."),
         evidence=None, links=[f"{DOC}#/almacenaje"]),
    dict(code="N03", title="Migración de maestros en boss20: clientes, proveedores, roles, puertos, tipos de "
                           "contenedor, aerolíneas y handlers, con validación", epic="E9", type=T.MIGRATION,
         sprint="S46", points=8, start=D(2026, 11, 10), due=D(2026, 11, 12), priority=P.CRITICAL,
         deps=["N02", "C04"], hours=12, who="belal", dept="sys", status=None, done=None,
         desc=desc("Resultado: maestros cargados en boss20 desde Odoo 17 con informe de conciliación (conteos, "
                   "duplicados resueltos, NIF y zonas de IVA, legacy id en «Referencia»); lista de revisión para "
                   "Cristina.",
                   "Aceptación: conteos legacy = nuevos; sin duplicados por NIF; cada cliente con zona de IVA."),
         evidence=None, links=[f"{DOC}#/contactos"]),
    dict(code="U01", title="Permisos por rol, correo saliente y plantillas de oferta y factura (PDF) en boss20",
         epic="E11", type=T.INFRA, sprint="S46", points=5, start=D(2026, 11, 11), due=D(2026, 11, 13),
         priority=P.HIGH, deps=["W08"], hours=8, who="belal", dept="sys", status=None, done=None,
         desc=desc("Resultado: grupos y reglas comprobados con un usuario por rol (comercial, operaciones, "
                   "compras, contabilidad); servidor de correo saliente de BOSS configurado y probado a una cuenta "
                   "interna; plantillas de oferta y factura con los datos legales de BOSS (dirección, NIF, "
                   "condiciones) revisadas por Ángel.",
                   "Aceptación: captura por rol; correo de prueba recibido; PDF de oferta y factura aprobados."),
         evidence=None, links=[f"{DOC}#/roles"]),
    dict(code="P02", title="Informes de facturación y rentabilidad por expediente, cliente y periodo", epic="E10",
         type=T.DEV, sprint="S46", points=3, start=D(2026, 11, 12), due=D(2026, 11, 13), priority=P.MEDIUM,
         deps=["P01"], hours=6, who="belal", dept="sys", status=None, done=None,
         desc=desc("Resultado: facturado, cobrado, pagado y margen por expediente, cliente y mes, a partir de los "
                   "mismos cálculos del resumen del expediente; exportable.",
                   "Aceptación: Ángel valida las columnas con los [DEMO]."),
         evidence=None, links=[f"{DOC}#/rentabilidad"]),
    dict(code="N06", title="SII o VeriFactu: instalar y configurar según la decisión de Ángel (si aplica)", epic="E7",
         type=T.INFRA, sprint="S46", points=5, start=D(2026, 11, 12), due=D(2026, 11, 13), priority=P.HIGH,
         deps=["A03"], hours=8, who="belal", dept="sys", status=None, done=None,
         desc=desc("Resultado: módulo de la localización instalado y configurado en modo de pruebas; envío real "
                   "solo tras el arranque y con la aprobación de Ángel.",
                   "Si Ángel decide que no aplica en 2027, la tarea se cancela con su motivo."),
         evidence=None, links=[]),
    dict(code="Q01", title="Pruebas automáticas completas con todas las tarifas cargadas y corrección de defectos",
         epic="E5", type=T.TEST, sprint="S46", points=3, start=D(2026, 11, 13), due=D(2026, 11, 13),
         priority=P.HIGH, deps=["D02", "F01", "F02", "B01"], hours=6, who="belal", dept="sys", status=None,
         done=None,
         desc="Resultado: motor, referencias (con todas las muestras privadas) y pruebas de Odoo en verde; "
              "defectos abiertos corregidos o registrados con prioridad. Aceptación: 0 fallos registrados en "
              "docs/ciclo-operativo.md con el commit.",
         evidence=None, links=[]),
    dict(code="U02", title="Formación 1: comercial y operaciones (contactos, CRM, oferta, aceptación, expediente, "
                           "compras)", epic="E11", type=T.TRAINING, sprint="S46", points=3, start=D(2026, 11, 13),
         due=D(2026, 11, 13), priority=P.HIGH, deps=["W08", "N03"], hours=4, who="belal", dept="ops",
         status=None, done=None,
         desc=desc("Resultado: sesión de 2 h con la guía como material, sobre los [DEMO] y los maestros migrados; "
                   "dudas registradas como tareas.", f"Participan las personas que indique Cristina. {NOT_COMMITTED}",
                   "Aceptación: asistentes crean una oferta y la aceptan sin ayuda."),
         evidence=None, links=[f"{DOC}#/inicio"]),
    dict(code="I01", title="Entorno de desarrollo en Mac: traslado y verificación (pruebas y despliegue desde el Mac)",
         epic="E12", type=T.INFRA, sprint="S44", points=3, start=D(2026, 10, 27), due=D(2026, 10, 29),
         priority=P.CRITICAL, deps=["007"], hours=5, who="belal", dept="sys", status=None, done=None,
         desc=desc("Resultado: el repositorio, Docker (dev/test.sh), los scripts de despliegue y las claves SSH "
                   "funcionan desde el Mac; pruebas y un despliegue de prueba a la copia local hechos desde él.",
                   "Estado real 26/10: no verificado (sin evidencia en el repositorio de que el traslado esté hecho). Adelantada a esta semana por decisión de Belal (26/10): lentitud del equipo actual.",
                   "Aceptación: `dev/test.sh run boss_expediente` en verde desde el Mac; `dev/deploy.sh` "
                   "ejecutado desde el Mac."),
         evidence=None, links=[]),
    # ===================================================================== S47 · 16–20 nov · Entrega
    dict(code="N04", title="Ensayo completo de migración en la copia local: expedientes abiertos de Odoo 17 → "
                           "Odoo 20 y conciliación", epic="E9", type=T.MIGRATION, sprint="S47", points=8,
         start=D(2026, 11, 16), due=D(2026, 11, 18), priority=P.CRITICAL, deps=["N03"], hours=14, who="belal",
         dept="sys", status=None, done=None,
         desc=desc("Resultado: carga de los expedientes abiertos (partes, contenedores, referencias, fechas, "
                   "servicios con coste previsto) en la copia local; informe de conciliación por expediente "
                   "(conteos y sumas legacy = nuevos, diferencias explicadas); procedimiento repetible para "
                   "cargar diferencias por fecha o id legacy sin duplicar.",
                   "Aceptación: 0 diferencias sin explicar; procedimiento documentado en docs/migracion.md."),
         evidence=None, links=[]),
    dict(code="I02", title="Copias de seguridad automáticas de boss20 (BD y ficheros), restauración probada y plan "
                           "de vuelta atrás", epic="E12", type=T.INFRA, sprint="S47", points=3,
         start=D(2026, 11, 17), due=D(2026, 11, 17), priority=P.CRITICAL, deps=[], hours=5, who="belal",
         dept="sys", status=None, done=None,
         desc=desc("Resultado: copia diaria de la base de datos y del filestore de boss20 fuera del servidor, con "
                   "retención; restauración probada en la copia local; plan de vuelta atrás escrito (Odoo 17 "
                   "sigue intacto hasta el 1/1).",
                   "Aceptación: una restauración completa verificada y documentada con fecha."),
         evidence=None, links=[]),
    dict(code="I03", title="Procedimiento de despliegue y vuelta atrás; rendimiento con datos migrados", epic="E12",
         type=T.INFRA, sprint="S47", points=2, start=D(2026, 11, 18), due=D(2026, 11, 18), priority=P.HIGH,
         deps=["N04", "I02"], hours=4, who="belal", dept="sys", status=None, done=None,
         desc="Resultado: dev/deploy.sh con paso de copia previa y vuelta atrás documentado; medición de tiempos "
              "con los datos migrados (objetivo: < 2 s por pantalla, como el 23/10). Aceptación: medidas en "
              "docs/ciclo-operativo.md.",
         evidence=None, links=[]),
    dict(code="Q02", title="Documentación final: guía ES/EN, ADR, decisiones y migración actualizados", epic="E5",
         type=T.DOCS, sprint="S47", points=3, start=D(2026, 11, 19), due=D(2026, 11, 19), priority=P.HIGH,
         deps=["Q01"], hours=6, who="belal", dept="sys", status=None, done=None,
         desc="Resultado: guía publicada con las pantallas definitivas; ADR-006 (venta ALM); "
              "docs/preguntas-abiertas.md con todas las ratificaciones; docs/migracion.md. Aceptación: publicada y "
              "verificada con curl.",
         evidence=None, links=[DOC]),
    dict(code="Q03", title="Verificación final de Hoja1 (28 requisitos) con evidencias", epic="E5", type=T.TEST,
         sprint="S47", points=3, start=D(2026, 11, 19), due=D(2026, 11, 20), priority=P.CRITICAL,
         deps=["D02", "D03", "D05", "F01", "F02", "B01", "B03", "P01"], hours=6, who="belal", dept="sys",
         status=None, done=None,
         desc="Resultado: docs/mapeo-hoja1.md con el estado final de cada requisito (Completo / Parcial / No "
              "implementado) y su evidencia (prueba, captura o lectura de boss20); lo que siga Parcial dice qué "
              "falta y de quién depende. Aceptación: ningún requisito «No verificado».",
         evidence=None, links=[]),
    dict(code="Q04", title="Entrega completa 20/11: acta con alcance entregado, pendientes y criterios de inicio de la "
                           "operación en pruebas", epic="E5", type=T.DOCS, sprint="S47", points=2,
         start=D(2026, 11, 20), due=D(2026, 11, 20), priority=P.CRITICAL, deps=["Q02", "Q03", "N04", "I02"],
         hours=3, who="belal", dept="dir", status=None, done=None,
         desc=desc("Resultado: acta de entrega firmada por Belal y aceptada por Cristina y Ángel: alcance "
                   "entregado (Hoja1, fase B según decisiones, ciclo, contabilidad, informes, datos, permisos, "
                   "documentación, formación 1), pendientes con responsable y fecha, criterios de inicio de la "
                   "operación en pruebas (T01).",
                   "Hito aprobado por Belal el 26/10/2026: entrega completa el 20/11/2026, con el alcance aprobado y "
                   "los requisitos de Hoja1; el coste manual para servicios sin tarifa solo como excepción aprobada por "
                   "Belal (X01), y esos requisitos siguen «Parcial»."),
         evidence=None, links=[]),
    # ===================================================================== Operación en pruebas · 21 nov–1 dic
    dict(code="T01", title="Criterios de inicio y fin de la operación en pruebas; plan de escenarios y registro de "
                           "incidencias", epic="E11", type=T.TEST, sprint="S48", points=2, start=D(2026, 11, 21),
         due=D(2026, 11, 23), priority=P.CRITICAL, deps=["Q04"], hours=3, who="belal", dept="dir", status=None,
         done=None,
         desc=desc("Inicio: entrega aceptada, maestros migrados, usuarios formados, copia de seguridad diaria "
                   "activa. Fin: todos los escenarios ejecutados por su responsable con resultado registrado, "
                   "incidencias críticas corregidas y re-probadas, informe de cierre. Se distingue «pasa con "
                   "[DEMO]» de «pasa con datos operativos representativos» (migrados y aprobados por Cristina).",
                   "Registro: tareas de tipo Corrección en esta plataforma, una por incidencia."),
         evidence=None, links=[]),
    dict(code="T02", title="Escenario: importación marítima FCL completa (CRM → oferta → aceptación → expediente → "
                           "compras → facturas → rentabilidad)", epic="E11", type=T.TEST, sprint="S48", points=5,
         start=D(2026, 11, 24), due=D(2026, 11, 26), priority=P.CRITICAL, deps=["T01"], hours=6, who="cristina",
         dept="ops", status=None, done=None,
         desc=desc("Con un envío real representativo (cliente migrado, naviera con tarifa aprobada) en el entorno "
                   "de pruebas; resultado y observaciones registrados por el operador.",
                   f"Responsable: Pendiente de asignar (operaciones; Cristina decide quién). {NOT_COMMITTED}"),
         evidence=None, links=[f"{DOC}#/demo-ciclo"]),
    dict(code="T03", title="Escenario: importación aérea (handler, ALM con periodo real, AWB) y exportación aérea",
         epic="E11", type=T.TEST, sprint="S48", points=5, start=D(2026, 11, 24), due=D(2026, 11, 27),
         priority=P.CRITICAL, deps=["T01"], hours=6, who="cristina", dept="ops", status=None, done=None,
         desc=desc("Con envíos reales representativos; comprueba NOA/ATA, periodo real y recálculo, handler "
                   "propuesto.", f"Responsable: Pendiente de asignar (operaciones). {NOT_COMMITTED}"),
         evidence=None, links=[f"{DOC}#/almacenaje"]),
    dict(code="T04", title="Escenario: exportación marítima y transporte terrestre (IRENEO 2026)", epic="E11",
         type=T.TEST, sprint="S48", points=3, start=D(2026, 11, 25), due=D(2026, 11, 27), priority=P.HIGH,
         deps=["T01"], hours=4, who="cristina", dept="ops", status=None, done=None,
         desc=desc("Con envíos reales representativos.", f"Responsable: Pendiente de asignar. {NOT_COMMITTED}"),
         evidence=None, links=[]),
    dict(code="T05", title="Escenario contable: facturas de cliente, abonos, facturas de proveedor por lo prestado, "
                           "bloqueo de pago, suplidos, informes", epic="E11", type=T.TEST, sprint="S48", points=5,
         start=D(2026, 11, 26), due=D(2026, 11, 30), priority=P.CRITICAL, deps=["T01", "W06"], hours=6,
         who="angel", dept="fin", status=None, done=None,
         desc=desc("Sobre los expedientes de T02–T04 en el entorno de pruebas (nunca en los libros reales de "
                   "boss20 antes del 1/1): contabilizar, pagar, abonar; comprobar cuentas, impuestos y los "
                   "informes de facturación y rentabilidad.", f"{NOT_COMMITTED}"),
         evidence=None, links=[f"{DOC}#/facturacion"]),
    dict(code="T06", title="Escenario comercial: oportunidad → oferta con clientes migrados, precios pactados, IVA "
                           "por zona, envío de la oferta", epic="E11", type=T.TEST, sprint="S48", points=3,
         start=D(2026, 11, 24), due=D(2026, 11, 27), priority=P.HIGH, deps=["T01"], hours=4, who="cristina",
         dept="com", status=None, done=None,
         desc=desc("Con clientes reales migrados y las listas de precios que Cristina decida (P01/P02).",
                   f"Responsable: Pendiente de asignar (comercial). {NOT_COMMITTED}"),
         evidence=None, links=[f"{DOC}#/oportunidad"]),
    dict(code="T07", title="Corrección de incidencias de la operación en pruebas y re-prueba", epic="E5", type=T.FIX,
         sprint="S49", points=8, start=D(2026, 11, 23), due=D(2026, 12, 1), priority=P.CRITICAL, deps=["T01"],
         hours=20, who="belal", dept="sys", status=None, done=None,
         desc="Resultado: cada incidencia registrada como tarea, corregida con prueba, desplegada en el entorno de "
              "pruebas y re-probada por quien la abrió. Aceptación: ninguna incidencia crítica abierta el 1/12.",
         evidence=None, links=[]),
    dict(code="T08", title="Informe de cierre de la operación en pruebas (1/12)", epic="E5", type=T.DOCS,
         sprint="S49", points=2, start=D(2026, 12, 1), due=D(2026, 12, 1), priority=P.CRITICAL,
         deps=["T02", "T03", "T04", "T05", "T06", "T07"], hours=3, who="belal", dept="dir", status=None, done=None,
         desc="Resultado: escenarios ejecutados y su resultado, incidencias abiertas y cerradas, lo que pasa con "
              "[DEMO] frente a lo verificado con datos reales, y la lista de lo que entra en la estabilización. "
              "Hito aprobado por Belal: operación en pruebas hasta el 1/12/2026.",
         evidence=None, links=[]),
    # ===================================================================== Estabilización · 2–31 dic
    dict(code="S01", title="Corrección de las incidencias priorizadas de la operación en pruebas", epic="E5",
         type=T.FIX, sprint="S50", points=8, start=D(2026, 12, 2), due=D(2026, 12, 11), priority=P.CRITICAL,
         deps=["T08"], hours=24, who="belal", dept="sys", status=None, done=None,
         desc="Resultado: incidencias del informe T08 corregidas por prioridad, con prueba y re-prueba. "
              "Aceptación: lista cerrada y aprobada por Cristina y Ángel.",
         evidence=None, links=[]),
    dict(code="S02", title="Sistema de referencia en diciembre y traslado de novedades sin pérdida ni duplicados",
         epic="E9", type=T.DOCS, sprint="S49", points=2, start=D(2026, 12, 2), due=D(2026, 12, 4),
         priority=P.CRITICAL, deps=["N04"], hours=3, who="belal", dept="dir", status=None, done=None,
         desc=desc("Regla: hasta el 31/12 Odoo 17 es el único sistema de registro; Odoo 20 solo pruebas. Las "
                   "novedades (expedientes nuevos o cambiados desde el último ensayo) se cargan por diferencias "
                   "(fecha de modificación e id legacy guardado en «Referencia»), sin duplicar; procedimiento "
                   "escrito y probado en el ensayo S04.",
                   "Aceptación: documento aprobado por Belal y Cristina."),
         evidence=None, links=[]),
    dict(code="S03", title="Formación restante por rol (operaciones, comercial, finanzas) y guía de arranque",
         epic="E11", type=T.TRAINING, sprint="S51", points=3, start=D(2026, 12, 9), due=D(2026, 12, 16),
         priority=P.HIGH, deps=["S01"], hours=8, who="belal", dept="ops", status=None, done=None,
         desc=desc("Resultado: cada persona ha hecho su escenario sin ayuda; guía de arranque de una página por "
                   "rol.", f"Participantes según Cristina y Ángel. {NOT_COMMITTED}"),
         evidence=None, links=[f"{DOC}#/inicio"]),
    dict(code="S04", title="Ensayo del cambio definitivo: corte simulado, copia, carga de diferencias, conciliación",
         epic="E9", type=T.TEST, sprint="S51", points=5, start=D(2026, 12, 14), due=D(2026, 12, 18),
         priority=P.CRITICAL, deps=["S02"], hours=10, who="belal", dept="sys", status=None, done=None,
         desc="Resultado: ensayo completo del procedimiento G01–G05 en la copia local con tiempos medidos; "
              "conciliación de expedientes abiertos, saldos y numeración; lista de comprobación corregida. "
              "Aceptación: 0 diferencias sin explicar; tiempo total conocido.",
         evidence=None, links=[]),
    dict(code="S05", title="Copias y restauración verificadas antes del cambio; plan de vuelta atrás aprobado",
         epic="E12", type=T.INFRA, sprint="S52", points=2, start=D(2026, 12, 21), due=D(2026, 12, 22),
         priority=P.CRITICAL, deps=["I02", "S04"], hours=3, who="belal", dept="sys", status=None, done=None,
         desc="Resultado: restauración de la copia más reciente probada; plan de vuelta atrás (seguir en Odoo 17) "
              "aprobado por Belal.",
         evidence=None, links=[]),
    dict(code="S06", title="Lista de comprobación del cambio definitivo aprobada por Cristina y Ángel", epic="E12",
         type=T.DOCS, sprint="S52", points=1, start=D(2026, 12, 22), due=D(2026, 12, 23), priority=P.CRITICAL,
         deps=["S04", "S05"], hours=2, who="belal", dept="dir", status=None, done=None,
         desc=desc("Resultado: lista G01–G06 con hora del corte, responsables, criterios de aceptación "
                   "comprobables y plan ante cualquier obstáculo; aprobada por Cristina (operaciones) y Ángel "
                   "(contabilidad).", f"{NOT_COMMITTED}"),
         evidence=None, links=[]),
    dict(code="W09", title="Desplegar en boss20 la corrección D-1 (líneas de cantidad 0) tras la verificación",
         epic="E7", type=T.INFRA, sprint="S44", points=1, start=D(2026, 10, 27), due=D(2026, 10, 28),
         priority=P.HIGH, deps=["W05"], hours=1, who="belal", dept="sys", status=S.DONE, done=D(2026, 10, 26),
         desc=desc("Resultado: boss_expediente con la corrección D-1 desplegado en boss20 (dev/deploy.sh, web parada) "
                   "tras pasar las pruebas de Odoo y las del motor; comprobación de lectura después.",
                   "Decisión de Belal (26/10, W04-1): el despliegue es una tarea independiente de la corrección.",
                   "Aceptación: versión instalada en boss20 = commit; lectura de boss20 sin errores."),
         evidence="Deployed on 26/10/2026 (dev/deploy.sh update boss_pricing,boss_pricing_sale,boss_expediente, exit 0, log deploy_20261026_130252.log) together with the fix of the crash when a line is priced before the planned date (commit fbea99c); 29/29 Odoo tests and 22/22 engine tests green before deploying; source on the server checked afterwards.", links=[SYS]),
    dict(code="W10", title="Aplicar en boss20 el mapa de cuentas de suplidos aprobado por Ángel (D-2)", epic="E7",
         type=T.FIX, sprint="S45", points=2, start=D(2026, 11, 4), due=D(2026, 11, 5), priority=P.CRITICAL,
         deps=["W06", "A02"], hours=2, who="belal", dept="sys", status=S.BLOCKED, done=None,
         blocked="Espera que Ángel apruebe el mapa de cuentas de suplidos (docs/cuentas-suplidos.md, tarea A02).",
         desc=desc("Resultado: cuentas 419001–419007 (o las que Ángel apruebe) creadas en boss20 y asignadas a ARA, IVA, "
                   "PLA y DUM con dev/setup_suplidos_accounts.py --approved-by-angel; el borrador de factura de ARA de "
                   "E260001 se crea sin error.",
                   "Bloqueo: espera la aprobación del mapa (docs/cuentas-suplidos.md) por Ángel (A02). Mientras tanto "
                   "la fila ARA de E260001 no se puede facturar en boss20 (defecto D-2).",
                   "Aceptación: lectura de boss20 con las cuentas y el mapa; factura borrador de ARA creada."),
         evidence=None, links=[f"{DOC}#/facturacion"]),
    dict(code="X01", title="Excepción de coste manual en la entrega para servicios sin tarifa aprobada: aprobación de "
                           "Belal por servicio", epic="E8", type=T.ANALYSIS, sprint="S47", points=1,
         start=D(2026, 11, 16), due=D(2026, 11, 17), priority=P.CRITICAL, deps=["D02", "D05"], hours=2, who="belal",
         dept="dir", status=None, done=None,
         desc=desc("Regla de Belal (26/10): la entrega del 20/11 incluye el alcance aprobado y los requisitos de "
                   "Hoja1; el coste manual para un servicio sin tarifa es una excepción que necesita su aprobación, y "
                   "el requisito afectado sigue «Parcial».",
                   "Resultado: lista de servicios de Hoja1 que a 16/11 siguen sin tarifa aprobada, con el motivo "
                   "(documento no recibido, no aprobado, decisión pendiente) y la aprobación o no de Belal de la "
                   "excepción por servicio; reflejada en docs/mapeo-hoja1.md y en el acta de entrega (Q04)."),
         evidence=None, links=[]),
    dict(code="B05", title="VET: configurar el servicio tras la decisión de Cristina, con ejemplo de referencia "
                           "(Hoja1 B7)", epic="E8", type=T.DEV, sprint="S45", points=2, start=D(2026, 11, 5),
         due=D(2026, 11, 6), priority=P.HIGH, deps=["C02"], hours=3, who="belal", dept="sys", status=None,
         done=None,
         desc=desc("Resultado: VET deja de estar «pendiente de decisión»: unidad, método, modo de coste y clase de IVA "
                   "según la respuesta de Cristina (P16: ¿inspección veterinaria en PIF por documento como SAN? "
                   "proveedor y precio); tarifa cargada si hay documento; ejemplo de referencia y prueba.",
                   "Estado real 26/10: H1-11 no implementado (modo pending).",
                   "Aceptación: VET calcula en una oferta en borrador según el ejemplo; docs/mapeo-hoja1.md H1-11 "
                   "actualizado."),
         evidence=None, links=[f"{DOC}#/srv-VET"]),
    dict(code="V01", title="Verificación en boss20 de Hoja1 filas 8–10: NOA/ATA con hora, aerolínea↔handler, lista "
                           "de Odoo 17", epic="E5", type=T.TEST, sprint="S46", points=2, start=D(2026, 11, 12),
         due=D(2026, 11, 13), priority=P.HIGH, deps=["F01", "F02", "F03", "C04"], hours=3, who="belal", dept="sys",
         status=None, done=None,
         desc=desc("Resultado: con un expediente aéreo [DEMO] en boss20: NOA y ATA con hora propagan el periodo de "
                   "ALM y recalculan el coste (H1-21, H1-22); al elegir aerolínea y aeropuerto se propone el handler "
                   "validado por Cristina (H1-23, H1-24, H1-26); capturas en la guía.",
                   "Aceptación: comportamiento observado en boss20 (no solo el campo en pantalla); docs/mapeo-hoja1.md "
                   "actualizado con la evidencia."),
         evidence=None, links=[f"{DOC}#/expediente"]),
    dict(code="G07", title="Soporte posterior al cambio (4–8 ene): incidencias con prioridad y seguimiento diario",
         epic="E12", type=T.INFRA, sprint="S2701", points=3, start=D(2027, 1, 4), due=D(2027, 1, 8),
         priority=P.CRITICAL, deps=["G04"], hours=20, who="belal", dept="sys", status=None, done=None,
         desc="Resultado: soporte inmediato la primera semana de operación real; cada incidencia como tarea de "
              "Corrección con prioridad; revisión diaria con Cristina y Ángel. Aceptación: ninguna incidencia "
              "crítica abierta el 8/1 (acta G06).",
         evidence=None, links=[SYS]),
    # ===================================================================== Cambio definitivo · 1–8 ene 2027
    dict(code="G01", title="Corte: dejar de registrar operaciones nuevas en Odoo 17 (hora definida, propuesta "
                           "31/12 18:00)", epic="E12", type=T.MIGRATION, sprint="S53", points=1,
         start=D(2026, 12, 31), due=D(2026, 12, 31), priority=P.CRITICAL, deps=["S06"], hours=1, who="cristina",
         dept="ops", status=None, done=None,
         desc=desc("Aviso al equipo; desde la hora del corte ninguna alta ni cambio en Odoo 17.",
                   f"Responsable: Cristina (operaciones). {NOT_COMMITTED}"),
         evidence=None, links=[]),
    dict(code="G02", title="Copia final de Odoo 17 y carga de diferencias en boss20 desde el último ensayo", epic="E9",
         type=T.MIGRATION, sprint="S53", points=5, start=D(2026, 12, 31), due=D(2027, 1, 1), priority=P.CRITICAL,
         deps=["G01"], hours=8, who="belal", dept="sys", status=None, done=None,
         desc="Resultado: copia final de Odoo 17 archivada; diferencias cargadas en boss20 con el procedimiento "
              "S02; informe de carga.",
         evidence=None, links=[]),
    dict(code="G03", title="Conciliación: expedientes abiertos, saldos, numeración, usuarios y permisos", epic="E9",
         type=T.TEST, sprint="S53", points=3, start=D(2027, 1, 1), due=D(2027, 1, 3), priority=P.CRITICAL,
         deps=["G02"], hours=6, who="belal", dept="fin", status=None, done=None,
         desc=desc("Resultado: conteos y sumas legacy = nuevos; numeración de expedientes y facturas según la "
                   "decisión (P36 y series de 2027); cada usuario con su rol.",
                   f"Con Ángel para saldos y series de facturación. {NOT_COMMITTED}"),
         evidence=None, links=[]),
    dict(code="G04", title="Odoo 20 único sistema de registro desde el 1/1/2027; aviso al equipo",
         epic="E12", type=T.INFRA, sprint="S53", points=3, start=D(2027, 1, 1), due=D(2027, 1, 3),
         priority=P.CRITICAL, deps=["G03"], hours=16, who="belal", dept="sys", status=None, done=None,
         desc="Resultado: comunicación del arranque y Odoo 20 declarado único sistema de registro el 1/1/2027 "
              "(hito aprobado por Belal el 26/10). El soporte de la primera semana es la tarea G07.",
         evidence=None, links=[SYS]),
    dict(code="G05", title="Odoo 17 en solo lectura (archivo) y copia de la base de datos conservada", epic="E12",
         type=T.INFRA, sprint="S53", points=1, start=D(2027, 1, 2), due=D(2027, 1, 3), priority=P.HIGH,
         deps=["G02"], hours=2, who="belal", dept="sys", status=None, done=None,
         desc="Resultado: usuarios de Odoo 17 sin permisos de escritura; copia de la base de datos y del filestore "
              "guardada; acceso de consulta conservado.",
         evidence=None, links=[]),
    dict(code="G06", title="Aceptación del arranque (acta de Cristina y Ángel)", epic="E12", type=T.DOCS,
         sprint="S2701", points=1, start=D(2027, 1, 8), due=D(2027, 1, 8), priority=P.CRITICAL, deps=["G04"],
         hours=2, who="belal", dept="dir", status=None, done=None,
         desc=desc("Resultado: acta con los criterios G01–G05 comprobados, incidencias abiertas y su plan.",
                   f"{NOT_COMMITTED}"),
         evidence=None, links=[]),
]


# English titles (Belal, 26/10/2026: task titles in English only; descriptions stay in Spanish)
TITLES_EN = {
    "000": "Step 1: situation analysis and open questions",
    "001": "Task manager: Scrum (sprints, backlog, board, burndown) + Gantt and publishing",
    "002": "Repository structure, CLAUDE.md and .gitignore",
    "003": "Development and test environment (local Docker, throw-away DB) and boss20 server",
    "004": "ADR-001: version, architecture and pricing modules",
    "005": "ADR-002: tariff data model",
    "006": "Service study template (docs/services)",
    "007": "Remote repository (GitHub) and code backup; quality (ruff, pre-commit)",
    "010": "THC study (sea FCL import) + golden cases",
    "011": "BL/DOC study",
    "012": "T3 / T3-PAD study",
    "013": "DEM/OCU/ALM study (time-based charges)",
    "014": "GLO study (CCC, FUELEU, LOG)",
    "015": "FAD study (import customs clearance)",
    "016": "TTE-FCL study (container haulage)",
    "017": "FMI study (sea freight from supplier offer)",
    "020": "Pure-Python pricing engine + tests on golden cases",
    "021": "Odoo module: supplier tariff (document, validity, versions, line per service)",
    "022": "Scope conditions and single matching and pricing service",
    "023": "Shipment data on the quotation (containers, weights, volumes, dates, route)",
    "024": "Time-based charges on the file (actual period with hours, recompute)",
    "025": "'Pricing & Suppliers' workspace: price entry with PDF and page, test pricing",
    "026": "es_ES translation and automated tests green",
    "030": "Review with Cristina and Ángel + delivery documentation",
    "A01": "Session with Ángel: test sheet (8 cases) and ratification of accounting decisions",
    "A02": "Ángel: paid-on-behalf accounts by concept and side, and accounts per category (P18, P37)",
    "A03": "Ángel: SII or VeriFactu and returns Odoo 20 must prepare from go-live (P45)",
    "A04": "Ángel: VAT of CAU and QBR for Spanish customers, QBR rate, minimum margin and CAU/SEG (P17, P03, P01/P02, P13)",
    "B01": "Phase B1: single ALM sale price (sale tariff on the time engine + pricelist rule; ADR-006)",
    "B02": "Phase B2: QBR — EUR invoice of a USD quotation at the carrier rate with exchange-loss line",
    "B03": "Phase B3: ETX (bought per master AWB, sold per file) and DET (own code or within DEM)",
    "B04": "Phase B4/B5: special storage (cargo-type condition, warehouse code) and price agreement for several shipments",
    "B05": "VET: configure the service after Cristina's decision, with reference example (Hoja1 B7)",
    "C01": "Cristina: review and approval of the 10 sample tariffs (P19) and ratification of WFS readings",
    "C02": "Cristina: pending service decisions (VET, GLO per document, Far East, DET, ETX, ALM sale D1–D7, undefined services, numbering)",
    "C03": "Cristina: IRENEO 2026 tariff or written confirmation of 2025 prices (P28)",
    "C04": "Cristina: approval of batch 1 tariffs and validation of the airline/handler list",
    "C05": "Cristina: approval of batch 2 tariffs (handler 2, shipping lines)",
    "D01": "Collect the missing tariff documents (list of 07/10: customs, Hapag, Transglory, PFT, inspections, CES, carriers D&D, 2nd handler)",
    "D02": "Load and submit for approval the received tariffs (batch 1: customs, Hapag, Transglory, inspections, IRENEO 2026) with reference examples",
    "D03": "Load the second air handler (import and export) and WFS export HAN/AWB (Hoja1 B10, D10)",
    "D04": "Test the reference scenario of each approved tariff with a draft quotation",
    "D05": "Load D&D of ONE, MSK, ZIM and OOCL and local charges of other carriers (batch 2) (Hoja1 E10)",
    "F01": "NOA and ATA fields with date and time on the file; they feed the ALM/DEM/OCU period (Hoja1 C8, D8)",
    "F02": "Airline and handler on the file, paired with the airport; airline → handler association (Hoja1 B9, C9)",
    "F03": "Extract the airline / airport / handler list from Odoo 17 and propose the association (Hoja1 C10)",
    "G01": "Cut-off: stop recording new operations in Odoo 17 (set time, proposed 31/12 18:00)",
    "G02": "Final Odoo 17 backup and delta load into boss20 since the last rehearsal",
    "G03": "Reconciliation: open files, balances, numbering, users and permissions",
    "G04": "Odoo 20 as the only system of record from 1/1/2027; team notice",
    "G05": "Odoo 17 read-only (archive) and database backup kept",
    "G06": "Go-live acceptance (sign-off by Cristina and Ángel)",
    "G07": "Post-cutover support (4–8 Jan): prioritised incidents and daily follow-up",
    "I01": "Development environment on Mac: move and verify (tests and deployment from the Mac)",
    "I02": "Automatic boss20 backups (DB and files), tested restore and rollback plan",
    "I03": "Deployment and rollback procedure; performance with migrated data",
    "N01": "Odoo 17 migration scope: which data, which open files, cut-off date",
    "N02": "Migration: field mapping and Odoo 17 read script (master data and open files) tested on the local copy",
    "N03": "Master data migration to boss20: customers, suppliers, roles, ports, container types, airlines and handlers, with validation",
    "N04": "Full migration rehearsal on the local copy: open Odoo 17 files → Odoo 20 and reconciliation",
    "N06": "SII or VeriFactu: install and configure per Ángel's decision (if applicable)",
    "P01": "Forecast report: files with sale, expected and actual cost, margin, dates, by week and month (list and pivot)",
    "P02": "Invoicing and profitability reports by file, customer and period",
    "Q01": "Full automated tests with all tariffs loaded and defect fixing",
    "Q02": "Final documentation: ES/EN guide, ADRs, decisions and migration updated",
    "Q03": "Final Hoja1 verification (28 requirements) with evidence",
    "Q04": "Full delivery 20/11: sign-off with delivered scope, open items and pilot start criteria",
    "R01": "BOSS service catalogue (78) with unit, calculation method and VAT class",
    "R02": "BOSS VAT table: Odoo tax by class, customer zone and paid-on-behalf",
    "R03": "Sale price from cost (pricelists: fixed, markup, margin, minimum)",
    "R04": "Operational cycle: file, parties, purchase orders, invoicing by service, credit notes and profitability",
    "R05": "Recompute with actual data, one quotation in several files, service added after acceptance",
    "R06": "ES/EN user guide published at doc.bosscontinental.com/new",
    "R07": "Deployment to boss20 (8ec4a2c) and configuration of the 23/10 decisions",
    "R08": "Real tariff samples loaded and submitted for approval (MSC, WFS, IRENEO, CMA, Hapag)",
    "R09": "23/10 decisions (P03–P44) approved by Belal and documented",
    "R10": "Performance measured in a real browser (0.95–1.47 s per screen)",
    "S01": "Fix prioritised pilot incidents",
    "S02": "System of record in December and transfer of new data without loss or duplicates",
    "S03": "Remaining training by role (operations, sales, finance) and go-live guide",
    "S04": "Cutover rehearsal: simulated cut-off, backup, delta load, reconciliation",
    "S05": "Backups and restore verified before cutover; rollback plan approved",
    "S06": "Cutover checklist approved by Cristina and Ángel",
    "T01": "Pilot start and exit criteria; scenario plan and incident log",
    "T02": "Scenario: full sea FCL import (CRM → quotation → acceptance → file → purchases → invoices → profitability)",
    "T03": "Scenario: air import (handler, ALM with actual period, AWB) and air export",
    "T04": "Scenario: sea export and road transport (IRENEO 2026)",
    "T05": "Accounting scenario: customer invoices, credit notes, supplier bills on performed quantities, payment block, paid-on-behalf, reports",
    "T06": "Sales scenario: opportunity → quotation with migrated customers, agreed prices, VAT by zone, sending the quotation",
    "T07": "Fix pilot incidents and retest",
    "T08": "Pilot closing report (1/12)",
    "U01": "Role permissions, outgoing mail and quotation/invoice templates (PDF) on boss20",
    "U02": "Training 1: sales and operations (contacts, CRM, quotation, acceptance, file, purchases)",
    "V01": "Verification on boss20 of Hoja1 rows 8–10: NOA/ATA with time, airline↔handler, Odoo 17 list",
    "W01": "Ángel's test sheet, isolated local copy and dry run of the 8 cases",
    "W02": "Tariff review for Cristina and single ALM sale price specification (P43)",
    "W03": "Hoja1 mapping and weekly launch plan on the platform",
    "W04": "Belal's decision: paid-on-behalf accounts on boss20 (D-2), D-1 fix and guide publishing",
    "W05": "Fix D-1: payment block ignores zero-quantity lines (code + test)",
    "W06": "D-2: paid-on-behalf account map (as Odoo 17), fix and invoicing tests locally; proposal to Ángel",
    "W07": "Publish the corrected guide (pending ratifications, open decisions)",
    "W08": "boss20 users for Ángel, Cristina and operations, with their roles",
    "W09": "Deploy the D-1 fix (zero-quantity lines) to boss20 after verification",
    "W10": "Apply on boss20 the paid-on-behalf account map approved by Ángel (D-2)",
    "X01": "Manual-cost exception at delivery for services without approved tariff: Belal's approval per service",
}

# English task descriptions (Belal, 26/10/2026: titles and descriptions in English). One text per task; the
# kickoff tasks of 21/10 keep their original description once, translated (ORIG_EN).
PROPOSED = "Date proposed by Belal on 26/10/2026; not confirmed by the person responsible."
RETRO_EN = ("Task created on 26/10/2026 to record work already done (planning rebuilt after the fact); the dates are "
            "those of the commits.")
DESCS_EN = {
    "000": "Result: analysis of what is asked and what is not, with open questions for Belal (step 1 of the KICKOFF).\n"
           "Source: KICKOFF_PROMPT.md.\nAcceptance: Belal answers the questions (done on 21–22/10).",
    "001": "Result: task.bosscontinental.com with sprints, backlog, board, story points, burndown and Gantt.\n"
           "Acceptance: published and checked in the browser.",
    "002": "Result: addons/, docs/adr, dev/, .gitignore without Odoo source or supplier PDFs; CLAUDE.md with the project "
           "rules.",
    "003": "Result: dev/test.sh (local Docker stack with an in-memory DB for tests), dev/deploy.sh with an environment "
           "identity check, boss20 server running Odoo 20 Enterprise.",
    "004": "Result: docs/adr/001-architecture-and-modules.md (context, alternatives, decision, consequences).",
    "005": "Result: docs/adr/002-pricing-model.md: tariff with document, validity and versions; line per service; "
           "methods; scope; minimum/maximum; approval; single pricing service.",
    "006": "Replaced: docs/services was not created; the per-service study lives in docs/matriz-servicios.md (unit, "
           "method, VAT, status) and docs/ejemplos-referencia.md (cases checked against real documents), plus each "
           "service page of the guide.",
    "007": "Result: the BossOdoo20 repository has a remote (dev1bms GitHub or another approved by Belal) with all "
           "commits; ruff and pre-commit configured.\nActual status 26/10: no remote (every commit is local: risk of "
           "loss).\nOriginal plan date: 3/11. New date: 27/10, brought forward by Belal's decision (26/10): the code is "
           "still local and the current machine is slow.\nAcceptance: `git remote -v` shows the remote and `git push` "
           "succeeds; ruff without errors.",
    "010": "Result: THC studied with the MSC 09/2026 document p.12 (R1), sample tariff loaded and reference test; "
           "equivalent to docs/services/THC.md of the original plan.",
    "011": "Result: BL once per file (R4, MSC p.12); DOC for the house; master per file (P25).",
    "012": "Result: T3-PAD by container size (R2, MSC p.12); T3 of other carriers and of LCL pending a document (Hoja1 "
           "H1-01).",
    "013": "Result: free days, events that open and close the period, relative or day-number tiers, 24 h periods or "
           "calendar days, minimum; cases R8–R18 (MSC, Hapag, CMA) and R01–R05 (WFS).",
    "014": "Result: GLO-CCC per DV/HC container (R5) and GLO-FUELEU per TEU, origin China (R3); «Far East» list pending "
           "from Cristina (P24); GLO per document pending a decision (H1-13).",
    "015": "Result: FAD with the real Aducex and Ramos Vila tariffs (1 container / 2 or more; several entries) loaded "
           "and checked with a reference example.\nActual status 26/10: «per clearance» method configured; no document "
           "(Hoja1 H1-02). Cristina 28/09: the operator chooses the broker, no automatic choice.\nOriginal date in the "
           "plan of 21/10: none (backlog). New date: 5/11, because the documents are missing (task D01).\nAcceptance: "
           "reference example with the real tariff in docs/ejemplos-referencia.md and reference test green.",
    "016": "Result: TTE-FCL with a real tariff by route and brackets, loaded and checked.\nActual status 26/10: "
           "brackets method configured; no document (Hoja1 H1-18).\nOriginal date: backlog, none. New date: 6/11, "
           "because the document is missing (task D01).\nAcceptance: reference example and test green.",
    "017": "Result: freight (FMI, FME, FAI, FAE) is quoted with the manual amount of the supplier offer («manual "
           "amount» mode), in its currency at the rate of the quotation date (P03).",
    "020": "Result: addons/boss_pricing/engine (fixed, per unit, larger of two bases, brackets, percentage, time with "
           "free period, 24 h periods or days, weekend exceptions) with its tests.",
    "021": "Result: boss.tariff and boss.tariff.line with document and page, validity, versions, scope, approval "
           "(draft → waiting for approval → approved) and sample importer.",
    "022": "Result: boss.pricing.price_cost(): one function for quotation and file, with explicit statuses (ok, missing "
           "input, no tariff, pending approval, conflict, not ready).",
    "023": "Result: shipment data on the quotation and the file (containers by size and type, gross kg, m³, pallets, "
           "AWB chargeable kg, dates, port, country, carrier) and one quantity function per charge basis.",
    "024": "Result: ALM/DEM/OCU with the actual period (start and end with date and time), 24 h or calendar-day "
           "readings, minimum per stay, weekend exceptions; recompute of the expected cost.",
    "025": "Result: one way to enter a price, linked to its document; filters by status; «Test pricing» with draft "
           "simulation; DEMO tariffs isolated.",
    "026": "Result: source strings in English and es.po translation of the four modules; 27 Odoo tests (boss_expediente "
           "13, boss_pricing_sale 13, boss_pricing 1) and 21 engine tests without failures.",
    "030": "Result: Cristina and Ángel have seen the system and ratified (or changed) the decisions in their area.\n"
           "Actual status 26/10: documentation delivered (ES/EN guide published on 23/10, decisions P03–P44 approved by "
           "Belal, Ángel's test sheet of 26/10); the sessions have not taken place.\nOriginal date: backlog, none. New "
           "date: 30/10 (sessions A01 and C01).\nAcceptance: minutes of both sessions with the ratifications recorded "
           "in docs/preguntas-abiertas.md.",
    "A01": "Result: docs/pruebas-angel.md filled in (actual result per case) and Ángel's decisions recorded: P17, P30, "
           "P31, P32, P03, P11, P38, P39, P33; paid-on-behalf accounts (D-2); VAT of CAU/QBR; purchase taxes per bill "
           "type; QBR; minimum margin; SII/VeriFactu (P45).\nEnvironments: boss20 drafts only; posting and payments on "
           f"the isolated local copy.\nOrganised by Belal; Ángel takes part. {PROPOSED}\nAcceptance: sheet signed and "
           "docs/preguntas-abiertas.md updated with date and source.",
    "A02": "Decision: which accounts the paid-on-behalf services (ARA, IVA, PLA, DUM) use when invoicing the customer "
           "and when recording the broker's bill. Odoo 17 uses 419001 VAT charged, 419002 duties charged, 419003 VAT "
           "borne, 419004 duties borne, 419005 anti-dumping, 419006 and 419007 plastic tax (current liabilities). Also "
           "the income and expense accounts per service category.\nProposal ready: docs/cuentas-suplidos.md (task "
           f"W06). {PROPOSED}\nAcceptance: account list per concept signed; applied in W10.",
    "A03": "Decision: whether BOSS must send invoices to the tax agency (SII or VeriFactu) from 1/1/2027 and which "
           "returns (303, 349, 390…) Odoo 20 produces. Today boss20 has no SII or VeriFactu module (read on 26/10) and "
           f"nothing is sent.\n{PROPOSED}\nAcceptance: written decision; if it applies, installation and configuration "
           "task (N06).",
    "A04": "VAT and finance decisions with no assumed answer: tax of NS services that are not paid on behalf (CAU, QBR) "
           "for a Spanish customer; exchange-loss rate and EUR invoice of a USD order; minimum margin value and who "
           "approves selling below it; rates and minimums of CAU and SEG (with Cristina).\nMeanwhile: VAT pending in "
           f"those cases; no QBR; no minimum margin. {PROPOSED}",
    "B01": "Result: per docs/especificacion-alm-venta.md: BOSS sale tariff (approved by Cristina), new pricelist base "
           "«BOSS sale tariff», price with explanation on the quotation, snapshot on acceptance; engine tests E1–E6 and "
           "a quotation with ALM.\nBlocker: needs Cristina's answers D1–D7 (C02). Real amounts stay out of Git.\n"
           "Acceptance: tests green; a [DEMO] quotation with ALM shows the price and its explanation.",
    "B02": "Result: «Invoice services» wizard with invoice currency; QBR line with the approved rate; exchange "
           "difference recorded as Ángel decides.\nBlocker: rate and accounting treatment (A04).\nAcceptance: test with "
           "a USD order invoiced in EUR on a throw-away DB.",
    "B03": "Result: ETX and DET configured (unit, method, cost mode) with the supplier document; MSC export DET loaded "
           "if applicable (Hoja1 H1-17, H1-25).\nAcceptance: reference example per service and test green.",
    "B04": "Result: cargo-type condition in the ALM tariffs, code for the off-airport warehouse if Cristina and Ángel "
           "approve it (P44), and price agreement for several shipments on top of the split between files (P34), if "
           "Cristina provides the data.\nIf there is no data by 9/11, it moves to the December stabilisation (not "
           "essential for delivery).",
    "B05": "Result: VET is no longer «pending decision»: unit, method, cost mode and VAT class per Cristina's answer "
           "(P16: veterinary inspection at the BIP, per document like SAN? supplier and price); tariff loaded if there "
           "is a document; reference example and test.\nActual status 26/10: H1-11 not implemented (pending mode).\n"
           "Acceptance: VET prices a draft quotation as in the example; docs/mapeo-hoja1.md H1-11 updated.",
    "C01": "Result: each [MUESTRA] tariff (MSC ×3, WFS ×2, CMA CGM, Hapag-Lloyd, IRENEO ×3) reviewed with its PDF and "
           "the examples of docs/ejemplos-referencia.md, and approved, sent back to draft with the correction, or not "
           "approved (IRENEO 2025 is not extended). WFS readings P40, P41, P29, P42 ratified or changed.\nSource: Hoja1 "
           "rows 7 and 10 (H1-01, 05, 12, 14, 15, 16, 20, 25, 27, 28); docs/revision-tarifas.md.\nNote: 8 of the 10 "
           "arrived without «Scope reviewed»; check it before approving.\nOrganised by Belal; Cristina approves in "
           f"Tariffs → Waiting for approval. {PROPOSED}\nAcceptance: status of each tariff on boss20 changed by "
           "Cristina; after approval, reference scenario tested with a draft quotation (task D04).",
    "C02": "Decisions that block Hoja1: VET (H1-11, P16), which GLO per document are proposed automatically (H1-13), "
           "«Far East» country list (H1-14, P24), DET own code or within DEM (H1-17, P09), ETX concept and unit (H1-25, "
           "P10), single ALM sale price points D1–D7 of docs/especificacion-alm-venta.md (P43), services to define or "
           f"retire (P16), E26xxxx numbering at go-live (P36), multi-shipment agreements (P34).\n{PROPOSED}\n"
           "Acceptance: written answers in docs/preguntas-abiertas.md with date; tasks B01, B03, B05 and D02 unblocked.",
    "C03": "Result: IRENEO 2026 document (HAN, X-R, TTE-CON, SEG, FS) or written confirmation; the 2025 tariffs are not "
           f"extended (Hoja1 H1-20).\n{PROPOSED}\nAcceptance: document in the NEW ODOO folder and new tariff loaded (D02).",
    "C04": "Result: batch 1 tariffs approved (or sent back with a correction) and airline / airport / handler list "
           f"validated.\n{PROPOSED}\nAcceptance: statuses changed on boss20; list signed.",
    "C05": f"Result: batch 2 tariffs approved or sent back.\n{PROPOSED}",
    "D01": "Result: current documents in the NEW ODOO folder: Aducex and Ramos Vila (FAD), export broker (DEX), "
           "Hapag-Lloyd local charges (T3, THC, CES), Transglory CFS (THC-LCL), agents' PFT agreements, prices per "
           "document (ROH, SOI, INS, SAN, VET), CES, D&D of ONE, MSK, ZIM and OOCL, and the second air handler (IAS or "
           "SAASA: import and export).\nSource: Hoja1 rows 7 and 10; sheet «Documentos no encontrados» of 07/10 (37 "
           "services without a document on 26/10: docs/revision-tarifas.md).\nOwner: to be assigned (07/10 proposal: "
           f"Laura / operations; Cristina coordinates). {PROPOSED}\nAcceptance: each document with supplier, edition and "
           "validity; what does not exist is noted as «does not exist», so a manual cost with supporting document is "
           "used (exception X01).",
    "D02": "Result: each received document loaded as a tariff (price with page, scope reviewed) and submitted for "
           "approval; reference example per service and reference test green.\nSource: Hoja1 H1-01 to H1-10, H1-12, "
           "H1-13, H1-18, H1-19, H1-20, H1-28.\nAcceptance: tariffs «Waiting for approval» on boss20; "
           "docs/ejemplos-referencia.md extended; Cristina's approval (C04).",
    "D03": "Result: HAN, ETX, ALM and AWB of the second handler (IAS or SAASA) for import and export, and the missing "
           "WFS export codes, loaded and submitted for approval.\nActual status 26/10: WFS only (import: HAN, ALM, AWB; "
           "export: ALM, X-R).\nAcceptance: tariffs waiting for approval; reference examples; Cristina's approval (C05).",
    "D04": "Result: for each approved tariff, a draft quotation (non-DEMO test customer) with the data of the reference "
           "example gives the cost of the example; the quotation is not sent.\nSource: condition 5 of "
           "docs/revision-tarifas.md.\nAcceptance: table tariff → quotation → expected cost = obtained, in "
           "docs/ejemplos-referencia.md.",
    "D05": "Result: import OCU/DEM/DET of the 5 carriers of Hoja1 (today only MSC; CMA and Hapag in addition) and the "
           "local charges received, loaded with their examples.\nAcceptance: tariffs waiting for approval and "
           "reference test green.",
    "F01": "Result (Cristina via Belal, 26/10/2026; replaces the earlier note that air files would not use ATA): "
           "the file has ATA (actual arrival) and Pickup (actual), both with date AND time, on every transport mode, "
           "and the system computes the dates from them: ATA → Pickup is the actual period of the time-based services "
           "(ALM on air; DEM/OCU on sea), the days/periods are counted by the engine and the expected cost is "
           "recomputed; an event is added to the file. NOA (Cristina 25/09) stays as an optional event, not required.\n"
           "Brought forward to the week of 26/10 (capacity available; depends on no decision). Actual status 26/10: "
           "the file has ATA and Pickup as dates without time, and they do not feed the service period (H1-21, "
           "H1-22).\nAcceptance: automated tests (ATA + Pickup with time → ALM period → days → cost recomputed; same "
           "for DEM/OCU on sea) and screenshots in the guide; checked with Cristina on a [DEMO] air file.",
    "F02": "Result: association model (airline, airport → handler) loaded from F03; on an air file, choosing airline "
           "and airport proposes the handler (editable); the handler is the default supplier of HAN, ALM, AWB, ETX.\n"
           "Actual status 26/10: not implemented (H1-23, H1-24). Cristina 28/09: association «later»; done now because "
           "Hoja1 asks for it.\nAcceptance: automated test and a [DEMO] air quotation with the handler proposed.",
    "F03": "Result: read-only script on Odoo 17 (air files: airline, airport, handler used) and list in .research (real "
           "data, outside Git) for Cristina to validate the association.\nActual status 26/10: not implemented "
           "(H1-26).\nAcceptance: list validated by Cristina; it is the load for F02.",
    "G01": f"Notice to the team; from the cut-off time no new record or change in Odoo 17.\nOwner: Cristina "
           f"(operations). {PROPOSED}",
    "G02": "Result: final Odoo 17 backup archived; differences loaded into boss20 with procedure S02; load report.",
    "G03": "Result: legacy and new counts and totals match; file and invoice numbering per the decision (P36 and 2027 "
           f"series); each user with their role.\nWith Ángel for balances and invoice series. {PROPOSED}",
    "G04": "Result: go-live announcement and Odoo 20 declared the only system of record on 1/1/2027 (milestone approved "
           "by Belal on 26/10). Support in the first week is task G07.",
    "G05": "Result: Odoo 17 users without write access; database and filestore backup kept; read access preserved.",
    "G06": f"Result: minutes with criteria G01–G05 checked, open incidents and their plan.\n{PROPOSED}",
    "G07": "Result: immediate support in the first week of real operation; each incident as a Fix task with priority; "
           "daily review with Cristina and Ángel. Acceptance: no critical incident open on 8/1 (minutes G06).",
    "I01": "Result: the repository, Docker (dev/test.sh), the deployment scripts and the SSH keys work from the Mac; "
           "tests and a test deployment to the local copy done from it.\nActual status 26/10: not verified (no evidence "
           "in the repository that the move is done). Brought forward to this week by Belal's decision (26/10): the "
           "current machine is slow.\nAcceptance: `dev/test.sh run boss_expediente` green from the Mac; `dev/deploy.sh` "
           "run from the Mac.",
    "I02": "Result: daily backup of the boss20 database and filestore outside the server, with retention; restore "
           "tested on the local copy; written rollback plan (Odoo 17 stays untouched until 1/1).\nAcceptance: one full "
           "restore verified and documented with date.",
    "I03": "Result: dev/deploy.sh with a prior backup step and documented rollback; timing measured with migrated data "
           "(target: < 2 s per screen, as on 23/10). Acceptance: measurements in docs/ciclo-operativo.md.",
    "N01": "Decision of Belal with Cristina: master data (customers, suppliers, roles, ports, container types, "
           "airlines/handlers), files open on 1/1/2027 (and their quotations), history in Odoo 17 read-only; invoices "
           "and accounting stay in Odoo 17 (criterion of the Odoo 19 mapping, Q11) unless Ángel decides otherwise.\n"
           "Actual status 26/10: no migration script in the repository; boss20 has no real customers or suppliers.\n"
           "Acceptance: scope written in docs/migracion.md with reconciliation criteria.",
    "N02": "Result: docs/migracion.md with the mapping per group (customers and suppliers with dedup by VAT number and "
           "name, roles, ports, container types, airlines/handlers, open files with parties, containers, references and "
           "dates); read-only Odoo 17 script and load into the local copy with a quality report (duplicates, no VAT "
           "number, zones).\nAcceptance: load into the local copy without errors; legacy counts = new; human review list "
           "for doubtful cases.",
    "N03": "Result: master data loaded into boss20 from Odoo 17 with a reconciliation report (counts, duplicates "
           "resolved, VAT numbers and VAT zones, legacy id in «Reference»); review list for Cristina.\nAcceptance: "
           "legacy counts = new; no duplicates by VAT number; each customer with a VAT zone.",
    "N04": "Result: load of the open files (parties, containers, references, dates, services with expected cost) into "
           "the local copy; reconciliation report per file (legacy and new counts and totals match, differences "
           "explained); repeatable procedure to load differences by date or legacy id without duplicates.\nAcceptance: "
           "0 unexplained differences; procedure documented in docs/migracion.md.",
    "N06": "Result: localisation module installed and configured in test mode; real sending only after go-live and with "
           "Ángel's approval.\nIf Ángel decides it does not apply in 2027, the task is cancelled with the reason.",
    "P01": "Result: list and pivot view over files and their services (agreed sale, cost at acceptance, committed, "
           "actual, forecast, margins, invoiced, collected, paid) filterable by status, customer, mode and dates "
           "(ETD/ETA/ATA/NOA); exportable.\nSource: Hoja1 «PREVISIONES» (A6); Odoo 17 forecast report (extension).\n"
           "Actual status 26/10: the figures exist per file («Summary» and «Where the figures come from»); no aggregated "
           "view.\nAcceptance: Cristina validates the columns with the [DEMO] data; it matches each file's summary.",
    "P02": "Result: invoiced, collected, paid and margin by file, customer and month, from the same calculations as the "
           "file summary; exportable.\nAcceptance: Ángel validates the columns with the [DEMO] data.",
    "Q01": "Result: engine, reference tests (with all private samples) and Odoo tests green; open defects fixed or "
           "logged with priority. Acceptance: 0 failures recorded in docs/ciclo-operativo.md with the commit.",
    "Q02": "Result: guide published with the final screens; ADR-006 (ALM sale); docs/preguntas-abiertas.md with all "
           "ratifications; docs/migracion.md. Acceptance: published and checked with curl.",
    "Q03": "Result: docs/mapeo-hoja1.md with the final status of each requirement (Complete / Partial / Not implemented) "
           "and its evidence (test, screenshot or boss20 read); what stays Partial says what is missing and who it "
           "depends on. Acceptance: no requirement «Not verified».",
    "Q04": "Result: delivery minutes signed by Belal and accepted by Cristina and Ángel: delivered scope (Hoja1, phase B "
           "per decisions, cycle, accounting, reports, data, permissions, documentation, training 1), open items with "
           "owner and date, pilot start criteria (T01).\nMilestone approved by Belal on 26/10/2026: full delivery on "
           "20/11/2026, with the approved scope and the Hoja1 requirements; manual cost for services without a tariff "
           "only as an exception approved by Belal (X01), and those requirements stay «Partial».",
    "R01": f"{RETRO_EN}\nResult: boss_services with the services as standard products, charge bases as units, cost mode "
           "(tariff, manual, own, pending) and VAT class.",
    "R02": f"{RETRO_EN}\nResult: Ángel's rules (31/08) as pure functions and a configurable table; a case without a row "
           "leaves the VAT pending and blocks sending or accepting.",
    "R03": f"{RETRO_EN}\nResult: «expected cost of the line» base in pricelist rules, markup or margin on sale, minimum "
           "margin; the values per customer are set by Cristina (P01/P02).",
    "R04": f"{RETRO_EN}\nResult: boss_expediente: E26xxxx file opened on acceptance, analytic account, parties and roles, "
           "RFQs without duplicates, «Mark as performed», invoicing by service (milestones), credit notes, extra cost "
           "re-invoiced, posting checks and profitability summary with the source of each figure.",
    "R05": f"{RETRO_EN}\nResult: expected cost recomputed from file data (recompute history), split of an accepted "
           "quotation across files, BOSS or supplier service added after acceptance with reason and snapshot.",
    "R06": f"{RETRO_EN}\nResult: 30 ES/EN pages (cycle, roles, tariffs, methods, services, file, purchases, invoicing, "
           "profitability, storage, decisions) with real screenshots.",
    "R07": f"{RETRO_EN}\nResult: modules deployed with the web stopped; VAT table (Art.22, CAN), exchange rate, payment "
           "block, control on received quantities, paid-on-behalf (419000: see D-2).",
    "R08": f"{RETRO_EN}\nResult: 10 [MUESTRA] tariffs from real documents, each price with its page; reference examples "
           "R1–R27 and automated test with the private samples.",
    "R09": f"{RETRO_EN}\nResult: proposals approved by Belal with phase A/B/C; pending ratification by Ángel (finance, "
           "VAT) and Cristina (services, prices, operations).",
    "R10": f"{RETRO_EN}\nResult: form and list load times in Chrome with a normal session; the 20–50 s waits came from "
           "the hidden panel of the built-in browser, not from the server.",
    "S01": "Result: incidents of report T08 fixed by priority, with test and retest. Acceptance: list closed and "
           "approved by Cristina and Ángel.",
    "S02": "Rule: until 31/12 Odoo 17 is the only system of record; Odoo 20 is for tests only. New data (files created "
           "or changed since the last rehearsal) is loaded as differences (modification date and legacy id stored in "
           "«Reference»), without duplicates; procedure written and tested in rehearsal S04.\nAcceptance: document "
           "approved by Belal and Cristina.",
    "S03": "Result: each person has done their scenario without help; one-page go-live guide per role.\nParticipants "
           f"per Cristina and Ángel. {PROPOSED}",
    "S04": "Result: full rehearsal of procedure G01–G05 on the local copy with measured times; reconciliation of open "
           "files, balances and numbering; checklist corrected. Acceptance: 0 unexplained differences; total time known.",
    "S05": "Result: restore of the latest backup tested; rollback plan (stay on Odoo 17) approved by Belal.",
    "S06": "Result: checklist G01–G06 with cut-off time, owners, verifiable acceptance criteria and a plan for any "
           f"obstacle; approved by Cristina (operations) and Ángel (accounting).\n{PROPOSED}",
    "T01": "Start: delivery accepted, master data migrated, users trained, daily backup active. Exit: every scenario run "
           "by its owner with the result recorded, critical incidents fixed and retested, closing report. «Passes with "
           "[DEMO]» is distinguished from «passes with representative operational data» (migrated and approved by "
           "Cristina).\nLog: Fix tasks on this platform, one per incident.",
    "T02": "With a real representative shipment (migrated customer, carrier with an approved tariff) in the test "
           "environment; result and remarks recorded by the operator.\nOwner: to be assigned (operations; Cristina "
           f"decides who). {PROPOSED}",
    "T03": "With real representative shipments; checks NOA/ATA, actual period and recompute, proposed handler.\nOwner: "
           f"to be assigned (operations). {PROPOSED}",
    "T04": f"With real representative shipments.\nOwner: to be assigned. {PROPOSED}",
    "T05": "On the files of T02–T04 in the test environment (never in the real books of boss20 before 1/1): post, pay, "
           f"credit; check accounts, taxes and the invoicing and profitability reports.\n{PROPOSED}",
    "T06": "With real migrated customers and the pricelists Cristina decides (P01/P02).\nOwner: to be assigned (sales). "
           f"{PROPOSED}",
    "T07": "Result: each incident logged as a task, fixed with a test, deployed to the test environment and retested by "
           "whoever opened it. Acceptance: no critical incident open on 1/12.",
    "T08": "Result: scenarios run and their result, incidents opened and closed, what passes with [DEMO] versus what is "
           "verified with real data, and the list of what goes into stabilisation. Milestone approved by Belal: pilot "
           "until 1/12/2026.",
    "U01": "Result: groups and rules checked with one user per role (sales, operations, purchasing, accounting); BOSS "
           "outgoing mail server configured and tested to an internal mailbox; quotation and invoice templates with "
           "BOSS legal data (address, VAT number, terms) reviewed by Ángel.\nAcceptance: screenshot per role; test "
           "e-mail received; quotation and invoice PDFs approved.",
    "U02": "Result: 2 h session with the guide as material, on the [DEMO] data and migrated master data; questions "
           f"logged as tasks.\nParticipants as Cristina indicates. {PROPOSED}\nAcceptance: attendees create and accept "
           "a quotation without help.",
    "V01": "Result: with a [DEMO] air file on boss20: NOA and ATA with time propagate the ALM period and recompute the "
           "cost (H1-21, H1-22); choosing airline and airport proposes the handler validated by Cristina (H1-23, H1-24, "
           "H1-26); screenshots in the guide.\nAcceptance: behaviour observed on boss20 (not only the field on screen); "
           "docs/mapeo-hoja1.md updated with the evidence.",
    "W01": "Result: docs/pruebas-angel.md (8 cases, 90 min, environment per case); isolated local copy (dev/test.sh "
           "uat: no scheduled jobs, mail or online services); rolled-back dry run that found defects D-1 and D-2.",
    "W02": "Result: docs/revision-tarifas.md (10 tariffs: document, validity, services, scope, decision) and "
           "docs/especificacion-alm-venta.md (rule of 25/09 read in Odoo 19, 14 points to decide).",
    "W03": "Result: docs/mapeo-hoja1.md (28 requirements with status, test, evidence and tasks) and this plan (weekly "
           "sprints until 8/1/2027) seeded on the platform. Review: Belal.",
    "W04": "Three decisions Belal deferred on 26/10 until the plan was finished, decided the same day:\n1) D-1: local "
           "fix with tests approved; deployment to boss20 is a separate task after verification (W09).\n2) D-2: prepare "
           "the account map, the fix and the invoicing tests locally and present them to Ángel; the accounting change "
           "on boss20 depends on his approval of the map (W10); reverting to the category accounts is NOT approved.\n"
           "3) Guide: publish the corrected version after checking the build, explaining the open defects and pending "
           "decisions (W07).",
    "W05": "Result: `_boss_bill_needs` (boss_expediente/models/account_move.py) ignores bill lines with quantity 0; test "
           "in test_file_followup.\nSource: defect D-1 of the 26/10 dry run (docs/pruebas-angel.md).\nAcceptance: new "
           "test green; payment allowed after invoicing the customer even when the order has services not performed. "
           "Deployment to boss20 is task W09.",
    "W06": "Result: proposal so that ARA, IVA, PLA and DUM can be invoiced to the customer and recorded on the broker's "
           "bill.\nSource: defect D-2 (419000 is a payable account; Odoo 17 uses 419001–419007, current liabilities).\n"
           "Belal's decision (26/10, W04-2): prepare the account map, the fix and the tests locally and present them to "
           "Ángel; reverting to the category accounts is not approved. The change on boss20 is task W10, which depends "
           "on Ángel's approval (A02).\nAcceptance: docs/cuentas-suplidos.md, script dev/setup_suplidos_accounts.py and "
           "automated test green (broker bill and customer invoice with the proposed accounts).",
    "W07": "Result: doc.bosscontinental.com/new with the corrected pages (decisions with a «Ratification» column, open "
           "accounting questions, defects D-1 and D-2). Acceptance: the «Pending decisions» page shows «Ratification» "
           "and the known defects (checked with curl).",
    "W08": "Result: internal users on boss20 (today only Belal's exists): Ángel (Accounting administrator, Sales all "
           "documents, Purchase user), Cristina (Sales administrator, Purchase, tariff approver) and those Cristina "
           "names for operations; with no mail server, passwords are handed over in person.\nAcceptance: each person "
           "logs in and sees what the guide page «Roles» describes (test with screenshot).",
    "W09": "Result: boss_expediente with the D-1 fix deployed to boss20 (dev/deploy.sh, web stopped) after the Odoo and "
           "engine tests pass; read check afterwards.\nBelal's decision (26/10, W04-1): deployment is a task separate "
           "from the fix.\nAcceptance: version installed on boss20 = commit; boss20 read without errors.",
    "W10": "Result: accounts 419001–419007 (or those Ángel approves) created on boss20 and assigned to ARA, IVA, PLA and "
           "DUM with dev/setup_suplidos_accounts.py --approved-by-angel; the ARA draft invoice of E260001 is created "
           "without error.\nBlocker: waits for Ángel's approval of the map (docs/cuentas-suplidos.md, A02). Meanwhile "
           "the ARA line of E260001 cannot be invoiced on boss20 (defect D-2).\nAcceptance: boss20 read with the "
           "accounts and the map; ARA draft invoice created.",
    "X01": "Belal's rule (26/10): the 20/11 delivery includes the approved scope and the Hoja1 requirements; a manual "
           "cost for a service without a tariff is an exception that needs his approval, and the requirement concerned "
           "stays «Partial».\nResult: list of Hoja1 services still without an approved tariff on 16/11, with the reason "
           "(document not received, not approved, decision pending) and Belal's approval or not of the exception per "
           "service; reflected in docs/mapeo-hoja1.md and in the delivery minutes (Q04).",
}
ORIG_EN = {
    "000": "Summary of what is asked and what is not, with questions for Belal (step 1 of the KICKOFF). Acceptance: "
           "Belal answers the questions.",
    "001": "Adapt task.bosscontinental.com to the project: dated sprints, Product/Sprint Backlog, board, story points, "
           "burndown and Gantt. Acceptance: published and checked in the browser.",
    "002": "addons/, docs/adr, docs/services, docs/requirements, tests/fixtures and tools. .gitignore excludes the Odoo "
           "source and supplier PDFs. CLAUDE.md with the project rules. Acceptance: proposal reviewed by Belal before "
           "creating it.",
    "003": "Step 6, only after steps 2–5 are approved. Docker Desktop is not stable: local venv with PostgreSQL 16 or a "
           "container on the server (with approval). Acceptance: Odoo 20 starts and runs a sample test.",
    "004": "docs/adr/001: version, overall architecture, proposed pricing modules and the responsibility of each. "
           "Context, alternatives, decision and consequences.",
    "005": "Supplier tariff with document, validity and versions; price line per service; methods (fixed, per unit, "
           "brackets, percentage, time-based); scope conditions; minimum/maximum; approval; single matching and pricing "
           "service; specialisation modules. With alternatives and examples.",
    "006": "Template with: what the service is, how suppliers charge it, lessons from Odoo 19, industry practice, "
           "proposed decision, open questions and golden cases.",
    "007": "Quality tools and creation of the repository in dev1bms (only with Belal's approval).",
    "010": "docs/services/THC.md per the template: the sample study of step 5. Business rules stay pending approval by "
           "Ángel or Cristina.",
    "011": "docs/services/BL-DOC.md per the template.",
    "012": "docs/services/T3.md per the template.",
    "013": "docs/services/DEM-OCU.md: free days, events that open and close the count, brackets and golden cases.",
    "014": "docs/services/GLO.md per the template.",
    "015": "docs/services/FAD.md per the template.",
    "016": "docs/services/TTE-FCL.md: road transport by route and brackets.",
    "017": "docs/services/FMI.md: the main freight comes with a supplier offer.",
    "020": "Fixed, per unit, brackets, percentage and time-based methods, without Odoo. Acceptance: unit tests on the "
           "THC golden cases green.",
    "021": "Each price linked to its PDF and page. The price line belongs to the service (lesson from Odoo 19). First "
           "task to postpone if the engine takes longer.",
    "022": "Direction, mode, shipment type, ports/zones, supplier role and customer. One single service called by every "
           "screen.",
    "023": "Containers, weights, volumes, dates and route; only what is needed to test the expected cost.",
    "024": "Specialisation on top of the general engine for time-based charges.",
    "025": "One single way to enter a price, linked to its document.",
    "026": "Source strings in English and translation in .po; no accepted failures.",
    "030": "Demonstration of the cost calculation and list of open questions pending their approval.",
}
BLOCKED_EN = {"W10": "Waiting for Ángel to approve the paid-on-behalf account map (docs/cuentas-suplidos.md, task A02)."}

class Command(BaseCommand):
    help = "Siembra idempotente del plan de lanzamiento BOSS Odoo 20 (26/10/2026): sprints semanales, epics, tareas."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="No guarda nada; muestra lo que haría.")

    def handle(self, *args, **options):
        dry = options["dry_run"]
        with transaction.atomic():
            self.apply()
            if dry:
                transaction.set_rollback(True)
                self.stdout.write(self.style.WARNING("dry-run: nada guardado"))

    def apply(self):
        users = get_user_model().objects
        people = {key: users.filter(username=username).first() for key, username in USERS.items()}
        owner = people["belal"]
        if owner is None:
            raise CommandError("No existe el usuario de Belal en la plataforma.")
        for key, user in people.items():
            if user is None:
                raise CommandError(f"No existe el usuario {USERS[key]}.")

        for day, name in HOLIDAYS:
            Holiday.objects.get_or_create(date=day, defaults={"name": name})
        depts = {key: Department.objects.get_or_create(name=name, defaults={"icon": "📌"})[0]
                 for key, name in DEPTS.items()}
        epics = {key: Phase.objects.update_or_create(name=name, defaults={"order": order})[0]
                 for order, (key, name) in enumerate(EPICS.items(), start=1)}

        from panel.models import working_days
        hours_per_day = 7  # horas de desarrollo útiles por día laborable de Belal
        sprints = {}
        for key, (name, start, end, status, goal, old_name) in SPRINTS.items():
            days = len(working_days(start, end))
            belal_hours = sum(float(r["hours"]) for r in TASKS if r["sprint"] == key and r["who"] == "belal"
                              and r["status"] not in (S.DONE, S.CANCELLED))
            waiting = [r["code"] for r in TASKS if r["sprint"] == key and r["who"] != "belal"]
            capacity = days * hours_per_day
            goal = (f"{goal}\nCapacidad: {days} días laborables × {hours_per_day} h = {capacity} h de Belal · "
                    f"Planificado para Belal: {belal_hours:.0f} h"
                    + (f" (EXCESO {belal_hours - capacity:.0f} h)" if belal_hours > capacity else "")
                    + (f" · Decisiones/datos de otros: {', '.join(waiting)}" if waiting else ""))
            sprint = Sprint.objects.filter(name=name).first()
            if sprint is None and old_name:
                sprint = Sprint.objects.filter(name=old_name).first()
            if sprint is None:
                sprint = Sprint(name=name)
            sprint.name, sprint.start_date, sprint.end_date, sprint.status, sprint.goal = name, start, end, status, goal
            sprint.save()
            sprints[key] = sprint

        tasks, created, updated, status_changes = {}, 0, 0, 0
        for order, row in enumerate(TASKS, start=1):
            code = f"BOSS20-{row['code']}"
            plan = {
                "title": TITLES_EN.get(row["code"], row["title"]), "description": DESCS_EN.get(row["code"], row["desc"]) + (
                    "\n\nOriginal description (plan of 21/10/2026): " + ORIG_EN[row["code"]]
                    if row["code"] in ORIG_EN else ""), "phase": epics[row["epic"]],
                "task_type": row["type"], "sprint": sprints.get(row["sprint"]), "story_points": row["points"],
                "start_date": row["start"], "due_date": row["due"], "priority": row["priority"],
                "backlog_order": order * 10, "estimated_hours": row["hours"], "assigned_to": people[row["who"]],
                "department": depts[row["dept"]], "related_links": "\n".join(row["links"]),
                "blocked_reason": BLOCKED_EN.get(row["code"], ""),
            }
            task = Task.objects.filter(code=code).first()
            if task is None:
                task = Task(code=code, created_by=owner, **plan)
                if row.get("progress") is not None:
                    task.progress = row["progress"]
                if row["status"]:
                    task.status = row["status"]
                    if row["status"] == S.DONE and row["done"]:
                        task.completed_at = mad(row["done"])
                task.save()
                log_activity(owner, task=task, change_type="creación",
                             description=f"{owner.get_full_name()} creó la tarea (plan de lanzamiento del 26/10/2026).")
                created += 1
                self.stdout.write(f"  + {code} {row['title'][:70]}")
            else:
                snapshot = snapshot_task(task)
                for field, value in plan.items():
                    setattr(task, field, value)
                if row.get("progress") is not None and task.status != S.DONE:
                    task.progress = row["progress"]
                last = task.activity.filter(change_type="status").order_by("-created_at").first()
                touched_by_person = task.activity.filter(change_type="status").exclude(user=owner).exists()
                if touched_by_person and row["status"] and task.status != row["status"]:
                    self.stdout.write(f"  ! {code}: estado cambiado por otra persona; se respeta")
                if row["status"] and task.status != row["status"] and not touched_by_person:
                    task.status = row["status"]
                    if row["status"] == S.DONE and row["done"]:
                        task.completed_at = mad(row["done"])
                    status_changes += 1
                task.save()
                log_task_changes(owner, task, snapshot)
                updated += 1
                self.stdout.write(f"  ~ {code} {row['title'][:70]}")
            if row["evidence"] and not Comment.objects.filter(task=task, text=row["evidence"]).exists():
                Comment.objects.create(task=task, author=owner, text=row["evidence"])
            tasks[row["code"]] = task
        for row in TASKS:
            tasks[row["code"]].depends_on.set([tasks[d] for d in row["deps"]])

        self.stdout.write("IDS " + " ".join(f"{row['code']}={tasks[row['code']].pk}" for row in TASKS))
        for key, sprint in sprints.items():
            self.stdout.write("CAPACITY " + key + " | " + sprint.goal.split("\n")[-1])
        self.stdout.write(self.style.SUCCESS(
            f"{len(sprints)} sprints · {len(EPICS)} epics · {len(TASKS)} tareas ({created} nuevas, {updated} "
            f"actualizadas, {status_changes} cambios de estado con evidencia)"))
