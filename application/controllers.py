from flask import Flask, render_template, redirect,request,url_for
from flask import current_app as app
from .models import *
import time
import math
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")


@app.route("/",methods=["GET","POST"])
@app.route("/login",methods=["GET","POST"])
def login():
    if request.method=="POST":
        email=request.form.get("username")
        pwd=request.form.get("pwd")
        this_user=User.query.filter_by(email=email).first()
        if this_user:
            if this_user.password == pwd:
                if this_user.type=='Admin':
                    return redirect('/dashboard/admin')
                else:
                    return redirect(url_for("dashboard",id=this_user.id))
            else:
                return render_template("login.html", error="Password is Wrong")
        else:
            return render_template("login.html", error="No user found")
    else:
        return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method=="POST":
        name=request.form.get("name")
        email=request.form.get("email")
        pwd=request.form.get("pwd")
        user_email=User.query.filter_by(email=email).first()
        if user_email:
            return render_template("register.html", error="Email Already registered")
        else:
            user = User(name=name, email=email, password=pwd)
            db.session.add(user)
            db.session.commit()
            return redirect("/login")
    return render_template("register.html")

@app.route('/dashboard/admin',methods=['GET','POST'])
def admin():
    this_user=User.query.filter_by(type='Admin').first()
    lots=Parking_Lot.query.all()
    return render_template('admin_dashboard.html',lots=lots,user=this_user)

@app.route('/add_lot',methods=['GET',"POST"])
def add_lot():
    if request.method=='POST':
        location_name=request.form.get('location_name')
        address=request.form.get('address')
        pincode=request.form.get('pincode')
        max_spots=request.form.get('max_spots')
        price=request.form.get('price')
        lot=Parking_Lot(location_name=location_name,address=address,price=price,pincode=pincode,max_spots=max_spots)
        db.session.add(lot)
        db.session.flush()
        for i in range(int(max_spots)):
            spot=Parking_Spot(lot_id=lot.id,status='A')
            db.session.add(spot)
        db.session.commit()
        return redirect('/dashboard/admin')
    return render_template('new_lot.html')

@app.route('/delete_lot/<int:id>')
def delete_lot(id):
    lot=Parking_Lot.query.get(id)
    occupied = any(spot.status == 'O' for spot in lot.spots)
    if not(occupied):
        for spot in lot.spots:
            db.session.delete(spot)
        db.session.delete(lot)
        db.session.commit()
        return redirect('/dashboard/admin')
    else:
        lots = Parking_Lot.query.all()
        this_user = User.query.filter_by(type='Admin').first()
        warning = "Spot(s) occupied, can't delete now."
        return render_template('admin_dashboard.html', lots=lots, user=this_user, warning=warning)

@app.route('/edit_lot/<int:id>',methods=['GET','POST'])
def edit_lot(id):
    lot=Parking_Lot.query.get(id)
    if request.method=="POST":
        location_name=request.form.get('location_name')
        address=request.form.get('address')
        pincode=request.form.get('pincode')
        max_spots=request.form.get('max_spots')
        price=request.form.get('price')
        lot=Parking_Lot.query.get(id)
        #checking for occupied--done
        occupied=0
        for spot in lot.spots:
            if spot.status=='O':
                occupied+=1
        if occupied>int(max_spots):
            warning = "Spots are already occupied, spots can’t be reduced."
            return render_template('edit_lot.html', lot=lot, warning=warning)
        #updating spots in database
        extra_spots=int(lot.max_spots)-int(max_spots)
        if extra_spots>0:
            available_spot=[spot for spot in lot.spots if spot.status=='A']
            for i in available_spot[:extra_spots]:
                db.session.delete(i)
        else:
            extra_spots*=-1
            for i in range(extra_spots):
                spot=Parking_Spot(lot_id=lot.id,status='A')
                db.session.add(spot)
        #Updating database --done
        lot.location_name = location_name
        lot.address = address
        lot.pincode = pincode
        lot.max_spots = max_spots
        lot.price = price
        db.session.commit()
        return redirect('/dashboard/admin')
    return render_template('edit_lot.html',lot=lot)

@app.route('/user_details')
def user_details():
    users=User.query.all()
    admin=User.query.filter_by(type='Admin').first()
    return render_template('admin_dashboard2.html',users=users,admin=admin)

@app.route('/search_users')
def search_users():
    admin=User.query.filter_by(type='Admin').first()
    return render_template('admin_search.html',admin=admin)

@app.route('/search_result')
def search_result():
    admin=User.query.filter_by(type='Admin').first()
    search_word=request.args.get('search')
    key = request.args.get("key")
    if key == "user":
        result=User.query.filter_by(name=search_word).all()
    else:
        result = Parking_Lot.query.filter_by(location_name = search_word).all()
        for lot in result:
            lot.available_spots = len([spot for spot in lot.spots if spot.status == 'A'])
    return render_template('search_results.html',result=result,word=search_word,admin=admin,key=key)

