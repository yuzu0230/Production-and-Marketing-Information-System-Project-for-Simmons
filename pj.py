import os
from datetime import datetime, timedelta
from math import pow

import json
from flask import Flask, request, jsonify, render_template, abort
from flask_cors import CORS
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import *
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

app = Flask(__name__)
CORS(app)

basedir = os.path.abspath(os.path.dirname(__file__))
# CREATE DATABASE, "test.db" is database's name
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'test.db')
# Optional: But it will silence the deprecation warning in the console.
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

ma = Marshmallow(app)

class Member(db.Model):
    __tablename__ = "member"
    id = db.Column(db.Integer, primary_key=True)
    member_name = db.Column(db.String(50), nullable=False)
    sex = db.Column(db.String(50), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    monetary = db.Column(db.Integer, nullable=False)

    db_member_order = db.relationship("Order", backref="member")

    def __init__(self, member_name, sex, age):
        self.member_name = member_name
        self.sex = sex
        self.age = age
        self.monetary = 0

order_product_relation = db.Table(
    'order_product',
    db.Column('order_id', db.Integer, db.ForeignKey('order.order_id')),
    db.Column('product_id', db.Integer, db.ForeignKey('product.product_id'))
    )

class Order(db.Model):
    __tablename__ = "order"
    order_id = db.Column(db.Integer, primary_key=True)
    total_amount = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, nullable=False)

    # 一對多的多
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)

    order_product_relation = db.relationship('Product', backref='products',
                                          secondary=order_product_relation)

    def __init__(self, total_amount, member_id, date):
        self.total_amount = total_amount
        self.member_id = member_id
        self.date = date

# Set many to many relation.

product_material_relation = db.Table(
    'product_material',
    db.Column('product_id', db.Integer, db.ForeignKey('product.product_id')),
    db.Column('material_id', db.Integer, db.ForeignKey('material.material_id'))
    )

class Product(db.Model):
    __tablename__ = 'product'
    product_id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    on_hand_balance = db.Column(db.Integer, nullable=False)
    leading_time = db.Column(db.Integer, nullable=False)
    reorder_point = db.Column(db.Float, nullable=False)

    product_material_relation = db.relationship('Material', backref='materials',
                                             secondary=product_material_relation)

    def __init__(self, product_name, price, on_hand_balance, leading_time,
                 reorder_point):
        self.product_name = product_name
        self.price = price
        self.on_hand_balance = on_hand_balance
        self.leading_time = leading_time
        self.reorder_point = reorder_point

material_material_relation = db.Table(
    'material_material',
    db.Column('material_id', db.Integer, db.ForeignKey('material.material_id')),
    db.Column('raw_material_id', db.Integer, db.ForeignKey('material.material_id'))
    )

class Material(db.Model):
    __tablename__ = 'material'
    material_id = db.Column(db.Integer, primary_key=True)
    material_name = db.Column(db.String(50), nullable=False)
    on_hand_balance = db.Column(db.Integer, nullable=False)
    leading_time = db.Column(db.Integer, nullable=False)
    reorder_point = db.Column(db.Float, nullable=False)

    material_material_relation = db.relationship('Material',
                                         secondary=material_material_relation,
                                         primaryjoin=material_id == material_material_relation.c.material_id,
                                         secondaryjoin=material_id == material_material_relation.c.raw_material_id
                                         )


    def __init__(self, material_id, material_name):
        self.material_id = material_id
        self.material_name = material_name

class Season_Sale(db.Model):
    __tablename__ = "season_sale"
    year = db.Column(db.Integer, primary_key=True)
    season = db.Column(db.Integer, primary_key=True)
    sale = db.Column(db.Integer, nullable=False)

    def __init__(self, year, season, sale):
        self.year = year
        self.season = season
        self.sale = sale

# Member Schema
class MemberSchema(ma.Schema):
    class Meta:
        fields = ('id', 'member_name', 'sex', 'age', 'monetary')

# Order Schema
class OrderSchema(ma.Schema):
    class Meta:
        fields = ("order_id", "total_amount", "date", "member_id")

