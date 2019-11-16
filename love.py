from flask import Flask, request, render_template, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler 
from mastodon import Mastodon
import html2text

BOT_NAME = '@wall_bot'
DOMAIN   = 'thu.closed.social'

token = open('token.secret','r').read().strip('\n')
th = Mastodon(
    access_token = token,
    api_base_url = 'https://' + DOMAIN
)

th.lid = 103145541052439620

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

ip_count = {}

h2t = html2text.HTML2Text()
h2t.ignore_links = True

def PM(msg, name):
    th.status_post(msg + '\n@' + name, visibility='direct')


def query():
    r = th.conversations(min_id=th.lid)
    #print(th.lid)
    if r:
        th.lid = r[0].last_status.id
    for conv in r[::-1]:
        if conv.unread:
            th.conversations_read(conv.id)

            name = conv.last_status.account.acct
            text = conv.last_status.content
            pt = h2t.handle(text).lstrip()
            s = pt.replace(BOT_NAME+' ','').replace('\n','')

            #print(s)

            r = Record.query.filter_by(cs_username=name).first()
            if r:
                PM('只能绑定一个暗号哦，你已经绑定了<%s>' % r.s, name)
                continue

            if len(s) > 100:
                PM('什么玩意儿', name)
                continue

            r = Record.query.filter_by(s=s).first()
            if not r:
                PM('没有找到暗号<%s>呢' % s, name)
                continue
            
            if r.cs_username:
                PM('暗号<%s>的绑定者已变更，你们在搞什么 = =' % s, name+' @'+r.cs_username)

            r.cs_username = name
            db.session.commit()

            rs =  Record.query.filter_by(full_hash=r.full_hash).all()
            if( len(rs) == 2 and rs[0].cs_username and rs[1].cs_username):
                PM('恭喜你们！祝幸福！', rs[0].cs_username + ' @' + rs[1].cs_username)
            else:
                PM('已成功绑定<%s>' % s, name)


db = SQLAlchemy(app)
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()


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
@app.route('/img/<path:path>')
def send_img(path):
    return send_from_directory('static/img', path)

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
        return '一个名字只能告白一次,\n重名/哈希冲突请联系主办方', 422
    
    ta = Record.query.filter_by(full_hash=ha[:64]).first()
    
    rec = Record(s, ha[64:], ha[:64], ip)
    rec = Record(s, ha[64:], ha[:64], ip)
    db.session.add(rec)
    db.session.commit()

    if not ta:
        return ''
    else:
        if ta.cs_username:
            PM('叮~ TA也给你表白啦! https://closed.social/meetLove/result/', ta.cs_username)
        return 'y' if ta.cs_username else 'n'

@app.route('/meetLove/result/')
def result():
    rs = Record.query.all()
    rs.sort(key=lambda r:r.full_hash)

    lovers = [(rs[i].s[:-4]+'****', rs[i+1].s[:-4]+'****') for i in range(len(rs)-1) if rs[i].full_hash == rs[i+1].full_hash]

    return render_template('result.html', lovers=lovers)

if __name__ == '__main__':
    app.run()
