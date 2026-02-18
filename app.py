import os
from flask import Flask, render_template, request
import pandas as pd
import numpy as np
import smtplib
from email.message import EmailMessage

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def calculate_topsis(data, weights, impacts):

    weights = np.array(weights, dtype=float)
    matrix = data.iloc[:, 1:].values

    norm = matrix / np.sqrt((matrix ** 2).sum(axis=0))
    weighted = norm * weights

    ideal_best = []
    ideal_worst = []

    for i in range(len(impacts)):
        if impacts[i] == '+':
            ideal_best.append(max(weighted[:, i]))
            ideal_worst.append(min(weighted[:, i]))
        else:
            ideal_best.append(min(weighted[:, i]))
            ideal_worst.append(max(weighted[:, i]))

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    dist_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    score = dist_worst / (dist_best + dist_worst)

    data['Topsis Score'] = score
    data['Rank'] = score.argsort()[::-1] + 1

    return data


def send_email(receiver_email, file_path):

    sender_email = os.environ.get("EMAIL_USER")
    sender_password = os.environ.get("EMAIL_PASS")

    msg = EmailMessage()
    msg['Subject'] = "TOPSIS Result"
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg.set_content("Please find attached TOPSIS result file.")

    with open(file_path, 'rb') as f:
        file_data = f.read()
        file_name = os.path.basename(file_path)

    msg.add_attachment(file_data, maintype='application',
                       subtype='octet-stream', filename=file_name)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(sender_email, sender_password)
        smtp.send_message(msg)


@app.route('/', methods=['GET', 'POST'])
def index():

    if request.method == 'POST':

        file = request.files['file']
        weights = request.form['weights'].split(',')
        impacts = request.form['impacts'].split(',')
        email = request.form['email']

        if len(weights) != len(impacts):
            return "Weights and Impacts must match."

        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        data = pd.read_csv(filepath)

        result = calculate_topsis(data, weights, impacts)

        output_path = os.path.join(UPLOAD_FOLDER, "result.csv")
        result.to_csv(output_path, index=False)

        send_email(email, output_path)

        return "Result sent to your email successfully!"

    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)