# Product schema
class ProductSchema(ma.Schema, json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)
    class Meta:
        fields = ('product_id', 'product_name', 'price', 'on_hand_balance',
                  'leading_time', 'reorder_point', 'product_material_relation')

# Material schema
class MaterialSchema(ma.Schema, json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)
    class Meta:
        fields = ('material_id', 'material_name', 'on_hand_balance', 'leading_time',
                  'reorder_point', 'material_material_relation')

# Material and their raw material schema.
# Season_Sale Schema
class SeasonSaleSchema(ma.Schema):
    class Meta:
        fields = ("year", "season", "sale")

# Init schema
member_schema = MemberSchema()
members_schema = MemberSchema(many=True)
order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)
material_schema = MaterialSchema()
materials_schema = MaterialSchema(many=True)
season_sale_schema = SeasonSaleSchema()
season_sales_schema = SeasonSaleSchema(many=True)

db.create_all()

@app.route('/')
def home():
    # READ ALL RECORDS
    all_members = db.session.query(Member).all()
    print(all_members)
    return render_template("index.html", members=all_members)

##### MEMBER FUCTIONS #####
# Add a member
@app.route("/member", methods=['POST'])
def add_member():
    request_data = request.get_json()
    print(request_data)
    member_name = request_data['member_name']
    sex = request_data['sex']
    age = int(request_data['age'])

    new_member = Member(member_name, sex, age)
    db.session.add(new_member)
    db.session.commit()

    return member_schema.jsonify(new_member)


# Get all members
@app.route('/member', methods=['GET'])
def get_members():
    # Check if there is any member in database, if no member, response a 404 page
    if Member.query.first_or_404():
        all_members = Member.query.all()
        result = members_schema.dump(all_members)
        return jsonify(result)

# Get all members by pagination
@app.route('/member/page/<int:request_page>', methods=['GET'])
def get_members_paginate(request_page):
    # Check if there is any member in database, if no member, response a 404 page
    if Member.query.first_or_404():
        # request_page表示要求第幾頁，10代表一頁幾筆資料，False代表出錯時要不要回傳error
        pages = Member.query.paginate(request_page, 10, False)
        # 如果要求的頁數多於所有的頁數，回傳404頁面
        if pages.page > pages.pages:
            abort(404)
        result = members_schema.dump(pages.items)
        return jsonify(result)


# Get a single member by id
@app.route('/member/<int:id>', methods=['GET'])
def get_member(id):
    # Check if there is any member with this id in database, if no, response a 404 page
    if Member.query.filter_by(id=id).first_or_404():
        member = Member.query.get(id)
        return member_schema.jsonify(member)


# Delete a member by member's id
@app.route('/member/<id>', methods=['DELETE'])
def delete_member(id):
    # Check if there is any member with this in database, if no member, response a 404 page
    if Member.query.filter_by(id=id).first_or_404():
        member_to_delete = Member.query.get(id)
        orders_to_delete = Order.query.filter_by(member_id=id).all()
        db.session.delete(member_to_delete)
        # Delete all deleted member's orders
        for order in orders_to_delete:
            db.session.delete(order)
        db.session.commit()
        return member_schema.jsonify(member_to_delete)

##### ORDER FUNCTIONS #####
# 當訂單增加或刪除時，依據member_id更新會員的monetary
def update_member_monetary(member_id, amount):
    member_to_update = Member.query.get(member_id)
    member_to_update.monetary += amount
    print(member_to_update.monetary)

    return member_to_update

# Add an order
@app.route("/order", methods=['POST'])
def add_order():
    request_data = request.get_json()
    member_id = int(request_data['member_id'])
    # Check if there is any member with this order's member_id in database
    if Member.query.filter_by(id=member_id).first_or_404():
        total_amount = request_data['total_amount']
        date = request_data['date']
        date = datetime.strptime(date, '%Y-%m-%d')

        new_order = Order(total_amount, member_id, date)
        db.session.add(new_order)

        ### Update product and orderProduct simultaneously. ###
        # update product's on hand balance.
        product_id = request_data['product_id']
        updated_product = Product.query.filter_by(product_id=product_id).first()
        updated_product.on_hand_balance -= request_data['quantity']

        # update orderProduct.
        new_order.order_product_relation.append(updated_product)

        db.session.add(updated_product)
        db.session.add(new_order)
        db.session.flush()

        # When add an order, update member's monetary
        db.session.add(update_member_monetary(member_id, total_amount))
        db.session.add(update_season_sale())

        db.session.commit()
        return order_schema.jsonify(new_order)

