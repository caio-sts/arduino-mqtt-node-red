from flask import Flask, render_template, redirect,url_for, request, jsonify, send_file, Response
from datetime import datetime
import pandas as pd
import json
import pytz
import plotly
import os
from notify import notify


app = Flask(__name__)

global datasJSON
global tempJSON
global umidJSON

deadTemp = 30
deadHumid = 40
counterAlert = 0
notifOpenedDrawer = False

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != 'admin' or request.form['password'] != 'admin':
            error = 'Credenciais inválidas. Por favor, tente novamente ou contate o administrador.'
        else:
            return redirect('https://iot.darkissons.repl.co/dashboard')
    return render_template('login.html', error=error)

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
  global notifOpenedDrawer
  if request.method == 'POST':
    data = json.loads(request.data)
    if data['Distance'] <= 50 or data['Light'] <= 650:
      with open('Cliente.json') as f:
            dados = json.load(f)
            dados["drawer"] = "aberta"
            json.dump(dados, open('Cliente.json', "w"), indent=4)
      if notifOpenedDrawer == False:
        notify('A gaveta foi aberta.')
        notifOpenedDrawer = True
    else: 
      with open('Cliente.json', "r+") as f:
            dados = json.load(f)
            dados["drawer"] = "fechada"
            json.dump(dados, open('Cliente.json', "w"), indent=4)
      if notifOpenedDrawer == True:
        notify('A gaveta foi fechada.')
        notifOpenedDrawer = False
    
    df = pd.read_csv('dados.csv', sep = ',', encoding = 'utf-8')
    if data['Temperatura'] is None or data['Temperature'] == "":
      data['Temperature'] = df.iloc[-10:,1].mean()
    if data['Humidity'] is None or data['Humidity'] == "":
      data['Humidity'] = df.iloc[-10:,2].mean()

    if data['Temperature'] is not None and data['Humidity'] is not None:
      dadosTempUmid = [ str(float(data['Temperature'])), str(float(data['Humidity'])-40) ]
      with open("dados.csv", "a+") as f:
        data_hora_atual = datetime.now(pytz.timezone('America/Sao_Paulo'))
        data_hora_atual = data_hora_atual.strftime('%d/%m/%Y %H:%M:%S')
        f.write(data_hora_atual+', '+', '.join(dadosTempUmid)+"\n")
        global counterAlert
        if data['Temperature'] > deadTemp or data['Humidity'] > deadHumid:
          counterAlert += 1
        if counterAlert >= 5:
          notify('Por favor, verifique a situação do seu smart drawer. Detectamos um alerta nos sensores.')
        if data['Temperature'] <= deadTemp and data['Humidity'] <= deadHumid:
          counterAlert = 0
          
      if os.path.getsize('dados.csv') + 30 > 10000: # adição 28, header 39
        df = pd.read_csv('dados.csv', sep = ',', encoding = 'utf-8')
        df.drop(df.index[list(range(1,100))], inplace=True)
        df.to_csv('dados.csv', index=False)

    
  with open("Cliente.json", "r+") as f:
    dadosClient = json.load(f)
    
  nome = dadosClient["Nome"]
  telefone = dadosClient["Telefone"]
  telefone = telefone[:2] + " " + telefone[2:7] + "-" + telefone[7:] 
  drawer = dadosClient["drawer"]

  df = pd.read_csv('dados.csv', sep = ',', encoding = 'utf-8')
  datasJSON = json.dumps(df.iloc[-10:,0], cls=plotly.utils.PlotlyJSONEncoder)
  tempsJSON = json.dumps(df.iloc[-10:,1], cls=plotly.utils.PlotlyJSONEncoder)
  umidsJSON = json.dumps(df.iloc[-10:,2], cls=plotly.utils.PlotlyJSONEncoder)

  return render_template('dashboard.html', datasJSON=datasJSON, tempJSON=tempsJSON, umidJSON=umidsJSON, nome=nome, telefone=telefone, drawerState=drawer)

@app.route('/data', methods=['GET'])
def getData():
  df = pd.read_csv('dados.csv', sep = ',', encoding = 'utf-8')
  datasJSON = json.dumps(df.iloc[-10:,0], cls=plotly.utils.PlotlyJSONEncoder)
  tempsJSON = json.dumps(df.iloc[-10:,1], cls=plotly.utils.PlotlyJSONEncoder)
  umidsJSON = json.dumps(df.iloc[-10:,2], cls=plotly.utils.PlotlyJSONEncoder)

  with open("Cliente.json", "r+") as f:
    dados = json.load(f)
  
  return jsonify(datasJSON, tempsJSON, umidsJSON, dados["drawer"])

@app.route("/getReport")
def getReport():
  return send_file(
        'dados.csv',
        mimetype="text/csv",
        as_attachment=True,
        download_name="relatorio.csv"
          )

if __name__=="__main__":
  app.run(host="0.0.0.0", debug=False)