@app.route('/edit-details/<int:id>',methods=['GET','POST'])
def edit_details(id):
    this_user=User.query.get(id)
    if request.method=='POST':
        name=request.form.get('name')
        address=request.form.get('address')
        dob=request.form.get('dob')
        this_user.name=name
        this_user.address=address
        this_user.dob=dob
        db.session.commit()
        if this_user.type=='Admin':
            return redirect('/dashboard/admin')
        else:
            return redirect(url_for('dashboard', id=this_user.id))
    return render_template('edit_profile.html',user=this_user)

@app.route('/view_spot/<int:id>',methods=['GET','POST'])
def view_spot(id):
    spot=Parking_Spot.query.get(id)
    if request.method=="POST":
        check=request.form.get('status')
        if check=="Available":
            db.session.delete(spot)    
            lot=spot.main
            lot.max_spots=int(lot.max_spots)-1
            db.session.commit()
            return redirect('/dashboard/admin')
        else:
            status = spot.status
            display = 'Occupied' if status == 'O' else 'Available'
            warning = "Already occupied, can't delete."
            return render_template('delete_spot.html', spot=spot, display=display, warning=warning)
    status=spot.status
    if status=='O':
        display='Occupied'
    else:
        display='Available'
    return render_template('delete_spot.html',spot=spot,display=display)

@app.route('/occupied/<int:id>')
def occupied(id):
    this_spot=Parking_Spot.query.get(id)
    reserved=Reserve_Spot.query.filter_by(spot_id=this_spot.id,leaving_timestamp=0).first()
    user=User.query.get(reserved.user_id)
    parking_time_str = ''
    est_cost=0
    if reserved and reserved.parking_timestamp:
        parking_time_str = datetime.fromtimestamp(reserved.parking_timestamp).strftime('%Y-%m-%dT%H:%M')
        now = int(time.time())
        duration_seconds = now - reserved.parking_timestamp
        hours = max(1, math.ceil(duration_seconds / 3600))
        est_cost = hours * this_spot.main.price
    return render_template('occupied_spot.html', spot=this_spot, reserved=reserved, parking_time_str=parking_time_str,user=user,cost=est_cost)


@app.route('/admin_summary')
def admin_summary():
    user=User.query.filter_by(type='Admin').first()
    active=len(Reserved_History.query.filter_by(leaving_timestamp=0).all())
    previous = len(Reserved_History.query.filter(Reserved_History.leaving_timestamp != 0).all())
    #1st
    plt.subplot(1,2,1)
    labels = ["Occupied","Parked Out"]
    sizes =[active,previous]
    plt.bar(labels,sizes)
    plt.xlabel("Status of the Spots")
    plt.ylabel("Frequency")
    plt.title("Parking Spots Distribution")
    

    plt.subplot(1,2,2)
    labels = ["Occupied","Parked Out"]
    sizes =[active,previous]
    colors = ["red","green"]
    plt.pie(sizes,labels=labels,colors=colors,autopct = "%1.1f%%")
    plt.title("Status of Parking Spots")    
    plt.savefig("static/admin_1.png")
    plt.clf()
    bill=0
    completed = Reserved_History.query.filter(Reserved_History.leaving_timestamp != 0).all()
    for lot in completed:
        bill+=lot.cost
    #2nd
    lots=Parking_Lot.query.all()
    hist=Reserved_History.query.all()    
    for lot in lots:
        lot.revenue=0
        for i in hist:
            if i.address==lot.address:
                lot.revenue+=i.cost
    location = [i.location_name for i in lots if i.revenue>0]
    revenue = [i.revenue for i in lots if i.revenue>0]
    plt.subplot(1,2,1)
    plt.bar(location,revenue)
    plt.xlabel("Location")
    plt.ylabel("Revenue")
    plt.title("Lots' Revenue")
    
    plt.subplot(1,2,2)
    plt.pie(revenue,labels=location,autopct = "%1.1f%%")
    plt.title("Revenue from each Lot")
    plt.savefig("static/admin_2.png")
    plt.clf()
    return render_template('admin_summary.html',user=user,active=active,previous=previous,bill=bill)

#User Routes from now on

@app.route('/dashboard/<int:id>')
def dashboard(id):
    this_user = User.query.get(id)
    lots = Parking_Lot.query.all()
    for lot in lots:
        lot.available_spots = len([spot for spot in lot.spots if spot.status == 'A'])
    reserved=Reserve_Spot.query.filter_by(user_id=this_user.id).all()
    hist=Reserved_History.query.filter_by(user_id=this_user.id).all()
    for i in reserved:
        i.parking_datetime = datetime.fromtimestamp(i.parking_timestamp).strftime('%Y-%m-%dT%H:%M')
    for i in hist:
        i.parking_datetime = datetime.fromtimestamp(i.parking_timestamp).strftime('%Y-%m-%dT%H:%M')
    return render_template('user_dashboard.html', user=this_user, lots=lots,reserved=reserved,hist=hist)