# Get all orders
@app.route('/order', methods=['GET'])
def get_orders():
    # Check if there is any order in database, if no order, response a 404 page
    if Order.query.first_or_404():
        all_orders = Order.query.all()
        result = orders_schema.dump(all_orders)
        return jsonify(result)

# Get all single member's orders
@app.route('/order/mid=<int:member_id>', methods=['GET'])
def get_a_member_orders(member_id):
    # Check if there is any order in database, if no order, response a 404 page
    if Order.query.filter_by(member_id=member_id).first_or_404():
        all_member_orders = Order.query.filter_by(member_id=member_id).all()
        result = orders_schema.dump(all_member_orders)
        return jsonify(result)

# Get members by pagination
@app.route('/order/page/<int:request_page>', methods=['GET'])
def get_orders_paginate(request_page):
    # Check if there is any order in database, if no order, response a 404 page
    if Order.query.first_or_404():
        pages = Order.query.paginate(request_page, 10, False)
        # 如果要求的頁數多於所有的頁數，回傳404
        if pages.page > pages.pages:
            abort(404)
        result = orders_schema.dump(pages.items)
        return jsonify(result)

# Get a single order by order's id
@app.route('/order/<id>', methods=['GET'])
def get_order(id):
    # Check if there is any order with this id in database, if no, response a 404 page
    if Order.query.filter_by(order_id=id).first_or_404():
        order = Order.query.get(id)
        return order_schema.jsonify(order)

# Delete a order by id
@app.route('/order/<id>', methods=['DELETE'])
def delete_order(id):
    # Check if there is any order with this id in database, if no, response a 404 page
    if Order.query.filter_by(order_id=id).first_or_404():
        # DELETE A RECORD BY ID
        order_to_delete = Order.query.get(id)
        amount = -(order_to_delete.total_amount)

        order_to_delete.order_product_relation = []

        db.session.delete(order_to_delete)
        # When delete an order, update member's monetary
        update_member_monetary(order_to_delete.member_id, amount)
        update_season_sale()
        db.session.commit()
        return order_schema.jsonify(order_to_delete)

##### PRODUCT FUNCTIONS #####
# Get all products.
@app.route('/products')
def get_products():
    if Product.query.first_or_404():
        all_products = Product.query.all()
        print(all_products)
        result = products_schema.dump(all_products)
        print(result)
        return jsonify(result)

# Get products paginate.
@app.route('/products/page/<int:request_page>')
def get_products_paginate(request_page):
    if Product.query.first_or_404():
        pages = Product.query.paginate(request_page, 10, False)
        # 如果要求的頁數多於所有的頁數，回傳404
        if pages.page > pages.pages:
            abort(404)
        result = products_schema.dump(pages.items)
        return jsonify(result)

# Get certain product by product_id.
@app.route('/product/<int:product_id>/edit', methods=['GET'])
def get_product(product_id):
    if Product.query.first_or_404():
        product = Product.query.get(product_id)
        return product_schema.jsonify(product)

##### REORDER POINT FUNCTIONS #####
# Get all material and product list.
@app.route('/inventory', methods=['GET'])
def get_inventory():
    if Product.query.first_or_404():
        if Material.query.first_or_404():
            all_products = Product.query.all()
            all_materials = Material.query.all()
            products = products_schema.dump(all_products)
            materials = materials_schema.dump(all_materials)
            return jsonify(products=products, materials=materials)

# Update all material and product.
@app.route('/inventory', methods=['PUT'])
def update_inventory():
    request_data = request.get_json()
    updated_products = []
    for product_request in request_data['products']:
        product_id = product_request['product_id']
        if Product.query.first_or_404():
            product = Product.query.get(product_id)
            product.leading_time = product_request['leading_time']
            product.reorder_point = product_request['reorder_point']
            updated_products.append(product)
    products = products_schema.dump(updated_products)

    updated_materials = []
    for material_request in request_data['materials']:
        material_id = material_request['material_id']
        if Product.query.first_or_404():
            material = Material.query.get(material_id)
            material.leading_time = material_request['leading_time']
            material.reorder_point = material_request['reorder_point']
            updated_materials.append(material)
    materials = materials_schema.dump(updated_materials)

    db.session.commit()
    return jsonify(products=products, materials=materials)

