import copy
import os
import glob
import secrets
import math
import base64
from io import BytesIO
from PIL import Image, ImageDraw
from flask import render_template, url_for, flash, redirect, request
from upark import app, db, bcrypt, login_manager
from upark.forms import UploadPic, RegistrationForm, LoginForm, EditProfile, UpdateAccountForm, AddZone
from flask_login import login_user, current_user, logout_user, login_required

# Class to define an account for a customer
class Customer:
    def __init__(self, username):
        self.username = username
        customer = db.Customers.find_one({"Username": username})
        self.email = customer['Email']
        self.image_file = customer['Image_file']
    @staticmethod
    def is_authenticated():
        return True

    @staticmethod
    def is_active():
        return True

    @staticmethod
    def is_anonymous():
        return False

    def get_id(self):
        return self.username

    @login_manager.user_loader
    def load_user(username):
        customer = db.Customers.find_one({"Username": username})
        if not customer:
            return None
        return Customer(username=customer['Username'])


    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        form = LoginForm()
        if form.validate_on_submit():
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            user = db.Customers.find_one({"Email": form.email.data})
            if user and bcrypt.check_password_hash(user['Password'], form.password.data):
                flash("You have been logged in successfully", 'success')
                user_obj = Customer(username=user['Username'])
                login_user(user_obj, remember=form.remember.data)
                next_page = request.args.get('next')
                if not next_page:
                    next_page = url_for('dashboard')
                return redirect(next_page)
            else:
                flash("Invalid username or password", "danger")
        return render_template('login.html', form=form)

    @app.route('/logout')
    def logout():
        logout_user()
        return redirect(url_for('login'))

@app.route("/registeration", methods=['GET', 'POST'])
def registeration():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = RegistrationForm()
    if (form.validate_on_submit()):
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        customer = {'Email': f'{form.email.data}',
                'Username': f'{form.username.data}',
                'Password': f'{hashed_password}',
                'Image_file': 'default.png'
                }
        db.Customers.insert_one(customer)
        flash("An account has been created for you, you can now login", 'success')
        return redirect(url_for('login'))
    return render_template('registeration.html', form=form)


# Structure of a clusters collection
''' 
Clusters = 
{
   {"_id":{"$oid":"6259c2bb35f73cb07342e8c9"},
    "name":"A01",
    "parking":"Dhahran Mall",
    "capacity":{"$numberLong":"66"},
    "occupancy":{"$numberLong":"202"},
    "type":"entrance",
    "parkedPlates":["1234XYZ","5198vxJ","7035TB","7035TBD","8877XRJ","8877xRJ","7035TBO","1436uLD","1436ULD","1436u","1436uLD8","5198vx","A","BXD","}|JRD","8867RXD|","7131","4385 NUB","5974HKD","2854GKB","9436DAR","9454GJD6","B","2715GLD","C","GJD","RAD","9227uKD","6361SUA","1908UUA","1908uuA","3675HJJ","7656DHO","4063vLJ","6656HJD","sa","GED","2269 RKD","3675 HJJ","2221ULD","9227UKD","4063VLJ","SA","6487ARJTSAY","8867RXDIY05","71317131","5198VXJS","1616GTB1616GTB","37178554616GTB","7173504616GTB","2007JAAYEII","6115KADT10UI5","4616GTB","2007JAA","1547BXD","6115KAD","7863JRD","8867RXD","2229NDB","8789HJO","8789HJD","3493SSD","8455HEO","R30988ZOA","3098RZD","HINDEHINDE","HYGEHYGE","HY9AC","6666","SESE","6601AR6","INDIND","8789HYHQAGD","3098RZD6","8789HJB","3493SSDA","3493SSDS","3493SSPA","AG8789HJB","8789HUD","3098RZDB","3493SSB","RERTRERT","8789HJ6","3493SS","8789HB","S5198VXJ","Z616DTALA","L616GTB","51985198","5198VXJ","1328UJD6","1328UJD","L37NND","8459LZJ","1328UJDA","46166TB","1328UJB","8L59LZJ","8459GZ","L137NND","8789 HJo"],
    "priority":{"$numberLong":"10"},
    "assignedCluster":"A22"
    } 
}
# Structure of parkings collection
parkings = 
{
    {"_id":{"$oid":"6259c10935f73cb07342e8c8"},
    "name":"Dhahran Mall",
    "capacity":{"$numberLong":"2000"},
    "occupancy":{"$numberLong":"1300"},
    "authRequired":false,
    "fees":true,
    "amount":"5"}
}
'''
@app.route("/")
@app.route("/home")
@app.route("/dashboard", methods=['GET', 'POST'])
@login_required
def dashboard():
    Parking_name = db.parkings.find_one({'owner': current_user.username})
    if Parking_name:
        Parking_name = Parking_name['name']
        zones = list(db.clusters.find({"owner": current_user.username}))
        zone_names = []
        for zone in zones:
            zone_names.append(zone['name'])
        print(zone_names)
        my_chart = db.chart.find_one({"parking": Parking_name}, {"table": 1, "entrance":1, "capacity":1, "zone":1, "_id":0})
        #chart for the zone 
        zone2 = None
        zone = None
        entrance = None
        capacity = None
        table = None
        if my_chart:
            zone2 = my_chart['zone']
            zone = combine(zone_names,zone2)

            entrance = my_chart['entrance']
            capacity = my_chart['capacity']
            table = my_chart['table']

        if request.method == 'POST':
            date = request.form['date']
            print(date)
            return redirect(url_for("dashboard")+"#predict")
        return render_template('dashboard.html', parking = True, zone= zone, entrance=entrance, capacity=capacity, table= table)
    else:
        return render_template('dashboard.html', parking = False)

def combine(list1,list2):
    out_list = [(i,x) for i,x in zip(list1,list2)]
    return out_list

@app.route("/help", methods=['GET', 'POST'])
@login_required
def help():

    return render_template('help.html')

@app.route("/authorized", methods=['GET', 'POST'])
@login_required
def authorized():
    Parking_name = db.parkings.find_one({'owner': current_user.username})
    if Parking_name:
        Parking_name = Parking_name['name']
        name = Parking_name.replace(" ","_")
        spath = app.config["UPLOAD_VIP"] + "/" + name

        if not os.path.exists(spath):
            os.makedirs(spath)

        if request.method == 'POST':
            # replace all the file 
            files = glob.glob(spath + "/*")
            for s in files:
                os.remove(s)

            # start the reading 
            f = request.files['vip_name']
            name = f.filename
            print(name)

            # if no file then do nothing
            if name =="":
                msg = "Old file deleted! you can not submit empty file "
                flash(msg, 'danger')
                return render_template('authorized.html', parking=True)
                
            # make sure the file is txt file 
            kind = name.rsplit(".",1)[1].lower()
            if kind == 'txt':
                # save the file
                f.save(os.path.join(spath, f.filename))
            else:
                msg = "The file must be a text file! "
                flash(msg, 'danger')
                return render_template('authorized.html', parking=True)

        # load the table for writing
        vip_list = [] 
        files = glob.glob(spath + "/*")
        for s in files:
            with open(s) as topo_file:
                vip_list = [plate.replace('\n', '') for plate in topo_file]
                print(vip_list)
                print("welcome") 
                    
        return render_template('authorized.html', parking=True, vip_list = vip_list )
    else:
        return render_template('authorized.html', parking = False)