@app.route('/search_lots/<int:id>')
def search_lots(id):
    this_user=User.query.get(id)
    search_word=request.args.get('search')
    key = request.args.get("key")
    if key == "pincode":
        results = Parking_Lot.query.filter_by(pincode= search_word).all()
    else:
        results = Parking_Lot.query.filter_by(location_name = search_word).all()
    for lot in results:
        lot.available_spots = len([spot for spot in lot.spots if spot.status == 'A'])
    reserved=Reserve_Spot.query.filter_by(user_id=this_user.id).all()
    hist=Reserved_History.query.filter_by(user_id=this_user.id).all()
    for i in reserved:
        i.parking_datetime = datetime.fromtimestamp(i.parking_timestamp).strftime('%Y-%m-%dT%H:%M')
    for i in hist:
        i.parking_datetime = datetime.fromtimestamp(i.parking_timestamp).strftime('%Y-%m-%dT%H:%M')
    return render_template('user_dashboard2.html',word=search_word,results=results,key=key,reserved=reserved,user=this_user,hist=hist)

@app.route('/book_spot/<int:userid>/<int:lotid>',methods=['GET','POST'])
def book_spot(userid,lotid):
    this_user=User.query.get(userid)
    this_lot=Parking_Lot.query.get(lotid)
    for spot in this_lot.spots:
            if spot.status=='A':
                this_spot=spot
                break
    if request.method=='POST':
        vehicle_no=request.form.get('vehicle')
        spot=request.form.get('spot')
        this_spot=Parking_Spot.query.get(spot)
        this_spot.status='O'
        reserve=Reserve_Spot(spot_id=this_spot.id, user_id=this_user.id,parking_timestamp=int(time.time()), leaving_timestamp=0, cost=0, vehicle_no=vehicle_no)
        reserve_hist=Reserved_History(spot_id=this_spot.id, user_id=this_user.id,parking_timestamp=int(time.time()), leaving_timestamp=0, cost=0, vehicle_no=vehicle_no,address=this_lot.address)
        db.session.add(reserve)
        db.session.add(reserve_hist)
        db.session.commit()
        return redirect(url_for("dashboard",id=this_user.id))
    return render_template('book_spot.html', id=this_user.id, lot=this_lot.id,spot=this_spot)

@app.route('/release_spot/<int:id>', methods=['GET','POST'])
def release_spot(id):
    this_reserved=Reserve_Spot.query.get(id)
    reserved_hist=Reserved_History.query.filter_by(parking_timestamp=this_reserved.parking_timestamp).first()
    this_spot=this_reserved.holder
    parking_datetime = datetime.fromtimestamp(this_reserved.parking_timestamp).strftime('%Y-%m-%dT%H:%M')
    now = int(time.time())
    this_reserved.leaving_timestamp=now
    reserved_hist.leaving_timestamp=now
    leaving_datetime = datetime.fromtimestamp(now).strftime('%Y-%m-%dT%H:%M')
    duration_seconds = now - this_reserved.parking_timestamp
    hours = max(1, math.ceil(duration_seconds / 3600))
    net_cost = hours * this_spot.main.price
    if request.method=='POST':
        this_reserved.cost=net_cost
        reserved_hist.cost=net_cost
        reserved_hist.status='R'
        this_spot.status='A'
        db.session.delete(this_reserved)
        db.session.commit()
        return redirect(url_for('dashboard',id=this_reserved.user_id))
    return render_template('release_spot.html',reserved=this_reserved,spot=this_spot,parking=parking_datetime,leaving=leaving_datetime,cost=net_cost)

@app.route('/user_summary/<int:id>')
def user_summary(id):
    user=User.query.get(id)
    active=len(Reserved_History.query.filter_by(user_id=user.id,leaving_timestamp=0).all())
    previous = len(Reserved_History.query.filter(Reserved_History.user_id == user.id,Reserved_History.leaving_timestamp != 0).all())
    #pie
    labels = ["Occupied","Parked Out    "]
    sizes =[active,previous]
    colors = ["red","green"]
    plt.pie(sizes,labels=labels,colors=colors,autopct = "%1.1f%%")
    plt.title("Status of Parking Spots")
    plt.savefig("static/user_pie.png")
    plt.clf()
    #bar
    labels = ["Occupied","Parked Out"]
    sizes =[active,previous]
    plt.bar(labels,sizes)
    plt.xlabel("Status of the Spots")
    plt.ylabel("Frequency")
    plt.title("Parking Spots Distribution")
    plt.savefig("static/user_bar.png")
    plt.clf()
    bill=0
    all = Reserved_History.query.filter_by(user_id = user.id).all()
    labels=[i.address for i in all]
    sizes=[]
    for i in labels:
        total=0
        for j in all:
            if j.address==i:
                total+=j.cost
        sizes.append(total)
    plt.bar(labels,sizes)
    plt.xlabel("Parking Lots")
    plt.ylabel("Cost")
    plt.title("Money paid at diff lots")
    plt.savefig("static/user_bar2.png")
    plt.clf()
    completed = Reserved_History.query.filter(Reserved_History.user_id == user.id,Reserved_History.leaving_timestamp != 0).all()
    for lot in completed:
        bill+=lot.cost
    return render_template('user_summary.html',user=user,active=active,previous=previous,bill=bill)