# Order predict using seasonal additive method.
@app.route('/order/predict', methods=['GET'])
def seasonal_predict():
    if Order.query.first_or_404():
        orders = Order.query.all()

        today = datetime.today()
        orders_quaters = {1:[], 2:[], 3:[], 4:[]}
        if today > datetime(year=today.year, month=10, day=1):
            for order in orders:
                if order.date > datetime(year=today.year, month=1, day=1):
                    if order.date < datetime(year=today.year, month=4, day=1):
                        orders_quaters[1].append(order)
                    elif order.date < datetime(year=today.year, month=7, day=1):
                        orders_quaters[2].append(order)
                    elif order.date < datetime(year=today.year, month=10, day=1):
                        orders_quaters[3].append(order)
                    else:
                        orders_quaters[4].append(order)
        elif today > datetime(year=today.year, month=7, day=1):
            for order in orders:
                if order.date > datetime(year=today.year, month=1, day=1):
                    if order.date < datetime(year=today.year, month=4, day=1):
                        orders_quaters[1].append(order)
                    elif order.date < datetime(year=today.year, month=7, day=1):
                        orders_quaters[2].append(order)
                    else:
                        orders_quaters[3].append(order)
                else:
                    if order.date > datetime(year=today.year-1, month=10, day=1):
                        orders_quaters[4].append(order)
        elif today > datetime(year=today.year, month=4, day=1):
            for order in orders:
                if order.date > datetime(year=today.year, month=1, day=1):
                    if order.date < datetime(year=today.year, month=4, day=1):
                        orders_quaters[1].append(order)
                    else:
                        orders_quaters[2].append(order)
                else:
                    if order.date > datetime(year=today.year-1, month=10, day=1):
                        orders_quaters[4].append(order)
                    elif order.date > datetime(year=today.year-1, month=7, day=1):
                        orders_quaters[3].append(order)
        elif today > datetime(year=today.year, month=1, day=1):
            for order in orders:
                if order.date > datetime(year=today.year, month=1, day=1):
                    if order.date < datetime(year=today.year, month=4, day=1):
                        orders_quaters[1].append(order)
                else:
                    if order.date > datetime(year=today.year-1, month=10, day=1):
                        orders_quaters[4].append(order)
                    elif order.date > datetime(year=today.year-1, month=7, day=1):
                        orders_quaters[3].append(order)
                    elif order.date > datetime(year=today.year-1, month=4, day=1):
                        orders_quaters[2].append(order)

        quaters_amount = {}
        predict_amount = {}
        for i in (1, 2, 3, 4):
            quaters_amount[i] = sum([order.total_amount for order in orders_quaters[i]])
            predict_amount[i] = quaters_amount[i] * 1.1
            # 寫死，就直接隔年是今年的 1.1 倍，因為沒有季以外的其他參數。

    return jsonify(available_data=quaters_amount, predict_data=predict_amount)

##### MRP FUNCTIONS #####
@app.route('/mrp', methods=['GET'])
def getMRP():
    materials = Material.query.all()
    products = Product.query.all()

    material_result = materials_schema.dump(materials)
    product_result = products_schema.dump(products)

    return jsonify(products=product_result, materials=material_result)

##### MARKETING METRTICS - SEASON_SALE FUNCTIONS #####
# Add a season_sale
@app.route("/ssale", methods=['POST'])
def add_season_sale():
    request_data = request.get_json()
    print(request_data)
    year = int(request_data['year'])
    season = int(request_data['season'])
    sale = int(request_data['sale'])

    new_season_sale = Season_Sale(year, season, sale)
    db.session.add(new_season_sale)
    db.session.commit()

    return season_sale_schema.jsonify(new_season_sale)


