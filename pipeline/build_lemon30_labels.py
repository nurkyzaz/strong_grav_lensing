import csv

EEL = {  # jname: (ra, dec, theta_E)
    "J0837": (129.25505, 8.02165, 0.56), "J0901": (135.33854, 20.46123, 0.67),
    "J1125": (171.30788, 30.96822, 0.86), "J1144": (176.11833, 15.67760, 0.68),
    "J1218": (184.52775, 56.80142, 0.68), "J1323": (200.99612, 39.77590, 0.31),
    "J1347": (206.77067, -1.01766, 0.43), "J1446": (221.62581, 38.94899, 0.41),
    "J1605": (241.34706, 38.19833, 0.64), "J1606": (241.52956, 22.58651, 0.52),
    "J1619": (244.80262, 20.40777, 0.50), "J2228": (337.17009, -0.30467, 0.60),
}
COSMOS = {
    "0012+2015": (150.0525, 2.3375, 0.67), "0038+4133": (150.159167, 2.6925, 0.73),
    "0047+5023": (150.198333, 1.839722, 1.41), "0211+1139": (150.546667, 2.194167, 3.14),
    "5921+0638": (149.840417, 2.110556, 0.70),
}
ACS = {  # coord: (ra, dec, arc_radius)
    "001423.02-302109.8": (3.595917, -30.352722, 1.52),
    "001426.26-302255.9": (3.609417, -30.382194, 1.00),
    "011018.22+193819.5": (17.575917, 19.638750, 3.10),
    "084710.65+344826.4": (131.794375, 34.807333, 1.98),
    "095139.44+684731.2": (147.914333, 68.792000, 0.77),
    "103751.40-124327.5": (159.464167, -12.724306, 1.48),
    "122332.64-123940.3": (185.886000, -12.661194, 0.36),
    "130042.73+280523.3": (195.178042, 28.089806, 1.08),
    "140237.11+542716.4": (210.654625, 54.454556, 1.85),
    "140339.94+541633.3": (210.916417, 54.275917, 0.90),
    "171817.43+593146.4": (259.572625, 59.529556, 2.35),
    "221501.12-135822.9": (333.754667, -13.973028, 0.82),
    "235130.60-261459.7": (357.877500, -26.249917, 3.32),
}

rows = []
for j, (ra, dec, t) in EEL.items():
    rows.append(dict(name="EEL_" + j, ra_deg=ra, dec_deg=dec, theta_E_pub=t,
                     q_pub=0.0, survey="LEMONEEL", src_table="Oldham+2017/OAF2017"))
for c, (ra, dec, t) in COSMOS.items():
    rows.append(dict(name="COSMOS_" + c, ra_deg=ra, dec_deg=dec, theta_E_pub=t,
                     q_pub=0.0, survey="LEMONCOSMOS", src_table="Faure+2008"))
for c, (ra, dec, arc) in ACS.items():
    rows.append(dict(name="ACS_" + c.replace(".", "p").replace("+", "P").replace("-", "M"),
                     ra_deg=ra, dec_deg=dec, theta_E_pub=0.0,  # NO real theta_E — arc radius substitute
                     q_pub=0.0, survey="LEMONACS", src_table="Pawase+2014_arcrad%.2f" % arc))

with open("lemon30_labels.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["name", "ra_deg", "dec_deg", "theta_E_pub", "q_pub", "survey", "src_table"])
    w.writeheader()
    for r in rows:
        w.writerow(r)
print("wrote lemon30_labels.csv: %d rows (%d EEL, %d COSMOS, %d ACS)"
      % (len(rows), len(EEL), len(COSMOS), len(ACS)))

# pilot = 1 per subsample
pilot = [rows[0], rows[len(EEL)], rows[len(EEL) + len(COSMOS)]]
with open("lemon_pilot3_labels.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["name", "ra_deg", "dec_deg", "theta_E_pub", "q_pub", "survey", "src_table"])
    w.writeheader()
    for r in pilot:
        w.writerow(r)
print("wrote lemon_pilot3_labels.csv:", [r["name"] for r in pilot])