@app.route("/analytics", methods=['GET', 'POST'])
@login_required
def analytics():
    Parking_name = db.parkings.find_one({'owner': current_user.username})
    if Parking_name:
        Parking_name = Parking_name['name'] 
        my_chart = db.chart.find_one({"parking": Parking_name}, {"last1h": 1, "last7d":1, "hour":1, "weekday":1, "_id":0})

        last1h = None
        last7d =None
        hour = None
        weekday = None
        if my_chart:
            last1h = my_chart['last1h']
            last7d = my_chart['last7d']
            hour = my_chart['hour']
            weekday = my_chart['weekday']
    
        val = []
        h = []
        vx = []
    
        if request.method == 'POST':
            date = request.form['date']
    
            x = datetime.datetime.strptime(date, '%d/%m/%Y')
            day = x.isoweekday()
            month = datetime.datetime.strptime(date, '%d/%m/%Y').month
    
            url = "https://upark22ocr.azurewebsites.net/availability"
            params = {"month":month, "day":day, "parking": Parking_name}
            r = requests.get(url = url, params = params)
    
            val = []
            h = []
            vx = []
            for index , x in enumerate(r.json()):
                h.append(index)
                vx.append("1")
                if x == 'mid':
                    val.append("rgb(255, 205, 86)")
                elif x =='high':
                    val.append("red")
                else:
                    val.append("green")
            print(val)
            print(h)
    
            
            return render_template('analytics.html', last1h=last1h, last7d=last7d,hour=hour , weekday=weekday, val=val , h=h, vx=vx, parking=True)


    
        return render_template('analytics.html', last1h=last1h, last7d=last7d,hour=hour , weekday=weekday, val=val , h=h, vx=vx, parking=True)
    else:
        return render_template('analytics.html', parking=False)

@app.route("/settings", methods=['GET', 'POST'])
def settings():
    fees ='' # read the value from the database
    if request.method == 'POST':
        if request.form.get('checked')=='on': # change the value in the database make the boolean true 
            fees = request.form['amount12']  # change the value in the database (make sure it is a number)
 
    return render_template('settings.html', fees=fees)

@app.route("/ads", methods=['GET', 'POST'])
@login_required
def ads():
    Parking_name = db.parkings.find_one({'owner': current_user.username})
    if Parking_name:
        Parking_name = Parking_name['name']
        name = Parking_name.replace(" ","_")
        spath = app.config['UPLOAD_PATH'] + "/" + name
        if not os.path.exists(spath):
            os.makedirs(spath)


        if request.method == 'POST':
            if request.form.get('checked') == "yes":
                print("YES HE WANT THE REPLACE")
                files = glob.glob(spath + "/*")
                for f in files:
                    os.remove(f)
            print("you are in img POST")
            for f in request.files.getlist('file_name'):
                name = f.filename
                if name =="":
                    continue
                kind = name.rsplit(".",1)[1].lower()
                if kind not in ['png', 'jpg', 'jpge']:
                    continue
                else:
                    #f = request.files['file_name']
                    #spath = app.config['UPLOAD_PATH'] + "/" +
                    gg = os.path.join(spath, f.filename)
                    print(gg) 
                    f.save(gg)
            image = list_imag_ads(spath)
            return render_template('ads.html', image= image, parking=True)
        image = list_imag_ads(spath)
        return render_template('ads.html', image= image, parking=True)
    else:
        return render_template('ads.html', parking=False)



def list_imag_ads(path):
    file_paths = []
    re_path = path.replace("upark","..")   
    for root, directories, files in os.walk(path):
        for filename in files:
            filepath = os.path.join(re_path, filename)
            filename = filename.rsplit(".",1)[0].lower()
            file_paths.append((filepath,filename))
    return file_paths  
    
@app.route("/profile", methods=['GET', 'POST'])
@login_required
def profile():
    form = EditProfile()
    if (form.validate_on_submit()):
        return redirect(url_for('edit_profile'))
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('profile.html', image_file=image_file, form=form, name='Abdullah', bio='Developer of the website', company='UPark', address='Dhahran')