# Get all season_sales
@app.route('/ssale', methods=['GET'])
def get_season_sales():
    # Check if there is any season_sale in database, if no, response a 404 page
    if Season_Sale.query.first_or_404():
        all_season_sales = Season_Sale.query.all()
        result = season_sales_schema.dump(all_season_sales)
        return jsonify(result)


# Get a single season_sale by year and season
@app.route('/ssale/<int:year>/<int:season>', methods=['GET'])
def get_season_sale(year, season):
    # Check if there is any season_sale in this year and season in database, if no, response a 404 page
    if Season_Sale.query.filter_by(year=year, season=season).first_or_404():
        # If two input parameters or above, using tuple
        season_sale = Season_Sale.query.get((year, season))
        return season_sale_schema.jsonify(season_sale)


# Get all season_sales in single year by year
@app.route('/ssale/year/<int:year>', methods=['GET'])
def get_season_sales_by_year(year):
    # Check if there is any season_sale in this year in database, if no, response a 404 page
    if Season_Sale.query.filter_by(year=year).first_or_404():
        season_sales_by_year = Season_Sale.query.filter_by(year=year).all()
        result = season_sales_schema.dump(season_sales_by_year)
        return jsonify(result)


# Get all season_sales in single season by season
@app.route('/ssale/season/<int:season>', methods=['GET'])
def get_season_sales_by_season(season):
    # Check if there is any season_sale in this season in database, if no, response a 404 page
    if Season_Sale.query.filter_by(season=season).first_or_404():
        season_sales_by_season = Season_Sale.query.filter_by(
            season=season).all()
        result = season_sales_schema.dump(season_sales_by_season)
        return jsonify(result)


# Get all quarter on quarter data
@app.route('/ssale/qoq', methods=['GET'])
def cal_qoq():
    sale_data = []
    if Season_Sale.query.first_or_404():
        all_season_sales = Season_Sale.query.all()
        for season_sale in all_season_sales:
            sale_data.append(season_sale.sale) 
        qoq_list = []
        for index in range(4, 12):
            qoq = round((sale_data[index]/sale_data[index-4]-1), 4) 
            qoq_list.append(qoq)
        print(qoq_list)
        result = []
        index = 0
        for year in range(2020, 2022):
            for season in range(1, 5):
                qoq = {
                    "year": year,
                    "season": season,
                    "quarter_on_quarter": qoq_list[index]
                }
                result.append(qoq)
                index += 1
        return jsonify(result) 


# Update a season_sale 
def update_season_sale():
    print("update season sale")
    result =[]
    for year in range(2019, 2022):
        for season in range(1, 5):
            a_season_data ={
                "year": year,
                "season": season,
                "sale": 0
            }
            result.append(a_season_data)
    print(result)
    if Order.query.first_or_404():
        all_orders = Order.query.all()
        for order in all_orders:
            if order.date.year == 2019:
                if 1 <= order.date.month <= 3:
                    result[0]['sale'] += order.total_amount
                elif 4 <= order.date.month <= 6:
                    result[1]['sale'] += order.total_amount
                elif 7 <= order.date.month <= 9:
                    result[2]['sale'] += order.total_amount
                elif 10 <= order.date.month <= 12:
                    result[3]['sale'] += order.total_amount
            elif order.date.year == 2020:
                if 1 <= order.date.month <= 3:
                    result[4]['sale'] += order.total_amount
                elif 4 <= order.date.month <= 6:
                    result[5]['sale'] += order.total_amount
                elif 7 <= order.date.month <= 9:
                    result[6]['sale'] += order.total_amount
                elif 10 <= order.date.month <= 12:
                    result[7]['sale'] += order.total_amount
            elif order.date.year == 2021:
                if 1 <= order.date.month <= 3:
                    result[8]['sale'] += order.total_amount
                elif 4 <= order.date.month <= 6:
                    result[9]['sale'] += order.total_amount
                elif 7 <= order.date.month <= 9:
                    result[10]['sale'] += order.total_amount
                elif 10 <= order.date.month <= 12:
                    result[11]['sale'] += order.total_amount
        print(result)
        index = 0
        for year in range(2019, 2022):
            for season in range(1, 5):
                ssale_to_update = Season_Sale.query.filter(Season_Sale.year == year, Season_Sale.season == season).first()
                ssale_to_update.sale = result[index]['sale']
                index += 1 
                


