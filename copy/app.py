from flask import Flask, request, render_template, redirect, session
from flask_sqlalchemy import SQLAlchemy
import bcrypt
import pickle

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
app.secret_key = 'secret_key'
model = pickle.load(open("RFmodel.pkl", "rb"))


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

    def __init__(self, email, password, name):
        self.name = name
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # handle request
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        new_user = User(name=name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/login')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session['email'] = user.email
            return redirect('/dashboard')
        else:
            return render_template('login.html', error='Invalid user')

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'email' in session:
        user = User.query.filter_by(email=session['email']).first()
        return render_template('dashboard.html', user=user)
    return redirect('/login')

@app.route('/croppred')
def croppred():
    return render_template('croppred.html')

@app.route('/crop-predict', methods=["GET", "POST"])
def crop_prediction():
    if request.method == "POST":
        # Nitrogen
        nitrogen = float(request.form["nitrogen"])
        # Phosphorus
        phosphorus = float(request.form["phosphorus"])
        # Potassium
        potassium = float(request.form["potassium"])
        # Temperature
        temperature = float(request.form["temperature"])
        # Humidity Level
        humidity = float(request.form["humidity"])
        # PH level
        phLevel = float(request.form["ph"])
        # Rainfall
        rainfall = float(request.form["rainfall"])

        # Making predictions from the values:

        # predictions = model.predict([[nitrogen, phosphorus, potassium, temperature, humidity, phLevel, rainfall]])
        # output = predictions[0:11]
        # finalOutput = output.capitalize()
        # cropStatement= finalOutput+" should be grown"
        predictions_proba = model.predict_proba([[nitrogen, phosphorus, potassium, temperature, humidity, phLevel, rainfall]])
        classes = model.classes_
        probabilities = predictions_proba[0]
        # Combine the classes and probabilities into a list of tuples
        results = list(zip(classes, probabilities))
        # Sort the results by the probability in descending order
        sorted_results = sorted(results, key=lambda x: x[1], reverse=True)
        # Get the top 10 results
        top_results = sorted_results[:10]
        # Create a statement for the top 10 crops
        top_crop_statement = "The top 10 predicted crops are: " + ", ".join([crop.capitalize() for crop, _ in top_results])

        # if (output == "rice" or output == "blackgram" or output == "pomegranate" or output == "papaya"
        #         or output == "cotton" or output == "orange" or output == "coffee" or output == "chickpea"
        #         or output == "mothbeans" or output == "pigeonpeas" or output == "jute" or output == "mungbeans"
        #         or output == "lentil" or output == "maize" or output == "apple"):
        #     cropStatement = finalOutput + " should be harvested. It's a Kharif crop, so it must be sown at the beginning of the rainy season e.g between April and May."

        # elif (output == "muskmelon" or output == "kidneybeans" or output == "coconut" or output == "grapes" or output == "banana"):
        #     cropStatement = finalOutput + " should be harvested. It's a Rabi crop, so it must be sown at the end of monsoon and beginning of winter season e.g between September and October."

        # elif (output == "watermelon"):
        #     cropStatement = finalOutput + " should be harvested. It's a Zaid Crop, so it must be sown between the Kharif and rabi season i.e between March and June."

        # elif (output == "mango"):
        #     cropStatement = finalOutput + " should be harvested. It's a cash crop and also perennial. So you can grow it anytime."


        # Assuming you have a dictionary mapping crop names to image paths
        crop_images = {
            "rice": "../static/rice.jpg",
            "mango": "../static/mango.jpg",
            "chickpea": "../static/chickpea.jpg",
            "orange": "../static/orange.jpg",
            "pomegranate": "../static/pomegranate.jpg",
            # Add more crop names and image paths as needed
        }
        # Create a list of image paths for the predicted crops
        predicted_crops = [crop_images.get(crop.lower(), "../static/default.jpg") for crop, _ in top_results]

        return render_template('crop_result.html', prediction_text=top_crop_statement, crop_images=predicted_crops)


    # Return a default response if the request method is not "POST"
    return "Invalid request"


@app.route('/logout')
def logout():
    session.pop('email', None)
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
