import json, pathlib
# Titles verified against the official EN and ES texts of Regulation (EU) 2022/2554
# published in OJ L 333, 27.12.2022.
ARTS = [
("5","II","Governance and organisation","Gobernanza y organizacion"),
("6","II","ICT risk management framework","Marco de gestion del riesgo relacionado con las TIC"),
("7","II","ICT systems, protocols and tools","Sistemas, protocolos y herramientas de TIC"),
("8","II","Identification","Identificacion"),
("9","II","Protection and prevention","Proteccion y prevencion"),
("10","II","Detection","Deteccion"),
("11","II","Response and recovery","Respuesta y recuperacion"),
("12","II","Backup policies and procedures, restoration and recovery procedures and methods","Politicas y procedimientos de respaldo y procedimientos y metodos de restablecimiento y recuperacion"),
("13","II","Learning and evolving","Aprendizaje y evolucion"),
("14","II","Communication","Comunicacion"),
("15","II","Further harmonisation of ICT risk management tools, methods, processes and policies","Mayor armonizacion de las herramientas, metodos, procesos y politicas de gestion del riesgo relacionado con las TIC"),
("16","II","Simplified ICT risk management framework","Marco simplificado de gestion del riesgo relacionado con las TIC"),
("17","III","ICT-related incident management process","Proceso de gestion de incidentes relacionados con las TIC"),
("18","III","Classification of ICT-related incidents and cyber threats","Clasificacion de los incidentes relacionados con las TIC y las ciberamenazas"),
("19","III","Reporting of major ICT-related incidents and voluntary notification of significant cyber threats","Notificacion de los incidentes graves relacionados con las TIC y notificacion voluntaria de las ciberamenazas importantes"),
("20","III","Harmonisation of reporting content and templates","Armonizacion del contenido de la informacion y las plantillas para presentarla"),
("21","III","Centralisation of reporting of major ICT-related incidents","Centralizacion de la informacion sobre los incidentes graves relacionados con las TIC"),
("22","III","Supervisory feedback","Observaciones de las autoridades de supervision"),
("23","III","Operational or security payment-related incidents concerning credit institutions, payment institutions, account information service providers, and electronic money institutions","Incidentes operativos o de seguridad relacionados con los pagos que atanen a entidades de credito, entidades de pago, proveedores de servicios de informacion sobre cuentas y entidades de dinero electronico"),
("24","IV","General requirements for the performance of digital operational resilience testing","Requisitos generales para la realizacion de pruebas de resiliencia operativa digital"),
("25","IV","Testing of ICT tools and systems","Pruebas de las herramientas y los sistemas de TIC"),
("26","IV","Advanced testing of ICT tools, systems and processes based on TLPT","Pruebas avanzadas de las herramientas, los sistemas y los procesos de TIC basadas en pruebas de penetracion basadas en amenazas"),
("27","IV","Requirements for testers for the carrying out of TLPT","Requisitos aplicables a los probadores para la realizacion de pruebas de penetracion basadas en amenazas"),
("28","V","General principles","Principios generales"),
("29","V","Preliminary assessment of ICT concentration risk at entity level","Evaluacion preliminar del riesgo de concentracion de TIC a nivel de la entidad"),
("30","V","Key contractual provisions","Clausulas contractuales fundamentales"),
("45","VI","Information-sharing arrangements on cyber threat information and intelligence","Acuerdos de intercambio de informacion en relacion con informacion e inteligencia sobre ciberamenazas"),
]
CH = {
 "II":("ICT risk management","Gestion del riesgo relacionado con las TIC"),
 "III":("ICT-related incident management, classification and reporting","Gestion, clasificacion y notificacion de incidentes relacionados con las TIC"),
 "IV":("Digital operational resilience testing","Pruebas de resiliencia operativa digital"),
 "V":("Managing of ICT third-party risk","Gestion del riesgo relacionado con las TIC derivado de terceros"),
 "VI":("Information-sharing arrangements","Acuerdos de intercambio de informacion"),
}
# Level 2 acts developing chapters II and V, all published in the OJ.
RTS = [
("rts.2024/1774","II","RTS on ICT risk management tools, methods, processes and policies and on the simplified framework (Delegated Regulation (EU) 2024/1774, OJ 25.6.2024)",
 "NTR sobre herramientas, metodos, procesos y politicas de gestion del riesgo TIC y sobre el marco simplificado (Reglamento Delegado (UE) 2024/1774, DOUE 25.6.2024)"),
("rts.2024/1773","V","RTS on the policy on contractual arrangements for ICT services supporting critical or important functions (Delegated Regulation (EU) 2024/1773, OJ 25.6.2024)",
 "NTR sobre la politica relativa a los acuerdos contractuales de servicios TIC que sustentan funciones esenciales o importantes (Reglamento Delegado (UE) 2024/1773, DOUE 25.6.2024)"),
("its.2024/2956","V","ITS on the standard templates for the register of information (Implementing Regulation (EU) 2024/2956, OJ 2.12.2024)",
 "NTE sobre las plantillas normalizadas para el registro de informacion (Reglamento de Ejecucion (UE) 2024/2956, DOUE 2.12.2024)"),
("rts.2025/532","V","RTS on subcontracting of ICT services supporting critical or important functions (Delegated Regulation (EU) 2025/532, OJ 2.7.2025)",
 "NTR sobre la subcontratacion de servicios TIC que sustentan funciones esenciales o importantes (Reglamento Delegado (UE) 2025/532, DOUE 2.7.2025)"),
("rts.2024/1772","III","RTS on the classification of major ICT-related incidents (Delegated Regulation (EU) 2024/1772, OJ 25.6.2024)",
 "NTR sobre la clasificacion de los incidentes graves relacionados con las TIC (Reglamento Delegado (UE) 2024/1772, DOUE 25.6.2024)"),
("rts.2025/1190","IV","RTS on threat-led penetration testing (Delegated Regulation (EU) 2025/1190, OJ 18.6.2025)",
 "NTR sobre las pruebas de penetracion basadas en amenazas (Reglamento Delegado (UE) 2025/1190, DOUE 18.6.2025)"),
]
items = [{"id":f"art.{n}","layer":"regulation","family":ch,
          "family_title":{"en":f"Chapter {ch} - {CH[ch][0]}","es":f"Capitulo {ch} - {CH[ch][1]}"},
          "title":{"en":en,"es":es}} for n,ch,en,es in ARTS]
items += [{"id":i,"layer":"technical_standard","family":ch,
           "family_title":{"en":f"Chapter {ch} - {CH[ch][0]}","es":f"Capitulo {ch} - {CH[ch][1]}"},
           "title":{"en":en,"es":es}} for i,ch,en,es in RTS]
pathlib.Path("crossmap/data/controls_dora.json").write_text(
    json.dumps({"framework":"DORA","items":items}, ensure_ascii=False, indent=1))
print("DORA:", len(items), "elementos |", len(ARTS), "articulos +", len(RTS), "normas de nivel 2")