@app.route("/edit_profile", methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = UpdateAccountForm()
    if (form.validate_on_submit()):
        db.Customers.update_one({"Username": f'{current_user.username}'}, {"$set": {"Email": form.email.data}})
        if form.picture.data:
            random_hex = secrets.token_hex(8)
            _, f_ext = os.path.splitext(form.picture.data.filename)
            picture_fn = random_hex + f_ext
            picture_path = os.path.join(app.root_path, 'static\profile_pics', picture_fn)            
            output_size = (125,125)
            i = Image.open(form.picture.data)
            i.thumbnail(output_size)
            i.save(picture_path)
            db.Customers.update_one({"Username": f'{current_user.username}'}, {"$set": {"Image_file": picture_fn}})
        db.Customers.update_one({"Username": f'{current_user.username}'}, {"$set": {"Username": form.username.data}})
        flash('Your account has been updated!', 'success')
        return redirect(url_for('profile'))
    elif (request.method=='GET'):
        form.username.data = db.Customers.find_one({"Username": current_user.username})['Username']
        form.email.data = db.Customers.find_one({"Username": current_user.username})['Email']

    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('edit_profile.html',
                           image_file=image_file, form=form)

'''
def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static\maps', picture_fn)
    
    i = Image.open(form_picture)
    i.save(picture_path)
    i2 = Image.open(form_picture)
    i2.save(os.path.join(app.root_path, 'static\img', picture_fn))
    f = open(os.path.join(app.root_path, 'static\img\layout.txt'), 'w')
    f.write(os.path.join(app.root_path, 'static\img', picture_fn))
    f.close()
    return picture_fn, picture_path'''

def save_image(img, description, collection):
    im = Image.open(img).convert('RGB')
    image_bytes = BytesIO()
    im.save(image_bytes, format='JPEG')
    image = {'data': image_bytes.getvalue(),
             'description': description,
             'owner': current_user.username}
    if(collection.find_one({'description': description, 'owner': current_user.username})):

        collection.update_one({'description': description,
                               'owner': current_user.username},
                                {'$set': image})
    else:
        collection.insert_one(image)
    return

def save_image2(im, description, collection):
    image_bytes = BytesIO()
    im.save(image_bytes, format='JPEG')
    image = {'data': image_bytes.getvalue(),
             'description': description,
             'owner': current_user.username}
    if(collection.find_one({'description': description, 'owner': current_user.username})):
        collection.update_one({'description': description,
                               'owner': current_user.username}, {'$set': image})
    else:
        collection.insert_one(image)
    return

def save_path(im, source, dest):
    image_bytes = BytesIO()
    im.save(image_bytes, format='JPEG')
    image = {'from': source,
             'to': dest,
             'path': image_bytes.getvalue(),
             'owner': current_user.username}
    db.staticPaths.insert_one(image)
    return

def get_image(description, collection):
    image = collection.find_one({"description":description})
    img_str = base64.b64encode(image['data'])
    img = BytesIO(image['data'])
    data_url = 'data:image/jpg;base64,' + img_str.decode()
    # img: can be opened using Pillow,
    # data_url: can be viewed in the browser
    return img, data_url

def get_path(source, dest):
    image = collection.find_one({"from":source,
                                 "to":dest})
    img_str = base64.b64encode(image['path'])
    data_url = 'data:image/jpg;base64,' + img_str.decode()
    return data_url


@app.route("/customization", methods=['GET', 'POST'])
@login_required
def customization():
    # If edited, cursor position will be stored, gate or slot or street will be added,
    # and finally, new image will be created with appropriate changes      
    form = UploadPic()
    if form.validate_on_submit():
        if form.picture.data:
            save_image(form.picture.data, 'original image', db.images)
            save_image(form.picture.data, 'being edited', db.images)
            _, data_url = get_image('original image', db.images)
            parking_name = form.parking_name.data
            db.parkings.insert_one({'name': parking_name,
                                    'capacity': 0,
                                    'occupancy':0,
                                    'authRequired': False,
                                    'fees': False,
                                    'amount':0,
                                    'gates': [],
                                    'slots': [],
                                    'intersections': [],
                                    'streets': [],
                                    'owner': current_user.username,
                                    'zones': []
                                    })
            return render_template('customization.html', form= form, pic=data_url)

    return render_template('customization.html', form= form, pic='' )

@app.route("/customization/add_gate", methods=['GET', 'POST']) 
@login_required
def add_gate():

    if (request.form.get('editor.x')):
        image, pic= get_image('being edited', db.images)
        img = Image.open(image)
        draw = ImageDraw.Draw(img)
        x = int(request.form.get('editor.x'))
        y = int(request.form.get('editor.y'))
        draw.rectangle(( (x - 4, y - 4),(x + 4, y + 4) ), fill="blue")
        save_image2(img, 'being edited', db.images)
        g = create_new_gate(x,y)
        db.parkings.update_one({'owner': current_user.username},
                               {'$push': {'gates': g}
                               })
        _, pic2 = get_image('being edited', db.images)
        return render_template('customization_add_gate.html', pic=pic2)
    elif(request.form.get('add_gate')):
        _, pic2 = get_image('being edited', db.images)
        return render_template('customization_add_gate.html', pic=pic2)
    return render_template('customization_add_gate.html')

@app.route("/customization/add_slot", methods=['GET', 'POST'])
@login_required
def add_slot():

    if (request.form.get('editor.x')):
        image, pic= get_image('being edited', db.images)
        img = Image.open(image)
        draw = ImageDraw.Draw(img)
        x = int(request.form.get('editor.x'))
        y = int(request.form.get('editor.y'))
        draw.rectangle(( (x - 4, y - 4),(x + 4, y + 4) ), fill="red")
        save_image2(img, 'being edited', db.images)
        s = create_new_Slot(x,y)
        db.parkings.update_one({'owner': current_user.username},
                               {'$push': {'slots': s}
                               })
        
        _, pic2 = get_image('being edited', db.images)
        return render_template('customization_add_slot.html', pic=pic2)
    elif(request.form.get('add_slot')):
        _, pic2 = get_image('being edited', db.images)
        return render_template('customization_add_slot.html', pic=pic2)
    return render_template('customization_add_slot.html')

@app.route("/customization/add_first_street", methods=['GET', 'POST'])
@login_required
def add_first_street():

    if(request.form.get('add_street')):
        _, pic2 = get_image('being edited', db.images)
        return render_template('customization_add_first_street.html', pic=pic2)
    return render_template('customization_add_street.html')

@app.route("/customization/add_first_street2", methods=['GET', 'POST'])
@login_required
def add_first_street2():

    if (request.form.get('editor.x')):
        x = int(request.form.get('editor.x'))
        y = int(request.form.get('editor.y'))
        _, pic2 = get_image('being edited', db.images)
        return render_template('customization_add_first_street2.html', pic=pic2, x=x, y=y )
    
    return render_template('customization_add_first_street2.html')


@app.route("/customization/add_street", methods=['GET', 'POST'])
@login_required
def add_street():

    if (request.form.get('editor.x')):
        x1 = int(request.form.get('editor.x'))
        y1 = int(request.form.get('editor.y'))
        x2 = int(request.form.get('x2'))
        y2 = int(request.form.get('y2'))
        image, pic = get_image('being edited', db.images)
        s = create_new_street(x1, y1, x2, y2)
        #load the intersection from temp file
        intersection2 = db.temp.find_one({'owner': current_user.username})['temp']
        db.temp.delete_one({'owner': current_user.username})
        #append the newly created street to the intersection
        intersection2['connected streets'].append(s)
        intersections = db.parkings.find_one({'owner': current_user.username})['intersections']
        #append the intersection to the list of intersections
        intersections.append(intersection2)
        db.parkings.update_one({'owner': current_user.username},
                               {'$set': {'intersections': intersections}
                               })
        img = Image.open(image)
        draw = ImageDraw.Draw(img)

        # if the second click is on existing intersection
        intersections2 = db.parkings.find_one({'owner': current_user.username})['intersections']
        correct = False
        for i in intersections2:
            distance = find_distance_between_points(x1, y1, i['position'][0], i['position'][1])
            if (distance <= 5):
                i['connected streets'].append(s)
                db.parkings.update_one({'owner': current_user.username},
                                       {'$set': {'intersections': intersections2}
                                       })
                correct = True
                break
        # if the second click is on existing street: create intersection, append 2 streets, append it to the list of intersections
        # To do: if in middle, break the street to two, append the three streets to the new intersection, update streets file
        if (correct == False):
            streets = db.parkings.find_one({'owner': current_user.username})['streets']
            for j in streets:
                distance2 = find_distance(x1, y1, j)
                if(distance2 <= 5):
                    intersection = create_new_intersection(x1, y1)
                    intersection['connected streets'].append(s) 
                    if (find_distance_between_points(x1, y1, j['endpoints'][0], j['endpoints'][1]) > 12 and find_distance_between_points(x1, y1, j['endpoints'][2], j['endpoints'][3]) > 12):
                        # in the middle of the street
                        seg1 = create_new_street(x1, y1, j['endpoints'][0], j['endpoints'][1])
                        seg2 = create_new_street(x1, y1, j['endpoints'][2], j['endpoints'][3])
                        streets.remove(j)
                        streets.append(seg1)
                        streets.append(seg2)
                        intersection['connected streets'].append(seg1)
                        intersection['connected streets'].append(seg2)
                        db.parkings.update_one({'owner': current_user.username},
                               {'$set': {'streets': streets}
                               })
                    else:
                        intersection['connected streets'].append(j)

                    intersections3 = db.parkings.find_one({'owner': current_user.username})['intersections']
                    intersections3.append(intersection)
                    db.parkings.update_one({'owner': current_user.username},
                               {'$set': {'intersections': intersections3}
                               })

                    img = Image.open(image)
                    draw = ImageDraw.Draw(img)
                    draw.rectangle(( (x1 - 4, y1 - 4),(x1 + 4, y1 + 4) ), fill="red")
                    save_image2(img, 'being edited', db.images)
                    break

        draw.line(( (x1, y1),(x2, y2) ), fill="orange", width=3)
        save_image2(img, 'being edited', db.images)
        
        #append the newly created street to the list of the streets
        db.parkings.update_one({'owner': current_user.username},
                               {'$push': {'streets': s}} )
        _, pic2 = get_image('being edited', db.images)
        return render_template('customization_add_street.html', pic=pic2 )

    elif (request.form.get('editor_first.x')):
        x1 = int(request.form.get('editor_first.x'))
        y1 = int(request.form.get('editor_first.y'))
        x2 = int(request.form.get('x2'))
        y2 = int(request.form.get('y2'))
        image, pic = get_image('being edited', db.images)

        img = Image.open(image)
        draw = ImageDraw.Draw(img)
        draw.line(( (x1, y1),(x2, y2) ), fill="orange", width=3)
        save_image2(img, 'being edited', db.images)

        s1 = create_new_street(x1, y1, x2, y2)
        db.parkings.update_one({'owner': current_user.username},
                               {'$push': {'streets': s1}
                               })        
        _, pic2 = get_image('being edited', db.images)
        return render_template('customization_add_street.html', pic=pic2 )
    
    return render_template('customization_add_street.html')

@app.route("/customization/add_street2", methods=['GET', 'POST'])
@login_required
def add_street2():

    if (request.form.get('editor.x')):
        
        x = int(request.form.get('editor.x'))
        y = int(request.form.get('editor.y'))
        image, pic= get_image('being edited', db.images)

        #first click is on an existing intersection
        intersections = db.parkings.find_one({'owner': current_user.username})['intersections']
        correct = False
        for i in intersections:
            distance = find_distance_between_points(x, y, i['position'][0], i['position'][1])
            if (distance <= 5):
                db.temp.insert_one({'owner': current_user.username,
                                    'temp': i})
                correct = True
                break
        if(correct):
            return render_template('customization_add_street2.html', pic=pic, x=x, y=y)

        # first click is on an existing street
        # To do: if in middle, break strt to two, append them to the new intersection, update streets file
        streets = db.parkings.find_one({'owner': current_user.username})['streets']
        for strt in streets:
            distance = find_distance(x, y, strt)
            if (distance <= 5):
                new_intersection = create_new_intersection(x, y)
                if (find_distance_between_points(x, y, strt['endpoints'][0], strt['endpoints'][1]) > 12 and find_distance_between_points(x, y, strt['endpoints'][2], strt['endpoints'][3]) > 12):
                    # in the middle of the street
                    seg1 = create_new_street(x, y, strt['endpoints'][0], strt['endpoints'][1])
                    seg2 = create_new_street(x, y, strt['endpoints'][2], strt['endpoints'][3])
                    streets.remove(strt)
                    streets.append(seg1)
                    streets.append(seg2)
                    new_intersection['connected streets'].append(seg1)
                    new_intersection['connected streets'].append(seg2)
                    db.parkings.update_one({'owner': current_user.username},
                                            {'$set': {'streets' : streets}}
                                            )
                else:
                    new_intersection['connected streets'].append(strt)
                ############
                db.temp.insert_one({'owner': current_user.username,
                                    'temp': new_intersection})
                ###############
                correct = True
                img = Image.open(image)
                draw = ImageDraw.Draw(img)
                draw.rectangle(( (x - 4, y - 4),(x + 4, y + 4) ), fill="red")
                save_image2(img, 'being edited', db.images)
                break
        
        _, pic2 = get_image('being edited', db.images)
        if(correct):
            return render_template('customization_add_street2.html', pic=pic2, x=x, y=y)
        else:
            flash('New streets must be connected to previous streets. Try again', 'danger')
            return render_template('customization_add_street.html', pic=pic2, x=x, y=y)
 
    return render_template('customization_add_street2.html')

@app.route("/customization/segmentation1", methods=['GET', 'POST'])
@login_required
def segmentation1():
    form = AddZone()
    if (request.form.get('editor.x') ):
        x1 = int(request.form.get('editor.x'))
        y1 = int(request.form.get('editor.y'))
        x2 = int(request.form.get('x2'))
        y2 = int(request.form.get('y2'))
        zone_name = request.form.get('zone_name')
        image, pic= get_image('being edited', db.images)
        img = Image.open(image)
        draw = ImageDraw.Draw(img)
        draw.rectangle(( (x1, y1),(x2, y2) ), fill=None, outline='blue', width=3)
        save_image2(img, 'being edited', db.images)
        x3 = min(x1, x2)
        x4 = max(x1, x2)
        y3 = min(y1, y2)
        y4 = max(y1, y2)
        Parking_name = db.parkings.find_one({'owner': current_user.username})['name']
        zone = {'name': zone_name,
                'parking': Parking_name,
                'capacity': 0,
                'occupancy': 0,
                'type': '',
                'parkedPlates': [],
                'priority': 0,
                'assignedCluster': '',
                'gates': [],
                'slots': [],
                'streets': [],
                'intersections': [],
                'corners': [],
                'owner': current_user.username
                }

        # zone has q1, q2, q3, q4
        q1 = Point(x1, y1)
        q2 = Point(x1, y2)
        q3 = Point(x2, y1)
        q4 = Point(x2, y2) 
        corners = [q1, q2, q3, q4]
        # zone borders are seg1, seg2, seg3, seg4
        seg1 = [q1, q2]
        seg2 = [q1, q3]
        seg3 = [q2, q4]
        seg4 = [q3, q4]

        for corner in corners:
            zone['corners'].append((corner.x, corner.y))
        # Add the gates withing the borders to the zone
        gates = db.parkings.find_one({'owner': current_user.username})['gates']
        for g in gates:
            x = g['position'][0]
            y = g['position'][1]
            if(x >= x3 and x <= x4 and y >= y3 and y <= y4):
                zone['gates'].append(g)

        # Add the slots within the borders to the zone
        slots = db.parkings.find_one({'owner': current_user.username})['slots']
        for slot in slots:
            x = slot['position'][0]
            y = slot['position'][1]
            if(x >= x3 and x <= x4 and y >= y3 and y <= y4):
                zone['slots'].append(slot)

        # Add the streets within the borders to the zone
        streets = db.parkings.find_one({'owner': current_user.username})['streets']
        streets_updated = []
        new_intersections = []
        for street in streets:
            # the point(s) of intersection of the street with the zone borders
            x1_intersection = 0
            y1_intersection = 0
            x2_intersection = 0
            y2_intersection = 0
            # street end points
            x_1 = street['endpoints'][0]
            y_1 = street['endpoints'][1]
            x_2 = street['endpoints'][2]
            y_2 = street['endpoints'][3]
            # street has p1 and p2
            p1 = Point(x_1, y_1)
            p2 = Point(x_2, y_2)
            a1, b1, c1 = street['equation']

            intersect_with1 = doIntersect(p1,p2, seg1[0], seg1[1])
            intersect_with2 = doIntersect(p1,p2, seg2[0], seg2[1])
            intersect_with3 = doIntersect(p1,p2, seg3[0], seg3[1])
            intersect_with4 = doIntersect(p1,p2, seg4[0], seg4[1])
            intersecting_segments = 0
            if(intersect_with1):
                intersecting_segments +=1
            if(intersect_with2):
                intersecting_segments +=1
            if(intersect_with3):
                intersecting_segments +=1
            if(intersect_with4):
                intersecting_segments +=1

            if (intersecting_segments == 0):
                #either the street is inside or outside
                if(x_1 >= x3 and x_1 <= x4 and y_1 >= y3 and y_1 <= y4):
                    # the whole street is inside the zone
                    zone['streets'].append(street)
                streets_updated.append(street)
                continue
            elif (intersecting_segments == 1):
                # only one end is inside
                if(intersect_with1):
                    a2, b2, c2 = find_equation(seg1[0].x, seg1[0].y, seg1[1].x, seg1[1].y)
                elif(intersect_with2):
                    a2, b2, c2 = find_equation(seg2[0].x, seg2[0].y, seg2[1].x, seg2[1].y)
                elif(intersect_with3):
                    a2, b2, c2 = find_equation(seg3[0].x, seg3[0].y, seg3[1].x, seg3[1].y)
                else:
                    a2, b2, c2 = find_equation(seg4[0].x, seg4[0].y, seg4[1].x, seg4[1].y)

                x1_intersection, y1_intersection = intersection_point(a1, b1, c1, a2, b2, c2)

                # Check if the intersection of the street and the border is at one of the street ends. If not, is_inside is false --> skip
                # If yes, check if the other end is inside the borders, if yes add the street to the zone
                # If no, the street is outside --> skip
                # if skipped, break the street to two segments, the one inside is added and the one outside is ignored
                intersections4 = db.parkings.find_one({'owner': current_user.username})['intersections']
                is_inside = False
                is_outside = False
                for k in intersections4:
                    if(find_distance_between_points(k['position'][0], k['position'][1], x1_intersection, y1_intersection)  <= 8):
                        if (find_distance_between_points(k['position'][0], k['position'][1], x_1, y_1) <= 8):
                            if(x_2 >= x3 and x_2 <= x4 and y_2 >= y3 and y_2 <= y4):
                                streets_updated.append(street)
                                zone['streets'].append(street)
                                is_inside = True
                                break
                            else:
                                streets_updated.append(street)
                                is_outside = True
                                break
                        else:
                            if(x_1 >= x3 and x_1 <= x4 and y_1>= y3 and y_1 <= y4):
                                streets_updated.append(street)
                                zone['streets'].append(street)
                                is_inside = True
                                break
                            else:
                                streets_updated.append(street)
                                is_outside = True
                                break
                            
                if(is_inside or is_outside):       
                    continue
                s1 = create_new_street(x_1, y_1, x1_intersection, y1_intersection)
                s2 = create_new_street(x_2, y_2, x1_intersection, y1_intersection)
                intersection = create_new_intersection(x1_intersection, y1_intersection)
                intersection['connected streets'].append(s1)
                intersection['connected streets'].append(s2)
                intersection['zone gate'] = True
                streets_updated.append(s1)
                streets_updated.append(s2)
                print('check int=1') 
                print(street['endpoints'])
                print(s1['endpoints'])
                print(s2['endpoints']) # the error is here

                # check which intersections are connected to the original street, then remove their connection with the original street
                # and connect them with the newly created streets.
                intersections1 = db.parkings.find_one({'owner': current_user.username})['intersections']
                for inter in intersections1:
                    if (street in inter['connected streets']):
                        inter['connected streets'].remove(street)
                        if(find_distance_between_points(inter['position'][0], inter['position'][1], x_1, y_1) <= 7):
                            # the intersection is connected to the first end of the street
                            inter['connected streets'].append(s1)
                        else:
                            inter['connected streets'].append(s2)

                db.parkings.update_one({'owner': current_user.username},
                                        {'$set': {'intersections': intersections1}
                                        })

                new_intersections.append(intersection)
                if(x_1 >= x3 and x_1 <= x4 and y_1 >= y3 and y_1 <= y4):
                    zone['streets'].append(s1)
                else:                    
                    zone['streets'].append(s2)
                
                #zone['intersections'].append(intersection)
                continue
            elif(intersecting_segments == 2):
                first_intersection = False
                second_intersection = False
                if(intersect_with1):
                    a2, b2, c2 = find_equation(seg1[0].x, seg1[0].y, seg1[1].x, seg1[1].y)
                    first_intersection = True
                if(intersect_with2):
                    if(first_intersection):
                        a3, b3, c3 = find_equation(seg2[0].x, seg2[0].y, seg2[1].x, seg2[1].y)
                        second_intersection = True
                    else:
                        a2, b2, c2 = find_equation(seg2[0].x, seg2[0].y, seg2[1].x, seg2[1].y)
                        first_intersection = True
                if(intersect_with3):
                    if(second_intersection == False):
                        if (first_intersection):
                            a3, b3, c3 = find_equation(seg3[0].x, seg3[0].y, seg3[1].x, seg3[1].y)
                            second_intersection = True
                        else:
                            a2, b2, c2 = find_equation(seg3[0].x, seg3[0].y, seg3[1].x, seg3[1].y)
                            first_intersection = True
                if(intersect_with4):
                    if(second_intersection == False):
                        if (first_intersection):
                            a3, b3, c3 = find_equation(seg4[0].x, seg4[0].y, seg4[1].x, seg4[1].y)
                        else:
                            a2, b2, c2 = find_equation(seg4[0].x, seg4[0].y, seg4[1].x, seg4[1].y)

                x1_intersection, y1_intersection = intersection_point(a1, b1, c1, a2, b2, c2)
                x2_intersection, y2_intersection = intersection_point(a1, b1, c1, a3, b3, c3)

                intersections5 = db.parkings.find_one({'owner': current_user.username})['intersections']
                
                is_inside1 = False # if true, first end of the street begins at a zone gate x1_intersection, y1_intersection
                is_inside2 = False # if true, second end of the street begins at a zone gate x2_intersection, y2_intersection
                for k in intersections5:
                    if(find_distance_between_points(k['position'][0], k['position'][1], x1_intersection, y1_intersection)  <= 8):
                        is_inside1 = True
                        continue
                    elif(find_distance_between_points(k['position'][0], k['position'][1], x2_intersection, y2_intersection)  <= 8):
                        is_inside2 = True
                        continue

                if(is_inside1 and is_inside2):
                    streets_updated.append(street)
                    zone['streets'].append(street)
                    continue
                if(is_inside1):
                    street_inside = create_new_street(x1_intersection, y1_intersection, x2_intersection, y2_intersection)
                    street_outside = None
                    if (find_distance_between_points(x_1, y_1, x1_intersection, y1_intersectin) <= 7):
                        street_outside = create_new_street(x2_intersection, y2_intersection, x_2, y_2)
                    elif(find_distance_between_points(x_2, y_2, x1_intersection, y1_intersection) <= 7):
                        street_outside = create_new_street(x2_intersection, y2_intersection, x_1, y_1)
                    else:
                        app.logger.info('check 628')
                    streets_updated.append(street_inside)
                    streets_updated.append(street_outside)
                    intersection = create_new_intersection(x2_intersection, y2_intersection)
                    intersection['connected streets'].append(street_inside)
                    intersection['connected streets'].append(street_outside)
                    intersection['zone gate'] = True
                    zone['streets'].append(street_inside)
                    # check which intersections are connected to the original street, then remove their connection with the original street
                    # and connect them with the newly created streets.
                    intersections11 = db.parkings.find_one({'owner': current_user.username})['intersections']
                    for inter in intersections11:
                        if (street in inter['connected streets']):
                            inter['connected streets'].remove(street)
                            if(find_distance(inter['position'[0], inter['position'][1], street_inside]) <= 5):
                                # the intersection is connected to the first end of the street
                                inter['connected streets'].append(street_inside)
                            else:
                                inter['connected streets'].append(street_outside)

                    db.parkings.update_one({'owner': current_user.username},
                                           {'$set': {'intersections': intersections11}
                                           })
                    continue
                if(is_inside2):
                    street_inside = create_new_street(x1_intersection, y1_intersection, x2_intersection, y2_intersection)
                    street_outside = None
                    if (find_distance_between_points(x_1, y_1, x2_intersection, y2_intersection) <= 7):
                        street_outside = create_new_street(x1_intersection, y1_intersection, x_2, y_2)
                    elif(find_distance_between_points(x_2, y_2, x2_intersection, y2_intersection) <= 7):
                        street_outside == create_new_street(x1_intersection, y1_intersection, x_1, y_1)
                    else:
                        app.logger.info('check 646')
                    streets_updated.append(street_inside)
                    streets_updated.append(street_outside)
                    intersection = create_new_intersection(x1_intersection, y1_intersection)
                    intersection['connected streets'].append(street_inside)
                    intersection['connected streets'].append(street_outside)
                    intersection['zone gate'] = True
                    zone['streets'].append(street_inside)
                    # check which intersections are connected to the original street, then remove their connection with the original street
                    # and connect them with the newly created streets.
                    intersections12 = db.parkings.find_one({'owner': current_user.username})['intersections']
                    
                    for inter in intersections12:
                        if (street in inter['connected streets']):
                            inter['connected streets'].remove(street)
                            if(find_distance(inter['position'[0], inter['position'][1], street_inside]) <= 5):
                                # the intersection is connected to the first end of the street
                                inter['connected streets'].append(street_inside)
                            else:
                                inter['connected streets'].append(street_outside)

                    db.parkings.update_one({'owner': current_user.username},
                                           {'$set': {'intersections': intersections12}
                                           })
                    continue

                street_between = create_new_street(x1_intersection, y1_intersection, x2_intersection, y2_intersection) 
                intersection1 = create_new_intersection(x1_intersection, y1_intersection)
                intersection2 = create_new_intersection(x2_intersection, y2_intersection)
                intersection1['connected streets'].append(street_between)
                intersection2['connected streets'].append(street_between)
                intersection1['zone gate'] = True
                intersection2['zone gate'] = True

                street_outside1 = None
                street_outside2 = None
                
                if(find_distance_between_points(x_1, y_1, x1_intersection, y1_intersection) <= find_distance_between_points(x_1, y_1, x2_intersection, y2_intersection)):
                    street_outside1 = create_new_street(x_1, y_1, x1_intersection, y1_intersection)
                    street_outside2 = create_new_street(x_2, y_2, x2_intersection, y2_intersection)
                    intersection1['connected streets'].append(street_outside1)
                    intersection2['connected streets'].append(street_outside2)
                else:
                    street_outside1 = create_new_street(x_1, y_1, x2_intersection, y2_intersection)
                    street_outside2 = create_new_street(x_2, y_2, x1_intersection, y1_intersection)
                    intersection1['connected streets'].append(street_outside2)
                    intersection2['connected streets'].append(street_outside1)
                
                # check which intersections are connected to the original street, then remove their connection with the original street
                # and connect them with the newly created streets.
                intersections2 = db.parkings.find_one({'owner': current_user.username})['intersections']
                for inter in intersections2:
                    if (street in inter['connected streets']):
                        inter['connected streets'].remove(street)
                        if(find_distance_between_points(inter['position'][0], inter['position'][1], x_1, y_1) <= 5):
                            # the intersection is connected to the first end of the street
                            inter['connected streets'].append(street_outside1)
                        else:
                            inter['connected streets'].append(street_outside2)
                
                db.parkings.update_one({'owner': current_user.username},
                                       {'$set': {'intersections': intersections2}
                                       })

                new_intersections.append(intersection1)
                new_intersections.append(intersection2)
                zone['streets'].append(street_between)
                streets_updated.append(street_between)
                streets_updated.append(street_outside1)
                streets_updated.append(street_outside2)
                continue
        
        # update the streets file with the newly created streets
        db.parkings.update_one({'owner': current_user.username},
                               {'$set': {'streets': streets_updated}
                               })
        print('length---------------------------------')
        print(len(streets_updated))

        # update the intersections file with the new zone gates 
        ints = db.parkings.find_one({'owner': current_user.username})['intersections']  
        for r in new_intersections:
            ints.append(r)
        db.parkings.update_one({'owner': current_user.username},
                               {'$set': {'intersections': ints}
                               })

        # Add the intersectinon within the borders to the zone
        intersections3 = db.parkings.find_one({'owner': current_user.username})['intersections']
        for inter in intersections3:
            x = inter['position'][0]
            y = inter['position'][1]
            print(x, y)
            if(x >= (x3-8) and x <= (x4 +8) and y >= (y3-8) and y <= (y4+8)):
                zone['intersections'].append(inter)
                
        # Add the elements of the zone to the clusters collection
        db.clusters.insert_one(zone)

        # retireve the automatically generated id of the inserted zone
        zone_id = db.clusters.find_one({'name': zone_name,
                                        'owner': current_user.username})['_id']
        # add the zone id to the parking document of the current user
        db.parkings.update_one({'owner': current_user.username},
                               {'$push': {'zones': zone_id}
                               })
        draw_zone(zone, image)
    
        _, pic2 = get_image('being edited', db.images)
        return render_template('customization_segmentation1.html', first_time='no', pic=pic2, corners=corners, form=form )

    elif(request.form.get('segment')):
        
        _, pic2 = get_image('being edited', db.images)
        return render_template('customization_segmentation1.html', pic=pic2, first_time='yes')

    _, pic2 = get_image('being edited', db.images)   
    return render_template('customization_segmentation1.html')

@app.route("/customization/segmentation2", methods=['GET', 'POST'])
@login_required
def segmentation2():
    form= AddZone()
    if(request.method == 'POST'):
        x = int(request.form.get('editor.x'))
        y = int(request.form.get('editor.y'))
        zone_name = request.form.get('zone_name')
        first_time = request.form.get('first time')
        if zone_name == '':
            flash('A name is required for the zone', 'info')
            _, pic2 = get_image('being edited', db.images)   
            return render_template('customization_segmentation1.html', pic=pic2, first_time= first_time)
        image, pic= get_image('being edited', db.images)
        print(zone_name)
        first_time = request.form.get('first time')
        if (first_time == 'yes'):
            _, pic2 = get_image('being edited', db.images)
            return render_template('customization_segmentation2.html', pic=pic2, x = x, y = y, zone_name=zone_name)
       
        zones = db.clusters.find({'owner': current_user.username})
        for zone in zones:
            for corner in zone['corners']:
                if (find_distance_between_points(x, y, corner[0], corner[1]) <= 5):
                    _, pic2 = get_image('being edited', db.images)
                    return render_template('customization_segmentation2.html', pic=pic2, x = corner[0], y = corner[1], zone_name=zone_name)
        
        flash('New zones must be connected to previous zones corners. Try again', 'danger')
        _, pic2 = get_image('being edited', db.images)
        return render_template('customization_segmentation2.html', pic=pic2, first_time='no')
    return render_template('customization_segmentation2.html')   

@app.route("/customization/final", methods=['GET', 'POST'])
@login_required
def final():
    if request.method == 'POST':
        print(request.form)
        # if request.form.get('submit') == 'submit':
        print('here finally')
        zones = db.clusters.find({'owner': current_user.username})
        # slots = db.parkings.find_one({'owner': current_user.username})['slots']
        # streets = db.parkings.find_one({'owner': current_user.username})['streets']
        intersections = db.parkings.find_one({'owner': current_user.username})['intersections']
        # gates = db.parkings.find_one({'owner': current_user.username})['gates']
        zones_list = list(zones)
        image, pic= get_image('original image', db.images)
        for source_zone in zones_list:
            for dest_zone in zones_list:
                if (equal_zones(source_zone, dest_zone)):
                    continue

                source_street = source_zone['streets'][0]
                dest_street = dest_zone['streets'][0]
                print('check parameters')
                print(source_street)
                print('------')
                print(dest_street)
                print('----------')
                print(intersections)
                shortest_path = find_path(source_street, dest_street, intersections)
                draw_path(shortest_path, zones_list, image, dest_street, str(source_zone['name']), str(dest_zone['name']))
    pictures = db.staticPaths.find({'owner': current_user.username})
    images = []
    for pic in pictures:
        img_str = base64.b64encode(pic['path'])
        data_url = 'data:image/jpg;base64,' + img_str.decode()
        images.append(data_url)
    return render_template('final.html', images=images)
    # print('not a POST request')
    # return render_template('final.html')

# Customization tool logic
def create_new_street(x1, y1, x2, y2):
    street = {'endpoints': (x1, y1, x2, y2),
              'equation' : find_equation(x1,y1, x2, y2),
              'Bi directional': True}
    return street

def find_equation(x1, y1, x2, y2):
        if ((x2 - x1) == 0):
            return (-1, 0, x1)
        m = (y2-y1)/(x2-x1)
        if (m == 0):
            return (0, -1, y1)
        else:
            b = y1 - (m*x1)
        return (m, -1, b)

def create_new_Slot(x, y):
    slot = {'position': (x, y),
            'connected street': None}
    return slot

def create_new_intersection(x, y):
    intersection = {'position': (x,y),
                    'connected streets': [],
                    'zone gate': False}
    return intersection

def create_new_gate(x, y):
    gate = {'position': (x, y),
            'connected street': None}
    return gate

def equal_zones(z1, z2):
    return (str(z1['_id']) == str(z2['_id']))

def equals(i1, i2):
    if ('connected streets' in i1):
        if ('connected streets' in i2):
            return (i1['position'][0] == i2['position'][0] and i1['position'][1] == i2['position'][1])
        else:
            return False
    else:
        if ('connected streets' in i2):
            return False
        else:
            return (i1['endpoints'][0] == i2['endpoints'][0] and i1['endpoints'][1] == i2['endpoints'][1] and i1['endpoints'][2] == i2['endpoints'][2] and i1['endpoints'][3] == i2['endpoints'][3])

def find_path(src, dst, inters):
    paths = [[src]]
    for path in paths:
        #check if there is a loop
        duplicate = False
        for i1 in range(len(path)):
            for i2 in range(len(path)):
                if(i1 == i2):
                    continue
                if(equals(path[i1], path[i2])):
                    print('removed')
                    if (path in paths):
                        paths.remove(path)
                        duplicate = True
                        break
        if(duplicate):
            continue
        print('**********')
        print('path is:')
        print(printPath(path))
        for i in inters:
            print('next intersection is: ')
            print(i['position'])
            if (i not in path):
                if(path[-1] in i['connected streets']):
                    for p in i['connected streets']:
                        print('next street is: ')
                        print(p['endpoints'])
                        if (p is path[-1]):
                            continue
                        new_path = copy.deepcopy(path)
                        new_path.append(i)
                        new_path.append(p)
                        if (equal(p, dst)):
                            print('done')
                            return new_path
                            #Done
                        else:
                            print('else')
                            paths.append(new_path)
    return "not found"

def equal(s1, s2):
    return s1['endpoints'] == s2['endpoints']

def printPath(path):
    printablePath = []
    for item in path:
        if ('connected streets' in item): 
            printablePath.append('intersection')
            printablePath.append(item['position'])
        else:
            printablePath.append('street')
            printablePath.append(item['endpoints'])
    return printablePath

def draw_path(path, zones, image, dest_street, source_zone, dest_zone):
    img = Image.open(image)
    draw = ImageDraw.Draw(img)
    for item in path:
        print("checking the item")
        if ('connected streets' in item): # check if this item is an intersection
            print(item)
            x = item['position'][0]
            y = item['position'][1]
            draw.rectangle(( (x - 4, y - 4),(x + 4, y + 4) ), fill="green")
        else:
            print(item)
            x1 = item['endpoints'][0]
            y1 = item['endpoints'][1]
            x2 = item['endpoints'][2]
            y2 = item['endpoints'][3]
            
            # # if the street is the source or the destination, draw half the line
            # if (item is path[0] or item is path[-1]):
            #     x3, y3 = find_middle_point(x1, y1, x2, y2)
            #     # loop through all intersections
            #     for item2 in path:
            #         if ('connected streets' in item2):
            #             if (find_distance_between_points(item2['position'][0], item2['position'][1], x1, y1) < 8):
            #                 draw.line(( (x3, y3),(x1, y1) ), fill="red", width=3)
            #             else:
            #                 draw.line(( (x3, y3),(x2, y2) ), fill="red", width=3)
            # else:    
            draw.line(( (x1, y1),(x2, y2) ), fill="red", width=3)
    
    # x11 = path[-1]['endpoints'][0]
    # y11 = path[-1]['endpoints'][1]
    # x22 = path[-1]['endpoints'][2]
    # y22 = path[-1]['endpoints'][3]
    # for item in path:
    #     if ('connected streets' in item):
    #         if (find_distance_between_points(item['position'][0], item['position'][1], x11, y11) <= 7):
    #             draw.rectangle(( (x22 - 6, y22 - 6),(x22 + 6, y22 + 6) ), fill="orange")
    #         elif(find_distance_between_points(item['position'][0], item['position'][1], x22, y22) <= 7):
    #             draw.rectangle(( (x11 - 6, y11 - 6),(x11 + 6, y11 + 6) ), fill="orange")
    
    for zone in zones:
        if (dest_street in zone['streets']):
            c1 = zone['corners'][0]
            c2 = zone['corners'][1]
            c3 = zone['corners'][2]
            c4 = zone['corners'][3]
            draw.rectangle((c1[0], c1[1], c4[0], c4[1]), outline='blue', width=4)
            break

    save_path(img, source_zone, dest_zone)
    return

def find_middle_point(x1, y1, x2, y2):
    return (x1 + x2)/2, ((y1 + y2)/2)
def draw_zone(zone, image):
    img = Image.open(image)
    draw = ImageDraw.Draw(img)
    c1 = zone['corners'][0]
    c2 = zone['corners'][1]
    c3 = zone['corners'][2]
    c4 = zone['corners'][3]

    seg1 = [c1, c2]
    seg2 = [c1, c3]
    seg3 = [c2, c4]
    seg4 = [c3, c4]
    draw.line(( (c1[0], c1[1]),(c2[0], c2[1]) ), fill="blue", width=2)
    draw.line(( (c1[0], c1[1]),(c3[0], c3[1]) ), fill="blue", width=2)
    draw.line(( (c2[0], c2[1]),(c4[0], c4[1]) ), fill="blue", width=2)
    draw.line(( (c3[0], c3[1]),(c4[0], c4[1]) ), fill="blue", width=2)
    for slot in zone['slots']:
        x = slot['position'][0]
        y = slot['position'][1]
        draw.rectangle(( (x - 4, y - 4),(x + 4, y + 4) ), fill="green")
    for gate in zone['gates']:
        x = gate['position'][0]
        y = gate['position'][1]
        draw.rectangle(( (x - 4, y - 4),(x + 4, y + 4) ), fill="green")
    for intersection in zone['intersections']:
        x = intersection['position'][0]
        y = intersection['position'][1]
        draw.rectangle(( (x - 4, y - 4),(x + 4, y + 4) ), fill="green")
    for street in zone['streets']:
        x1 = street['endpoints'][0]
        y1 = street['endpoints'][1]
        x2 = street['endpoints'][2]
        y2 = street['endpoints'][3]
        draw.line(( (x1, y1),(x2, y2) ), fill="green", width=3)

    save_image2(img, 'being edited', db.images)
    return

#intersection between the two lines: a1*x + b1*y + c1 = 0, and a2*x + b2y + c2 = 0
def intersection_point(a1, b1, c1, a2, b2, c2):
    x = (-1) * ((c1*b2) - (c2*b1))/((a1*b2) - (a2*b1))
    y = (-1) * ((a1*c2) - (a2*c1))/((a1*b2) - a2*b1)
    return (x,y)

# distance between a point and a line is: d = (|Ax + By + C|)/(sqrt(A^2 + B^2)) , x, y for the point and A, B, C for the line
def find_distance(x, y, street):
    d = abs((street['equation'][0] * x) + street['equation'][1] * y + street['equation'][2]) / (math.sqrt(pow(street['equation'][0], 2) + pow(street['equation'][1], 2)))
    return d

def find_distance_between_points(x1, y1, x2, y2):
    return math.sqrt(pow((x2-x1), 2) + pow((y2 - y1), 2))

############# Following code is from https://www.geeksforgeeks.org/check-if-two-given-line-segments-intersect/ ###################
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
 
# Given three collinear points p, q, r, the function checks if
# point q lies on line segment 'pr'
def onSegment(p, q, r):
    if ( (q.x <= max(p.x, r.x)) and (q.x >= min(p.x, r.x)) and
           (q.y <= max(p.y, r.y)) and (q.y >= min(p.y, r.y))):
        return True
    return False
 
def orientation(p, q, r):
    # to find the orientation of an ordered triplet (p,q,r)
    # function returns the following values:
    # 0 : Collinear points
    # 1 : Clockwise points
    # 2 : Counterclockwise
     
    # See https://www.geeksforgeeks.org/orientation-3-ordered-points/amp/
    # for details of below formula.
     
    val = (float(q.y - p.y) * (r.x - q.x)) - (float(q.x - p.x) * (r.y - q.y))
    if (val > 0):
         
        # Clockwise orientation
        return 1
    elif (val < 0):
         
        # Counterclockwise orientation
        return 2
    else:
         
        # Collinear orientation
        return 0
 
# The main function that returns true if
# the line segment 'p1q1' and 'p2q2' intersect.
def doIntersect(p1,q1,p2,q2):
     
    # Find the 4 orientations required for
    # the general and special cases
    o1 = orientation(p1, q1, p2)
    o2 = orientation(p1, q1, q2)
    o3 = orientation(p2, q2, p1)
    o4 = orientation(p2, q2, q1)
 
    # General case
    if ((o1 != o2) and (o3 != o4)):
        return True
 
    # Special Cases
 
    # p1 , q1 and p2 are collinear and p2 lies on segment p1q1
    if ((o1 == 0) and onSegment(p1, p2, q1)):
        return True
 
    # p1 , q1 and q2 are collinear and q2 lies on segment p1q1
    if ((o2 == 0) and onSegment(p1, q2, q1)):
        return True
 
    # p2 , q2 and p1 are collinear and p1 lies on segment p2q2
    if ((o3 == 0) and onSegment(p2, p1, q2)):
        return True
 
    # p2 , q2 and q1 are collinear and q1 lies on segment p2q2
    if ((o4 == 0) and onSegment(p2, q1, q2)):
        return True
 
    # If none of the cases
    return False
 ##################################################################