##### 顧客活動指標 #####
# 回購率
@app.route('/repurchase-rate', methods=['GET'])
def cal_repurchase_rate():
    one_year_ago = datetime.today() - timedelta(days = 365)
    two_year_ago = datetime.today() - timedelta(days = 730)
    if Order.query.filter(Order.date >= two_year_ago, Order.date <= one_year_ago).first_or_404():
        last_year_orders = Order.query.filter(Order.date >= two_year_ago, Order.date <= one_year_ago).group_by(Order.member_id).all()
        result = orders_schema.dump(last_year_orders)
        member_id_list =[]
        for order in last_year_orders:
            member_id_list.append(order.member_id)
        count = 0
        for member_id in member_id_list:
            if Order.query.filter(Order.date >= one_year_ago, Order.member_id == member_id).first():
                count += 1
        repurchase_rate = count /len(member_id_list)
        result = {"repurchase_rate": repurchase_rate}
        return jsonify(result)

# 活躍率
@app.route('/active-rate', methods=['GET'])
def cal_active_rate():
    one_year_ago = datetime.today() - timedelta(days = 365)
    result = []
    member_id_list = []
    members = Member.query.all()
    for member in members:
        member_id_list.append(member.id)
    for member_id in member_id_list:
        name = Member.query.get(member_id).member_name
        if Order.query.filter(Order.date >= one_year_ago, Order.member_id==member_id).first():
            count = Order.query.filter(Order.date >= one_year_ago, Order.member_id==member_id).count()
            order = Order.query.filter(Order.date >= one_year_ago, Order.member_id==member_id).order_by(desc(Order.date)).first()
            months_ago_purchase = round(((datetime.today() - order.date).days)/30, 2)
            active_rate = round(pow((12-months_ago_purchase)/12, count), 4)
        else:
            count = 0
            months_ago_purchase = 0
            active_rate = 0

        result_list ={
            "member_id": member_id,
            "name": name,
            "purchase_time": count,
            "months_ago_purchase": months_ago_purchase,
            "active_rate": active_rate
        }
        result.append(result_list)
    return jsonify(result)

# RFM
@app.route('/rfm', methods=['GET'])
def cal_rfm():
    if Order.query.first_or_404():
        #M
        counts = Order.query.group_by(Order.member_id).count()
        selected_member_id = []
        members = Member.query.order_by(desc(Member.monetary)).limit((counts+1)/2).all()
        for member in members:
            selected_member_id.append(member.id)
        print(selected_member_id)
        
        #F
        freq_dict = {}
        for member_id in selected_member_id:
            count = Order.query.filter(Order.member_id==member_id).count()
            freq_dict[member_id] = count
        freq_list = sorted(freq_dict.items(), reverse=True, key=lambda x:x[1])
        member_id_list = freq_list[:int((len(selected_member_id)+1)/2)]
        selected_member_id = []
        for i in range(len(member_id_list)):
            selected_member_id.append(member_id_list[i][0])
        print(selected_member_id)
        
        #R(負的)
        rect_dict = {}
        for member_id in selected_member_id:
            order = Order.query.filter(Order.member_id==member_id).order_by(desc(Order.date)).first()
            rect_dict[member_id] = order.date
        rect_list = sorted(rect_dict.items(), key=lambda x:x[1])
        member_id_list = rect_list[:int((len(selected_member_id)+1)/2)]
        result_id_list = [member[0] for member in member_id_list]
        members = Member.query.filter(Member.id.in_(result_id_list)).all()
        result = members_schema.dump(members)
        return jsonify(result)



if __name__ == "__main__":
    app.run(debug=True)
    

# "POST" test data
member_test_data = {
    "member_name": "luke",
    "sex": "M",
    "age": 88
}

order_test_data = {
    "member_id": 1,
    "total_amount": 888,
    "date": "2021-12-25",
    "product_id": 1,
    "quantity": 10
}


season_sale_test_data = {
    "year": 2019,
    "season": 1,
    "sale": 147
}