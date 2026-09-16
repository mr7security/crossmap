import json, pathlib
# The Sarbanes-Oxley Act of 2002 (Pub. L. 107-204) has no catalogue of IT
# controls. What auditors test under Section 404 is the set of IT General
# Controls (ITGC) that COSO 2013 and PCAOB AS 2201 treat as the technology
# underpinning of internal control over financial reporting (ICFR). The list
# below is the classic four-domain ITGC catalogue as it is used in practice
# (access to programs and data, program changes, program development, computer
# operations), preceded by the entity-level expectations and by the sections of
# the Act that create the obligation. It is a synthesis of common practice, not
# an official taxonomy, and the catalogue says so in its source note.
FAM = {
 "act": ("Sarbanes-Oxley Act sections", "Secciones de la ley Sarbanes-Oxley"),
 "elc": ("Entity-level controls (COSO)", "Controles a nivel de entidad (COSO)"),
 "acc": ("ITGC - Access to programs and data", "ITGC - Acceso a programas y datos"),
 "chg": ("ITGC - Program changes", "ITGC - Cambios en programas"),
 "dev": ("ITGC - Program development", "ITGC - Desarrollo de programas"),
 "ops": ("ITGC - Computer operations", "ITGC - Operaciones informaticas"),
}
ITEMS = [
("sec.302","act","law","Corporate responsibility for financial reports: officers certify the reports and the effectiveness of disclosure controls","Responsabilidad corporativa sobre los informes financieros: los directivos certifican los informes y la eficacia de los controles de divulgacion"),
("sec.404","act","law","Management assessment of internal control over financial reporting and auditor attestation","Evaluacion por la direccion del control interno sobre la informacion financiera y atestacion del auditor"),
("sec.409","act","law","Real-time disclosure of material changes in financial condition or operations","Divulgacion en tiempo real de cambios materiales en la situacion financiera o las operaciones"),
("sec.802","act","law","Retention of audit records and criminal penalties for altering or destroying them","Conservacion de los registros de auditoria y sanciones penales por alterarlos o destruirlos"),
("sec.906","act","law","Criminal certification of periodic financial reports by the CEO and CFO","Certificacion penal de los informes financieros periodicos por el CEO y el CFO"),
("elc.1","elc","itgc","Control environment: tone at the top, IT governance and defined responsibilities over financial systems","Entorno de control: tono desde la direccion, gobierno de TI y responsabilidades definidas sobre los sistemas financieros"),
("elc.2","elc","itgc","IT risk assessment over the systems that support financial reporting","Evaluacion de riesgos de TI sobre los sistemas que soportan la informacion financiera"),
("elc.3","elc","itgc","Policies and procedures for information technology are documented, approved and communicated","Las politicas y procedimientos de tecnologias de la informacion estan documentados, aprobados y comunicados"),
("elc.4","elc","itgc","Monitoring: internal audit, control self-assessment and remediation of deficiencies","Supervision: auditoria interna, autoevaluacion de controles y remediacion de deficiencias"),
("elc.5","elc","itgc","Reliance on service organisations is supported by SOC 1 reports and complementary user controls","La dependencia de organizaciones de servicios se soporta con informes SOC 1 y controles complementarios del usuario"),
("acc.1","acc","itgc","User access provisioning is requested, approved and granted according to the role","El alta de acceso de usuarios se solicita, aprueba y concede segun el rol"),
("acc.2","acc","itgc","Access is removed promptly on termination or transfer","El acceso se retira con prontitud al cesar o cambiar de puesto"),
("acc.3","acc","itgc","Periodic review of user access rights by the business owner","Revision periodica de los derechos de acceso de los usuarios por el propietario de negocio"),
("acc.4","acc","itgc","Privileged and administrative access is restricted, approved and monitored","El acceso privilegiado y administrativo esta restringido, aprobado y supervisado"),
("acc.5","acc","itgc","Authentication parameters: unique identifiers, password rules and multi-factor where applicable","Parametros de autenticacion: identificadores unicos, reglas de contrasena y multifactor cuando aplique"),
("acc.6","acc","itgc","Segregation of duties within financial applications and between IT roles","Segregacion de funciones dentro de las aplicaciones financieras y entre los roles de TI"),
("acc.7","acc","itgc","Physical access to data centres and computer rooms is restricted","El acceso fisico a los centros de datos y salas de servidores esta restringido"),
("acc.8","acc","itgc","Security logging and monitoring of financial systems, with review of security events","Registro y supervision de seguridad de los sistemas financieros, con revision de los eventos de seguridad"),
("acc.9","acc","itgc","Direct access to data (database, operating system) and the use of powerful utilities are restricted","El acceso directo a los datos (base de datos, sistema operativo) y el uso de utilidades potentes estan restringidos"),
("chg.1","chg","itgc","Changes are requested, authorised and approved before development","Los cambios se solicitan, autorizan y aprueban antes de desarrollarse"),
("chg.2","chg","itgc","Changes are tested and accepted by the business before release","Los cambios se prueban y son aceptados por el negocio antes de su puesta en produccion"),
("chg.3","chg","itgc","Segregation between development, test and production, and restricted migration to production","Segregacion entre desarrollo, pruebas y produccion, y migracion a produccion restringida"),
("chg.4","chg","itgc","Emergency changes are controlled and approved retrospectively","Los cambios de emergencia estan controlados y se aprueban a posteriori"),
("chg.5","chg","itgc","Configuration, patches and infrastructure changes follow the change process","La configuracion, los parches y los cambios de infraestructura siguen el proceso de cambios"),
("dev.1","dev","itgc","A system development methodology governs new systems and major enhancements","Una metodologia de desarrollo de sistemas gobierna los nuevos sistemas y las mejoras importantes"),
("dev.2","dev","itgc","Data conversion and migration are controlled and reconciled","La conversion y migracion de datos estan controladas y conciliadas"),
("dev.3","dev","itgc","Implementation of a new system is approved and its controls tested before go-live","La implantacion de un nuevo sistema se aprueba y sus controles se prueban antes de la puesta en marcha"),
("ops.1","ops","itgc","Batch jobs and interfaces are scheduled, monitored and failures resolved","Los procesos por lotes y las interfaces se planifican y supervisan, y los fallos se resuelven"),
("ops.2","ops","itgc","Backups of financial data are taken, monitored and periodically restored","Se realizan copias de seguridad de los datos financieros, se supervisan y se restauran periodicamente"),
("ops.3","ops","itgc","Incidents and problems affecting financial systems are recorded, resolved and escalated","Los incidentes y problemas que afectan a los sistemas financieros se registran, resuelven y escalan"),
("ops.4","ops","itgc","Continuity and recovery of the systems that support financial reporting","Continuidad y recuperacion de los sistemas que soportan la informacion financiera"),
]
items = [{
    "id": cid, "layer": layer, "family": fam,
    "family_title": {"en": FAM[fam][0], "es": FAM[fam][1]},
    "title": {"en": en, "es": es},
} for cid, fam, layer, en, es in ITEMS]
pathlib.Path("crossmap/data/controls_sox.json").write_text(
    json.dumps({"framework": "SOX", "items": items}, ensure_ascii=False, indent=1))
print("SOX:", len(items), "items")
