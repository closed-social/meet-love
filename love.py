from flask import Flask, request, render_template, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler 

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///meetLove.db'
app.config['SCHEDULER_API_ENABLED'] = True
app.config['JOBS'] = [{
    'id': 'bot',
    'func': 'love:query',
    'trigger': 'interval',
    'seconds': 15
    }
]

db = SQLAlchemy(app)
scheduler = APScheduler()

ip_count = {}


def query():
    print('okkk')

class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    s  = db.Column(db.String(64))
    name_hash = db.Column(db.String(64))
    full_hash = db.Column(db.String(64))
    ip = db.Column(db.String(32))
    cs_username = db.Column(db.String(32))

    def __init__(self, s, name_hash, full_hash, ip):
        self.s = s
        self.name_hash = name_hash
        self.full_hash = full_hash
        self.ip = ip
        self.cs_username = ''

    def __repr__(self):
        return '%s[%s]<%s>'%(self.s, self.cs_username, self.ip)

@app.route('/js/<path:path>')
def send_js(path):
    return send_from_directory('static/js', path)

@app.route('/meetLove/')
def root():
    return app.send_static_file('love.html')

@app.route('/meetLove/api/', methods=['POST'])
def api():
    s = request.form.get('s')
    if( not s or len(s) < 8 or len(s) > 60):
        return '暗号格式不正确', 422

    ha = request.form.get('hash')
    if( not ha or len(ha) != 64 * 2):
        return '哈希格式不正确', 422

    ip = request.remote_addr
    if ip in ip_count:
        ip_count[ip] += 1
        if ip_count[ip] > 50:
            return '该ip告白次数太多', 403
    else:
        ip_count[ip] = 1

    if Record.query.filter_by(s=s).count():
        return '暗号重复', 422
    if Record.query.filter_by(name_hash=ha[64:]).count():
        return '一个名字只能告白一次,重名/哈希冲突请联系主办方', 422
    rec = Record(s, ha[64:], ha[:64], ip)
    rec = Record(s, ha[64:], ha[:64], ip)
    db.session.add(rec)
    db.session.commit()

    return 'done'


if __name__ == '__main__':
    scheduler.init_app(app)
    scheduler.start()
    app.run(debug=True)
