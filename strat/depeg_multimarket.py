# TODO: Találd ki, hogy lehet ebbe bevonni valakit, pontosan mi okozza azt, hogy tudsz dolgozni, azt hogy tudod megoldani.

# Tehát az a konfliktus, hogy mennyire dolgozzunk előre, mennyire legyünk felkészülve.
# Semennyire, ha kell majd átírjuk.
# A limit orderek miből állnánk?
#  - A marketben: A wrapperbe egy limit orderes lehetőségből, egy orders változóból,
#    !! A piaci árnál csak nagyobbat hagyva, errort dobva ha szar volt a strat!
# 	(Meg nagyon találd ki, hogy biztos legyen, meg akár az apitól is kaphasson
# 	szar adatot, működjön úgy is (legyen előre megadott min-max (pl. 0.93-1.07)))
#  - A stratban: Ide kell a logic
#		Amikor eléri a thresholdot, rakjon be egy ordert, kb. ennyi, nyilván figyelnie kell, elviszik-e és cancellelni.
