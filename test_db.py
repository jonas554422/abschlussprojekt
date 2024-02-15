from tinydb import TinyDB, Query

db_path = 'verfuegbare_raeume_db.json'
db = TinyDB(db_path)
print(db.all())