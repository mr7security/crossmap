import json, pathlib
# Layer 1: Article 21(2) of Directive (EU) 2022/2555 - applies to every essential
# and important entity.
ART21 = [
("21.2.a","Policies on risk analysis and information system security",
 "Politicas de analisis de riesgos y de seguridad de los sistemas de informacion"),
("21.2.b","Incident handling","Gestion de incidentes"),
("21.2.c","Business continuity, such as backup management and disaster recovery, and crisis management",
 "Continuidad de la actividad, como la gestion de copias de seguridad y la recuperacion en caso de catastrofe, y gestion de crisis"),
("21.2.d","Supply chain security, including security-related aspects concerning the relationships between each entity and its direct suppliers or service providers",
 "Seguridad de la cadena de suministro, incluidos los aspectos de seguridad relativos a las relaciones entre cada entidad y sus proveedores directos o prestadores de servicios"),
("21.2.e","Security in network and information systems acquisition, development and maintenance, including vulnerability handling and disclosure",
 "Seguridad en la adquisicion, el desarrollo y el mantenimiento de sistemas de redes y de informacion, incluida la gestion y divulgacion de las vulnerabilidades"),
("21.2.f","Policies and procedures to assess the effectiveness of cybersecurity risk-management measures",
 "Politicas y procedimientos para evaluar la eficacia de las medidas para la gestion de riesgos de ciberseguridad"),
("21.2.g","Basic cyber hygiene practices and cybersecurity training",
 "Practicas basicas de ciberhigiene y formacion en ciberseguridad"),
("21.2.h","Policies and procedures regarding the use of cryptography and, where appropriate, encryption",
 "Politicas y procedimientos relativos a la utilizacion de criptografia y, en su caso, de cifrado"),
("21.2.i","Human resources security, access control policies and asset management",
 "Seguridad de los recursos humanos, politicas de control de acceso y gestion de activos"),
("21.2.j","Use of multi-factor authentication or continuous authentication solutions, secured voice, video and text communications and secured emergency communication systems",
 "Utilizacion de soluciones de autenticacion multifactorial o de autenticacion continua, comunicaciones de voz, video y texto protegidas y sistemas de comunicaciones de emergencia protegidos"),
]
GOV = [
("20","Governance: management bodies approve the risk-management measures, oversee their implementation and follow cybersecurity training",
 "Gobernanza: los organos de direccion aprueban las medidas de gestion de riesgos, supervisan su aplicacion y siguen formacion en ciberseguridad"),
("23","Reporting obligations: early warning within 24 hours, incident notification within 72 hours and final report within one month",
 "Obligaciones de notificacion: alerta temprana en 24 horas, notificacion del incidente en 72 horas e informe final en un mes"),
]
# Layer 2: Annex to Commission Implementing Regulation (EU) 2024/2690, the only
# binding articulation of Article 21(2) so far. Legally it binds DNS, TLD, cloud,
# data centre, CDN, managed service, marketplace, search engine, social network
# and trust service providers; for everyone else it is the reference of choice.
CIR = [
("1.1","Policy on the security of network and information systems","Politica de seguridad de las redes y sistemas de informacion","1"),
("1.2","Roles, responsibilities and authorities","Funciones, responsabilidades y autoridades","1"),
("2.1","Risk management framework","Marco de gestion de riesgos","2"),
("2.2","Compliance monitoring","Seguimiento del cumplimiento","2"),
("2.3","Independent review of information and network security","Revision independiente de la seguridad de la informacion y de las redes","2"),
("3.1","Incident handling policy","Politica de gestion de incidentes","3"),
("3.2","Monitoring and logging","Monitorizacion y registro","3"),
("3.3","Event reporting","Notificacion de eventos","3"),
("3.4","Event assessment and classification","Evaluacion y clasificacion de eventos","3"),
("3.5","Incident response","Respuesta a incidentes","3"),
("3.6","Post-incident reviews","Revisiones posteriores a incidentes","3"),
("4.1","Business continuity and disaster recovery plan","Plan de continuidad de negocio y de recuperacion ante desastres","4"),
("4.2","Backup and redundancy management","Gestion de copias de seguridad y redundancia","4"),
("4.3","Crisis management","Gestion de crisis","4"),
("5.1","Supply chain security policy","Politica de seguridad de la cadena de suministro","5"),
("5.2","Directory of suppliers and service providers","Directorio de proveedores y prestadores de servicios","5"),
("6.1","Security in acquisition of ICT services or ICT products","Seguridad en la adquisicion de servicios o productos TIC","6"),
("6.2","Secure development life cycle","Ciclo de vida de desarrollo seguro","6"),
("6.3","Configuration management","Gestion de la configuracion","6"),
("6.4","Change management, repairs and maintenance","Gestion de cambios, reparaciones y mantenimiento","6"),
("6.5","Security testing","Pruebas de seguridad","6"),
("6.6","Security patch management","Gestion de parches de seguridad","6"),
("6.7","Network security","Seguridad de la red","6"),
("6.8","Network segmentation","Segmentacion de la red","6"),
("6.9","Protection against malicious and unauthorised software","Proteccion contra software malicioso y no autorizado","6"),
("6.10","Vulnerability handling and disclosure","Gestion y divulgacion de vulnerabilidades","6"),
("7","Policies and procedures to assess the effectiveness of cybersecurity risk-management measures","Politicas y procedimientos para evaluar la eficacia de las medidas de gestion de riesgos de ciberseguridad","7"),
("8.1","Awareness raising and basic cyber hygiene practices","Concienciacion y practicas basicas de ciberhigiene","8"),
("8.2","Security training","Formacion en seguridad","8"),
("9","Cryptography","Criptografia","9"),
("10.1","Human resources security","Seguridad de los recursos humanos","10"),
("10.2","Verification of background","Verificacion de antecedentes","10"),
("10.3","Termination or change of employment procedures","Procedimientos de finalizacion o cambio de empleo","10"),
("10.4","Disciplinary process","Proceso disciplinario","10"),
("11.1","Access control policy","Politica de control de acceso","11"),
("11.2","Management of access rights","Gestion de los derechos de acceso","11"),
("11.3","Privileged accounts and system administration accounts","Cuentas privilegiadas y cuentas de administracion de sistemas","11"),
("11.4","Administration systems","Sistemas de administracion","11"),
("11.5","Identification","Identificacion","11"),
("11.6","Authentication","Autenticacion","11"),
("11.7","Multi-factor authentication","Autenticacion multifactorial","11"),
("12.1","Asset classification","Clasificacion de activos","12"),
("12.2","Handling of assets","Manipulacion de activos","12"),
("12.3","Removable media policy","Politica de soportes extraibles","12"),
("12.4","Asset inventory","Inventario de activos","12"),
("12.5","Deposit, return or deletion of assets upon termination of employment","Deposito, devolucion o borrado de activos al finalizar el empleo","12"),
("13.1","Supporting utilities","Instalaciones de suministro","13"),
("13.2","Protection against physical and environmental threats","Proteccion frente a amenazas fisicas y ambientales","13"),
("13.3","Perimeter and physical access control","Perimetro y control de acceso fisico","13"),
]
AREA = {
 "1":("Policy on the security of network and information systems","Politica de seguridad de las redes y sistemas de informacion"),
 "2":("Risk management policy","Politica de gestion de riesgos"),
 "3":("Incident handling","Gestion de incidentes"),
 "4":("Business continuity and crisis management","Continuidad de negocio y gestion de crisis"),
 "5":("Supply chain security","Seguridad de la cadena de suministro"),
 "6":("Security in acquisition, development and maintenance","Seguridad en la adquisicion, desarrollo y mantenimiento"),
 "7":("Assessing the effectiveness of the measures","Evaluacion de la eficacia de las medidas"),
 "8":("Basic cyber hygiene and security training","Ciberhigiene basica y formacion en seguridad"),
 "9":("Cryptography","Criptografia"),
 "10":("Human resources security","Seguridad de los recursos humanos"),
 "11":("Access control","Control de acceso"),
 "12":("Asset management","Gestion de activos"),
 "13":("Environmental and physical security","Seguridad fisica y ambiental"),
}
items = []
for i,en,es in ART21:
    items.append({"id":i,"layer":"directive","family":"art21",
                  "family_title":{"en":"Directive (EU) 2022/2555, Article 21(2)","es":"Directiva (UE) 2022/2555, articulo 21.2"},
                  "title":{"en":en,"es":es}})
for i,en,es in GOV:
    items.append({"id":f"art.{i}","layer":"directive","family":"articles",
                  "family_title":{"en":"Directive (EU) 2022/2555, other obligations","es":"Directiva (UE) 2022/2555, otras obligaciones"},
                  "title":{"en":en,"es":es}})
for i,en,es,area in CIR:
    items.append({"id":f"cir.{i}","layer":"implementing_regulation","family":area,
                  "family_title":{"en":AREA[area][0],"es":AREA[area][1]},
                  "title":{"en":en,"es":es}})
pathlib.Path("crossmap/data/controls_nis2.json").write_text(
    json.dumps({"framework":"NIS2","items":items}, ensure_ascii=False, indent=1))
print("NIS2:", len(items), "elementos |", len(ART21),"letras art.21.2 +",len(GOV),"articulos +",len(CIR),"requisitos CIR")
