from flask import Flask, request, render_template, send_from_directory

app = Flask(__name__)


@app.route('/js/<path:path>')
def send_js(path):
    return send_from_directory('static/js', path)

@app.route('/meetLove/')
def root():
    return app.send_static_file('love.html')

@app.route('/meetLove/api/', methods=['POST'])
def api():
    s = request.form.get('s')
    if( not s or len(s) < 8):
        return '暗号格式不正确', 422

    ha = request.form.get('hash')
    if( not ha or len(ha) != 64 * 2):
        return '哈希格式不正确', 422

    #do sothing
    ip = request.remote_addr

    return ip


if __name__ == '__main__':
    app.run(debug=True)
